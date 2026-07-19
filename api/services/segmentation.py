"""Utterance segmentation engine for ASR dataset building.

Replaces naive fixed-threshold silence splitting with a proper pipeline:

1. Decode any input (mp3/mp4/wav/...) to 16 kHz mono float32 via ffmpeg.
2. Detect speech with Silero VAD (vendored ONNX model, onnxruntime backend,
   no torch dependency), falling back to adaptive energy-based detection when
   the model is unavailable.
3. Assemble VAD speech regions into utterances sized for labeling and ASR
   training (default 1-15 s), merging short regions across small gaps and
   splitting overlong regions at the least-speech-like frame.
4. Reject segments that are unusable for training (near-silent, heavily
   clipped, or mostly non-speech).
5. Export each utterance as 16 kHz mono 16-bit PCM WAV — the format the
   training pipeline consumes directly.

The public entry point is :func:`segment_audio_file`. It is a synchronous
function intended to be called through ``run_in_threadpool`` from FastAPI.

Model attribution: Silero VAD (https://github.com/snakers4/silero-vad),
MIT licensed. See api/assets/README.md.
"""
from __future__ import annotations

import logging
import math
import os
import subprocess
import threading
import wave
from dataclasses import dataclass
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
# Silero VAD v5 consumes fixed 512-sample windows at 16 kHz (32 ms) and keeps
# a 64-sample context tail from the previous window plus a recurrent state.
VAD_WINDOW = 512
VAD_CONTEXT = 64

DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets",
    "silero_vad.onnx",
)


class SegmentationError(RuntimeError):
    """Raised when an input cannot be decoded or segmented at all."""


def _env_float(name: str, default: float) -> float:
    """
    Read a floating-point setting from an environment variable.
    
    Parameters:
    	name (str): Environment variable name.
    	default (float): Value to use when the variable is unset or invalid.
    
    Returns:
    	float: The parsed environment value, or `default` if parsing fails.
    """
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        logger.warning("Invalid value for %s; using default %s", name, default)
        return default


@dataclass
class SegmentationConfig:
    """Tuning knobs for the segmentation pipeline (see .env.example)."""

    backend: str = "silero"  # "silero" | "energy"
    model_path: str = DEFAULT_MODEL_PATH
    # VAD hysteresis (silero-vad get_speech_timestamps semantics)
    vad_threshold: float = 0.5
    vad_neg_threshold: Optional[float] = None  # defaults to threshold - 0.15
    min_speech_ms: float = 250.0
    min_silence_ms: float = 300.0
    speech_pad_ms: float = 150.0
    # Utterance assembly
    min_utterance_s: float = 1.0
    max_utterance_s: float = 15.0
    max_merge_gap_s: float = 1.0
    # Quality gates
    min_rms_dbfs: float = -55.0
    max_clipping_ratio: float = 0.02
    min_avg_speech_prob: float = 0.30

    @property
    def neg_threshold(self) -> float:
        """Return the speech probability threshold used to end a detected speech region.
        
        Returns:
            float: The configured negative threshold, or a value derived from the speech threshold.
        """
        if self.vad_neg_threshold is not None:
            return self.vad_neg_threshold
        return max(self.vad_threshold - 0.15, 0.01)

    @classmethod
    def from_env(cls) -> "SegmentationConfig":
        """
        Create a segmentation configuration from environment variables, using defaults for unset or invalid numeric values.
        
        Returns:
        	SegmentationConfig: Configuration populated from the supported `SEGMENTER_*` environment variables.
        """
        return cls(
            backend=os.getenv("SEGMENTER_BACKEND", "silero").strip().lower(),
            model_path=os.getenv("SEGMENTER_VAD_MODEL_PATH", DEFAULT_MODEL_PATH),
            vad_threshold=_env_float("SEGMENTER_VAD_THRESHOLD", 0.5),
            min_speech_ms=_env_float("SEGMENTER_MIN_SPEECH_MS", 250.0),
            min_silence_ms=_env_float("SEGMENTER_MIN_SILENCE_MS", 300.0),
            speech_pad_ms=_env_float("SEGMENTER_SPEECH_PAD_MS", 150.0),
            min_utterance_s=_env_float("SEGMENTER_MIN_UTTERANCE_S", 1.0),
            max_utterance_s=_env_float("SEGMENTER_MAX_UTTERANCE_S", 15.0),
            max_merge_gap_s=_env_float("SEGMENTER_MAX_MERGE_GAP_S", 1.0),
            min_rms_dbfs=_env_float("SEGMENTER_MIN_RMS_DBFS", -55.0),
            max_clipping_ratio=_env_float("SEGMENTER_MAX_CLIPPING_RATIO", 0.02),
            min_avg_speech_prob=_env_float("SEGMENTER_MIN_AVG_SPEECH_PROB", 0.30),
        )


@dataclass
class Segment:
    """One exported utterance plus the metadata the caller persists."""

    path: str
    filename: str
    start_s: float
    end_s: float
    duration_s: float
    avg_speech_prob: float
    rms_dbfs: float
    clipping_ratio: float


def decode_audio(input_path: str, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """
    Decode a media file to mono float32 PCM samples.
    
    Parameters:
    	input_path (str): Path to the input media file.
    	sample_rate (int): Target audio sample rate in Hz.
    
    Returns:
    	np.ndarray: Decoded mono audio samples in the range [-1, 1].
    
    Raises:
    	SegmentationError: If the input file is missing, ffmpeg is unavailable or fails, or no audio samples are decoded.
    """
    if not os.path.exists(input_path):
        raise SegmentationError(f"Input file not found: {input_path}")
    cmd = [
        "ffmpeg", "-v", "error", "-nostdin",
        "-i", input_path,
        "-vn", "-ac", "1", "-ar", str(sample_rate),
        "-f", "f32le", "-",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, check=True)
    except FileNotFoundError as exc:
        raise SegmentationError("ffmpeg binary not found on PATH") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace").strip()
        raise SegmentationError(f"ffmpeg failed to decode {input_path}: {stderr}") from exc
    audio = np.frombuffer(proc.stdout, dtype=np.float32)
    if audio.size == 0:
        raise SegmentationError(f"Decoded no audio samples from {input_path}")
    return audio


def write_wav(path: str, samples: np.ndarray, sample_rate: int = SAMPLE_RATE) -> None:
    """Write float32 samples as a mono 16-bit PCM WAV file."""
    pcm = (np.clip(samples, -1.0, 1.0) * 32767.0).astype("<i2")
    with wave.open(path, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm.tobytes())


class SileroOnnxVAD:
    """Minimal numpy/onnxruntime driver for the vendored Silero VAD model."""

    def __init__(self, model_path: str):
        """Initialize the Silero VAD inference session for the specified model.
        
        Parameters:
        	model_path (str): Path to the Silero VAD ONNX model.
        
        Raises:
        	SegmentationError: If the model file does not exist.
        """
        import onnxruntime  # deferred: keep module import light for tests/workers

        if not os.path.exists(model_path):
            raise SegmentationError(f"Silero VAD model not found at {model_path}")
        self.model_path = model_path
        options = onnxruntime.SessionOptions()
        options.inter_op_num_threads = 1
        options.intra_op_num_threads = 1
        self._session = onnxruntime.InferenceSession(
            model_path, sess_options=options, providers=["CPUExecutionProvider"]
        )
        self._lock = threading.Lock()

    def speech_probs(self, audio: np.ndarray) -> np.ndarray:
        """
        Estimate speech probability for each fixed-size audio window.
        
        Parameters:
            audio (np.ndarray): Audio samples to analyze.
        
        Returns:
            np.ndarray: Speech probabilities, one for each 512-sample window. The final
                window is zero-padded when the audio length is not an exact multiple of
                the window size.
        """
        state = np.zeros((2, 1, 128), dtype=np.float32)
        context = np.zeros(VAD_CONTEXT, dtype=np.float32)
        sr = np.array(SAMPLE_RATE, dtype=np.int64)
        n_windows = math.ceil(len(audio) / VAD_WINDOW)
        probs = np.empty(n_windows, dtype=np.float32)
        # The model is stateful across windows, so one audio stream must be
        # processed sequentially and exclusively.
        with self._lock:
            for i in range(n_windows):
                chunk = audio[i * VAD_WINDOW:(i + 1) * VAD_WINDOW]
                if len(chunk) < VAD_WINDOW:
                    chunk = np.pad(chunk, (0, VAD_WINDOW - len(chunk)))
                model_input = np.concatenate([context, chunk]).reshape(1, -1).astype(np.float32)
                out, state = self._session.run(
                    None, {"input": model_input, "state": state, "sr": sr}
                )[:2]
                probs[i] = out[0][0]
                context = chunk[-VAD_CONTEXT:]
        return probs


_vad_instance: Optional[SileroOnnxVAD] = None
_vad_init_lock = threading.Lock()


def _get_vad(model_path: str) -> SileroOnnxVAD:
    """Return the shared Silero VAD instance for the specified model path.
    
    Parameters:
    	model_path (str): Path to the Silero ONNX model.
    
    Returns:
    	SileroOnnxVAD: The initialized VAD instance for the model path.
    """
    global _vad_instance
    with _vad_init_lock:
        if _vad_instance is None or _vad_instance.model_path != model_path:
            _vad_instance = SileroOnnxVAD(model_path)
            logger.info("Loaded Silero VAD model from %s", model_path)
        return _vad_instance


def energy_speech_probs(audio: np.ndarray) -> np.ndarray:
    """
    Estimate speech activity from short-term audio energy using an adaptive threshold.
    
    Parameters:
        audio (np.ndarray): Audio samples from which to estimate speech activity.
    
    Returns:
        np.ndarray: Smoothed activity values for each analysis window, where higher
            values indicate greater speech likelihood.
    """
    n_windows = math.ceil(len(audio) / VAD_WINDOW)
    padded = np.pad(audio, (0, n_windows * VAD_WINDOW - len(audio)))
    frames = padded.reshape(n_windows, VAD_WINDOW)
    rms = np.sqrt(np.mean(frames.astype(np.float64) ** 2, axis=1))
    frame_db = 20.0 * np.log10(rms + 1e-10)
    noise_floor = np.percentile(frame_db, 10)
    loud_level = np.percentile(frame_db, 90)
    threshold_db = max(noise_floor + 6.0, loud_level - 20.0, -55.0)
    active = (frame_db > threshold_db).astype(np.float32)
    # Light smoothing so brief energy dips inside words do not flicker.
    # np.convolve(mode="same") returns max(len, kernel) elements, so the
    # kernel must never exceed the number of windows.
    kernel_size = min(5, n_windows)
    kernel = np.ones(kernel_size, dtype=np.float32) / kernel_size
    return np.convolve(active, kernel, mode="same")


def probs_to_speech_regions(
    probs: np.ndarray,
    total_samples: int,
    config: SegmentationConfig,
) -> List[dict]:
    """
    Convert per-window speech probabilities into padded speech regions.
    
    Parameters:
        probs (np.ndarray): Speech probabilities for consecutive VAD windows.
        total_samples (int): Total number of audio samples used to bound the regions.
        config (SegmentationConfig): Threshold and timing settings for speech detection.
    
    Returns:
        List[dict]: Regions with integer ``start`` and ``end`` sample indices.
    """
    threshold = config.vad_threshold
    neg_threshold = config.neg_threshold
    min_speech = int(config.min_speech_ms * SAMPLE_RATE / 1000)
    min_silence = int(config.min_silence_ms * SAMPLE_RATE / 1000)
    pad = int(config.speech_pad_ms * SAMPLE_RATE / 1000)

    regions: List[dict] = []
    triggered = False
    current_start = 0
    temp_end = 0

    for i, prob in enumerate(probs):
        position = i * VAD_WINDOW
        if prob >= threshold and temp_end:
            temp_end = 0
        if prob >= threshold and not triggered:
            triggered = True
            current_start = position
            continue
        if prob < neg_threshold and triggered:
            if not temp_end:
                temp_end = position
            if position - temp_end < min_silence:
                continue
            if temp_end - current_start > min_speech:
                regions.append({"start": current_start, "end": temp_end})
            triggered = False
            temp_end = 0

    if triggered and total_samples - current_start > min_speech:
        regions.append({"start": current_start, "end": total_samples})

    for i, region in enumerate(regions):
        if i == 0:
            region["start"] = max(0, region["start"] - pad)
        if i < len(regions) - 1:
            gap = regions[i + 1]["start"] - region["end"]
            if gap < 2 * pad:
                region["end"] += gap // 2
                regions[i + 1]["start"] -= gap // 2
            else:
                region["end"] = min(total_samples, region["end"] + pad)
                regions[i + 1]["start"] -= pad
        else:
            region["end"] = min(total_samples, region["end"] + pad)
    return regions


def _split_at_least_speechy(
    start: int,
    end: int,
    probs: np.ndarray,
    max_samples: int,
    min_samples: int,
) -> List[dict]:
    """
    Split an overlong speech region into utterance-sized pieces at low-probability boundaries.
    
    Parameters:
        start (int): Start sample index of the region.
        end (int): End sample index of the region.
        probs (np.ndarray): Speech probabilities for successive VAD windows.
        max_samples (int): Maximum allowed length of each piece in samples.
        min_samples (int): Minimum required length of each piece in samples.
    
    Returns:
        List[dict]: Non-overlapping regions with ``start`` and ``end`` sample indices.
    """
    pieces: List[dict] = []
    cursor = start
    while end - cursor > max_samples:
        # The cut must leave at least min_samples on both sides.
        search_lo = max(cursor + min_samples, cursor + max_samples // 2)
        search_hi = cursor + max_samples
        if end - search_hi < min_samples:
            search_hi = end - min_samples
        lo_w = max(search_lo // VAD_WINDOW, 0)
        hi_w = min(search_hi // VAD_WINDOW, len(probs) - 1)
        if hi_w <= lo_w:
            cut = cursor + max_samples
        else:
            cut = (lo_w + int(np.argmin(probs[lo_w:hi_w + 1]))) * VAD_WINDOW
        pieces.append({"start": cursor, "end": cut})
        cursor = cut
    pieces.append({"start": cursor, "end": end})
    return pieces


def build_utterances(
    regions: List[dict],
    probs: np.ndarray,
    config: SegmentationConfig,
) -> List[dict]:
    """Assemble speech regions into utterances within duration bounds.

    Adjacent regions are merged while the silence gap between them is at most
    `max_merge_gap_s` and the merged span stays within `max_utterance_s`
    (natural pauses are kept inside the utterance). Regions still longer than
    the cap are split at the least-speech-like frame. Utterances shorter than
    `min_utterance_s` are dropped.
    """
    min_utt = int(config.min_utterance_s * SAMPLE_RATE)
    max_utt = int(config.max_utterance_s * SAMPLE_RATE)
    max_gap = int(config.max_merge_gap_s * SAMPLE_RATE)

    merged: List[dict] = []
    current: Optional[dict] = None
    for region in regions:
        if current is None:
            current = dict(region)
            continue
        gap = region["start"] - current["end"]
        if gap <= max_gap and region["end"] - current["start"] <= max_utt:
            current["end"] = region["end"]
        else:
            merged.append(current)
            current = dict(region)
    if current is not None:
        merged.append(current)

    utterances: List[dict] = []
    for span in merged:
        if span["end"] - span["start"] > max_utt:
            utterances.extend(
                _split_at_least_speechy(span["start"], span["end"], probs, max_utt, min_utt)
            )
        else:
            utterances.append(span)

    return [u for u in utterances if u["end"] - u["start"] >= min_utt]


def _segment_metrics(samples: np.ndarray, probs: np.ndarray, start: int, end: int) -> dict:
    """
    Compute quality metrics for an audio segment.
    
    Parameters:
    	samples (np.ndarray): Audio samples in the segment.
    	probs (np.ndarray): Speech probabilities for the audio.
    	start (int): Segment start sample index.
    	end (int): Segment end sample index.
    
    Returns:
    	dict: Metrics containing RMS level in dBFS, clipping ratio, and average speech probability.
    """
    rms = float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))
    rms_dbfs = 20.0 * math.log10(rms + 1e-10)
    clipping_ratio = float(np.mean(np.abs(samples) >= 0.999))
    lo_w = start // VAD_WINDOW
    hi_w = max(lo_w + 1, min(math.ceil(end / VAD_WINDOW), len(probs)))
    avg_speech_prob = float(np.mean(probs[lo_w:hi_w])) if len(probs) else 0.0
    return {
        "rms_dbfs": rms_dbfs,
        "clipping_ratio": clipping_ratio,
        "avg_speech_prob": avg_speech_prob,
    }


def segment_audio_file(
    input_path: str,
    output_dir: str,
    base_name: str,
    config: Optional[SegmentationConfig] = None,
) -> List[Segment]:
    """Segment a media file into utterance WAVs ready for labeling.

    Decodes `input_path`, finds utterances, and writes one 16 kHz mono 16-bit
    PCM WAV per utterance into `output_dir` as
    ``{base_name}_{start_ms:08d}-{end_ms:08d}.wav``.

    Returns the list of exported segments (chronological). May legitimately
    return an empty list when the recording contains no usable speech (e.g.
    music-only uploads) — callers should treat that as "nothing to label",
    not as an error.

    Raises SegmentationError when the input cannot be decoded at all.
    """
    cfg = config or SegmentationConfig.from_env()
    os.makedirs(output_dir, exist_ok=True)

    audio = decode_audio(input_path)
    total_s = len(audio) / SAMPLE_RATE

    probs: Optional[np.ndarray] = None
    backend = cfg.backend
    if backend not in ("silero", "energy"):
        logger.warning("Unknown SEGMENTER_BACKEND %r; using silero", backend)
        backend = "silero"
    if backend == "silero":
        try:
            probs = _get_vad(cfg.model_path).speech_probs(audio)
        except Exception:
            logger.exception(
                "Silero VAD unavailable; falling back to energy-based segmentation"
            )
            backend = "energy"
    if probs is None:
        probs = energy_speech_probs(audio)

    regions = probs_to_speech_regions(probs, len(audio), cfg)
    utterances = build_utterances(regions, probs, cfg)

    segments: List[Segment] = []
    dropped = 0
    for utterance in utterances:
        start, end = utterance["start"], utterance["end"]
        samples = audio[start:end]
        metrics = _segment_metrics(samples, probs, start, end)
        if (
            metrics["rms_dbfs"] < cfg.min_rms_dbfs
            or metrics["clipping_ratio"] > cfg.max_clipping_ratio
            or metrics["avg_speech_prob"] < cfg.min_avg_speech_prob
        ):
            dropped += 1
            continue

        start_ms = int(round(start * 1000 / SAMPLE_RATE))
        end_ms = int(round(end * 1000 / SAMPLE_RATE))
        filename = f"{base_name}_{start_ms:08d}-{end_ms:08d}.wav"
        path = os.path.join(output_dir, filename)
        try:
            write_wav(path, samples)
        except Exception:
            # Never leave partial files behind: the output directory feeds
            # the labeling queue and stray files would corrupt it.
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    logger.warning("Could not remove partial segment file %s", path)
            raise
        segments.append(
            Segment(
                path=path,
                filename=filename,
                start_s=start / SAMPLE_RATE,
                end_s=end / SAMPLE_RATE,
                duration_s=(end - start) / SAMPLE_RATE,
                avg_speech_prob=metrics["avg_speech_prob"],
                rms_dbfs=metrics["rms_dbfs"],
                clipping_ratio=metrics["clipping_ratio"],
            )
        )

    kept_speech_s = sum(s.duration_s for s in segments)
    logger.info(
        "Segmented %s (%.1fs) using %s backend: %d speech regions -> %d utterances "
        "(%d dropped by quality gates), %.1fs of speech kept",
        input_path, total_s, backend, len(regions), len(segments), dropped, kept_speech_s,
    )
    return segments
