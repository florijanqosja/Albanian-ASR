import os
import shutil
import tempfile
import unittest

from fastapi import HTTPException
from pydub import AudioSegment

from api.main import _prepare_trim_window, _trim_audio_segment


class PrepareTrimWindowTests(unittest.TestCase):
    def test_returns_none_when_both_missing(self):
        self.assertIsNone(_prepare_trim_window(None, None))

    def test_requires_both_values(self):
        with self.assertRaises(HTTPException):
            _prepare_trim_window(0.1, None)
        with self.assertRaises(HTTPException):
            _prepare_trim_window(None, 0.5)

    def test_rejects_negative_values(self):
        with self.assertRaises(HTTPException):
            _prepare_trim_window(-0.1, 0.5)

    def test_orders_window(self):
        start, end = _prepare_trim_window(2.0, 0.25)
        self.assertEqual((start, end), (0.25, 2.0))

    def test_returns_none_when_identical(self):
        self.assertIsNone(_prepare_trim_window(0.5, 0.5))


class TrimAudioSegmentTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="trim_tests_")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_wav(self, duration_ms=2000, filename="clip.wav"):
        path = os.path.join(self.temp_dir, filename)
        AudioSegment.silent(duration=duration_ms).export(path, format="wav")
        return path

    def test_trims_audio_and_returns_new_duration(self):
        clip = self._create_wav()
        new_duration = _trim_audio_segment(clip, 0.2, 1.0)
        self.assertAlmostEqual(new_duration, 0.8, places=2)
        updated = AudioSegment.from_file(clip)
        self.assertAlmostEqual(len(updated) / 1000, 0.8, places=2)

    def test_trimming_skipped_when_window_empty(self):
        clip = self._create_wav()
        original = AudioSegment.from_file(clip)
        result = _trim_audio_segment(clip, 0.5, 0.5)
        self.assertIsNone(result)
        updated = AudioSegment.from_file(clip)
        self.assertAlmostEqual(len(original), len(updated), places=0)

    def test_trimming_clamps_to_audio_length(self):
        clip = self._create_wav()
        new_duration = _trim_audio_segment(clip, 1.5, 5.0)
        self.assertAlmostEqual(new_duration, 0.5, places=2)
        updated = AudioSegment.from_file(clip)
        self.assertAlmostEqual(len(updated) / 1000, 0.5, places=2)


if __name__ == "__main__":
    unittest.main()
