import os
import shutil
import subprocess
import tempfile
import unittest
import wave

import numpy as np

from api.services.segmentation import (
    MAX_FILENAME_BYTES,
    SAMPLE_RATE,
    VAD_WINDOW,
    SegmentationConfig,
    SegmentationError,
    build_splice_filename,
    build_utterances,
    decode_audio,
    energy_speech_probs,
    probs_to_speech_regions,
    segment_audio_file,
    write_wav,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAMPLE_MP3 = os.path.join(REPO_ROOT, "sample_audio_njerez_dhe_fate_e2.mp3")


def _has_ffmpeg():
    return shutil.which("ffmpeg") is not None


def _has_onnxruntime():
    try:
        import onnxruntime  # noqa: F401
        return True
    except ImportError:
        return False


def _windows(seconds):
    """Number of VAD windows covering `seconds` of audio."""
    return int(seconds * SAMPLE_RATE / VAD_WINDOW)


def _region_probs(*spans, total_s):
    """Build a synthetic prob array: high inside the given (start_s, end_s) spans."""
    probs = np.full(_windows(total_s), 0.05, dtype=np.float32)
    for start_s, end_s in spans:
        probs[_windows(start_s):_windows(end_s)] = 0.95
    return probs


class ProbsToSpeechRegionsTests(unittest.TestCase):
    def setUp(self):
        self.config = SegmentationConfig(speech_pad_ms=0)

    def test_detects_single_speech_region(self):
        probs = _region_probs((2.0, 6.0), total_s=10.0)
        total = _windows(10.0) * VAD_WINDOW
        regions = probs_to_speech_regions(probs, total, self.config)
        self.assertEqual(len(regions), 1)
        self.assertAlmostEqual(regions[0]["start"] / SAMPLE_RATE, 2.0, delta=0.1)
        self.assertAlmostEqual(regions[0]["end"] / SAMPLE_RATE, 6.0, delta=0.1)

    def test_drops_bursts_shorter_than_min_speech(self):
        probs = _region_probs((2.0, 2.1), total_s=10.0)  # 100ms < 250ms min
        total = _windows(10.0) * VAD_WINDOW
        regions = probs_to_speech_regions(probs, total, self.config)
        self.assertEqual(regions, [])

    def test_short_silence_does_not_split_region(self):
        # 100ms dip < 300ms min_silence: must stay one region
        probs = _region_probs((2.0, 4.0), (4.1, 6.0), total_s=10.0)
        total = _windows(10.0) * VAD_WINDOW
        regions = probs_to_speech_regions(probs, total, self.config)
        self.assertEqual(len(regions), 1)

    def test_long_silence_splits_regions(self):
        probs = _region_probs((2.0, 4.0), (5.0, 7.0), total_s=10.0)
        total = _windows(10.0) * VAD_WINDOW
        regions = probs_to_speech_regions(probs, total, self.config)
        self.assertEqual(len(regions), 2)

    def test_padding_does_not_overlap_neighbours(self):
        config = SegmentationConfig(speech_pad_ms=400)
        probs = _region_probs((2.0, 4.0), (4.5, 6.0), total_s=10.0)
        total = _windows(10.0) * VAD_WINDOW
        regions = probs_to_speech_regions(probs, total, config)
        self.assertEqual(len(regions), 2)
        self.assertLessEqual(regions[0]["end"], regions[1]["start"])
        self.assertGreaterEqual(regions[0]["start"], 0)
        self.assertLessEqual(regions[-1]["end"], total)


class BuildUtterancesTests(unittest.TestCase):
    def setUp(self):
        self.config = SegmentationConfig(
            min_utterance_s=1.0, max_utterance_s=15.0, max_merge_gap_s=1.0
        )

    def _samples(self, seconds):
        return int(seconds * SAMPLE_RATE)

    def test_merges_regions_across_small_gaps(self):
        regions = [
            {"start": self._samples(0), "end": self._samples(3)},
            {"start": self._samples(3.5), "end": self._samples(6)},
        ]
        probs = np.ones(_windows(10.0), dtype=np.float32)
        utterances = build_utterances(regions, probs, self.config)
        self.assertEqual(len(utterances), 1)
        self.assertEqual(utterances[0]["end"] - utterances[0]["start"], self._samples(6))

    def test_does_not_merge_across_large_gaps(self):
        regions = [
            {"start": self._samples(0), "end": self._samples(3)},
            {"start": self._samples(6), "end": self._samples(9)},
        ]
        probs = np.ones(_windows(10.0), dtype=np.float32)
        utterances = build_utterances(regions, probs, self.config)
        self.assertEqual(len(utterances), 2)

    def test_does_not_merge_beyond_max_duration(self):
        regions = [
            {"start": self._samples(0), "end": self._samples(9)},
            {"start": self._samples(9.5), "end": self._samples(18)},
        ]
        probs = np.ones(_windows(20.0), dtype=np.float32)
        utterances = build_utterances(regions, probs, self.config)
        self.assertEqual(len(utterances), 2)

    def test_splits_overlong_region_at_low_prob_valley(self):
        # 25s continuous region with an artificial low-prob valley at ~10s
        regions = [{"start": 0, "end": self._samples(25)}]
        probs = np.full(_windows(25.0), 0.9, dtype=np.float32)
        valley = _windows(10.0)
        probs[valley] = 0.1
        utterances = build_utterances(regions, probs, self.config)
        self.assertGreaterEqual(len(utterances), 2)
        max_samples = int(self.config.max_utterance_s * SAMPLE_RATE)
        for utterance in utterances:
            self.assertLessEqual(utterance["end"] - utterance["start"], max_samples)
        # The first cut should land on the valley, not at the 15s hard cap.
        self.assertEqual(utterances[0]["end"], valley * VAD_WINDOW)
        # No audio lost: pieces are contiguous
        for prev, cur in zip(utterances, utterances[1:]):
            self.assertEqual(prev["end"], cur["start"])

    def test_drops_utterances_below_min_duration(self):
        regions = [{"start": 0, "end": self._samples(0.5)}]
        probs = np.ones(_windows(1.0), dtype=np.float32)
        self.assertEqual(build_utterances(regions, probs, self.config), [])


class WavExportTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="segment_tests_")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_writes_16k_mono_16bit_pcm(self):
        samples = np.sin(np.linspace(0, 440 * 2 * np.pi, SAMPLE_RATE * 2)).astype(np.float32)
        path = os.path.join(self.temp_dir, "tone.wav")
        write_wav(path, samples)
        with wave.open(path, "rb") as wav_file:
            self.assertEqual(wav_file.getnchannels(), 1)
            self.assertEqual(wav_file.getsampwidth(), 2)
            self.assertEqual(wav_file.getframerate(), SAMPLE_RATE)
            self.assertEqual(wav_file.getnframes(), len(samples))

    def test_build_splice_filename_leaves_short_names_intact(self):
        self.assertEqual(
            build_splice_filename("Test_Video", 0, 1000),
            "Test_Video_00000000-00001000.wav",
        )

    def test_build_splice_filename_truncates_over_long_names(self):
        # A name that would overflow the 255-byte component limit is trimmed, but
        # the "_{start}-{end}.wav" suffix is preserved so it stays unique.
        filename = build_splice_filename("x" * 400, 234, 14806)
        self.assertLessEqual(len(filename.encode("utf-8")), MAX_FILENAME_BYTES)
        self.assertTrue(filename.endswith("_00000234-00014806.wav"))


@unittest.skipUnless(_has_ffmpeg(), "ffmpeg not available")
class SegmentAudioFileTests(unittest.TestCase):
    """End-to-end segmentation using the deterministic energy backend."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="segment_e2e_")
        self.output_dir = os.path.join(self.temp_dir, "out")
        self.config = SegmentationConfig(
            backend="energy",
            min_utterance_s=1.0,
            max_utterance_s=15.0,
            max_merge_gap_s=1.0,
            speech_pad_ms=100,
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_input(self, samples, name="input.wav"):
        """Write float32 audio samples to a temporary WAV input file.
        
        Parameters:
        	samples: Audio samples to write.
        	name (str): Output filename within the temporary directory.
        
        Returns:
        	str: Path to the written WAV file.
        """
        path = os.path.join(self.temp_dir, name)
        write_wav(path, samples.astype(np.float32))
        return path

    def _noise_burst(self, seconds, amplitude=0.3, seed=0):
        """Generate a deterministic Gaussian noise waveform for the specified duration.
        
        Parameters:
            seconds (float): Duration of the waveform in seconds.
            amplitude (float): Scale applied to the generated noise.
            seed (int): Seed for the random number generator.
        
        Returns:
            numpy.ndarray: Float waveform containing Gaussian noise samples.
        """
        rng = np.random.default_rng(seed)
        return amplitude * rng.standard_normal(int(seconds * SAMPLE_RATE))

    def _silence(self, seconds):
        return np.zeros(int(seconds * SAMPLE_RATE), dtype=np.float32)

    def test_segments_noise_bursts_into_utterances(self):
        audio = np.concatenate([
            self._silence(2), self._noise_burst(3, seed=1),
            self._silence(2), self._noise_burst(4, seed=2),
            self._silence(2), self._noise_burst(3, seed=3),
            self._silence(2),
        ])
        input_path = self._write_input(audio)
        segments = segment_audio_file(input_path, self.output_dir, "Test_Video", self.config)

        self.assertEqual(len(segments), 3)
        for segment in segments:
            self.assertTrue(os.path.exists(segment.path))
            self.assertTrue(segment.filename.startswith("Test_Video_"))
            self.assertTrue(segment.filename.endswith(".wav"))
            self.assertGreaterEqual(segment.duration_s, self.config.min_utterance_s)
            self.assertLessEqual(segment.duration_s, self.config.max_utterance_s)
            with wave.open(segment.path, "rb") as wav_file:
                self.assertEqual(wav_file.getnchannels(), 1)
                self.assertEqual(wav_file.getframerate(), SAMPLE_RATE)
                file_duration = wav_file.getnframes() / SAMPLE_RATE
            self.assertAlmostEqual(file_duration, segment.duration_s, places=2)
        # Chronological, non-overlapping
        for prev, cur in zip(segments, segments[1:]):
            self.assertLessEqual(prev.end_s, cur.start_s)
        # Only the exported wavs live in the output dir (it feeds the DB queue)
        self.assertEqual(
            sorted(os.listdir(self.output_dir)), sorted(s.filename for s in segments)
        )

    def test_over_long_name_is_truncated_to_fit_filesystem(self):
        # A pathologically long title (e.g. a full audiobook chapter name) must not
        # blow past the 255-byte filename limit and crash with [Errno 36].
        long_name = "Perralla_e_car_salltanit_" * 12  # ~300 chars, > 255 bytes
        audio = np.concatenate([
            self._silence(2), self._noise_burst(3, seed=1), self._silence(2),
        ])
        input_path = self._write_input(audio)
        segments = segment_audio_file(input_path, self.output_dir, long_name, self.config)

        self.assertTrue(segments)
        for segment in segments:
            self.assertTrue(os.path.exists(segment.path))
            self.assertLessEqual(len(segment.filename.encode("utf-8")), MAX_FILENAME_BYTES)
            self.assertTrue(segment.filename.endswith(".wav"))
        # On-disk names still match the returned Segment metadata (feeds the DB queue).
        self.assertEqual(
            sorted(os.listdir(self.output_dir)), sorted(s.filename for s in segments)
        )

    def test_pure_silence_produces_no_segments(self):
        input_path = self._write_input(self._silence(20))
        segments = segment_audio_file(input_path, self.output_dir, "Silent", self.config)
        self.assertEqual(segments, [])
        self.assertEqual(os.listdir(self.output_dir), [])

    def test_clipped_audio_is_rejected(self):
        clipped = np.sign(self._noise_burst(5, seed=4))  # full-scale square wave
        audio = np.concatenate([self._silence(2), clipped, self._silence(2)])
        input_path = self._write_input(audio)
        segments = segment_audio_file(input_path, self.output_dir, "Clipped", self.config)
        self.assertEqual(segments, [])

    def test_missing_input_raises(self):
        with self.assertRaises(SegmentationError):
            segment_audio_file(
                os.path.join(self.temp_dir, "missing.mp3"), self.output_dir, "X", self.config
            )

    def test_energy_probs_ignore_pure_silence(self):
        probs = energy_speech_probs(self._silence(10))
        self.assertLess(float(probs.max(initial=0.0)), 0.5)


@unittest.skipUnless(
    _has_ffmpeg() and _has_onnxruntime() and os.path.exists(SAMPLE_MP3),
    "requires ffmpeg, onnxruntime, and the bundled sample mp3",
)
class SileroIntegrationTests(unittest.TestCase):
    """Silero VAD on real Albanian speech (first 2 minutes of the sample episode).

    The episode opens with ~60s of intro music: a correct segmenter must skip
    it entirely, which the old fixed-threshold splicer could not do.
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="segment_silero_")
        self.output_dir = os.path.join(self.temp_dir, "out")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_segments_real_speech_and_skips_intro_music(self):
        excerpt = os.path.join(self.temp_dir, "excerpt.wav")
        subprocess.run(
            ["ffmpeg", "-v", "error", "-i", SAMPLE_MP3, "-t", "120",
             "-ac", "1", "-ar", str(SAMPLE_RATE), excerpt],
            check=True,
        )
        config = SegmentationConfig(backend="silero")
        segments = segment_audio_file(excerpt, self.output_dir, "Sample", config)

        self.assertGreaterEqual(len(segments), 3)
        # Intro music occupies roughly the first minute; no utterance should
        # start inside it.
        self.assertGreater(segments[0].start_s, 30.0)
        for segment in segments:
            self.assertGreaterEqual(segment.duration_s, config.min_utterance_s)
            self.assertLessEqual(segment.duration_s, config.max_utterance_s)
            self.assertGreaterEqual(segment.avg_speech_prob, config.min_avg_speech_prob)

    def test_decode_audio_reads_mp3(self):
        audio = decode_audio(SAMPLE_MP3)
        self.assertGreater(len(audio) / SAMPLE_RATE, 2000)  # ~39 min episode
        self.assertEqual(audio.dtype, np.float32)


if __name__ == "__main__":
    unittest.main()
