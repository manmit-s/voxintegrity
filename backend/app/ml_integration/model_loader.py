"""Lazy, process-wide model loading for voice verification."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

import numpy as np
from scipy.signal import stft

from app.core.config import settings

logger = logging.getLogger(__name__)

_model: Any | None = None
_model_name: str = "unloaded"
_model_lock = threading.Lock()


class NeutralFallbackModel:
    """Keeps the API usable when no model artifact or HF cache is available.

    A neutral score deliberately avoids presenting a fabricated detection result as
    an ML prediction. Deployments should set MODEL_PATH or allow the HF baseline
    to download once.
    """

    def predict(self, waveform: np.ndarray) -> float:
        return 0.5


class OnnxAudioClassifier:
    """Adapter for the exported AST ONNX graph and its external weight file."""

    def __init__(self, path: Path, dml_device_id: int | None = None) -> None:
        import onnxruntime as ort

        available = set(ort.get_available_providers())
        device_id = settings.DML_DEVICE_ID if dml_device_id is None else dml_device_id
        providers: list[Any] = []
        if "DmlExecutionProvider" in available:
            providers.append(("DmlExecutionProvider", {"device_id": device_id}))
        if "CPUExecutionProvider" in available:
            providers.append("CPUExecutionProvider")
        self.session = ort.InferenceSession(str(path), providers=providers or ["CPUExecutionProvider"])
        self._ort = ort
        self._model_path = path
        self._cpu_session: Any | None = None
        self.using_cpu_fallback = False
        logger.info("ONNX Runtime providers: %s", self.session.get_providers())
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape
        self._mel_filter: np.ndarray | None = None
        self._probe_directml()

    def _switch_to_cpu(self) -> None:
        self._cpu_session = self._ort.InferenceSession(
            str(self._model_path), providers=["CPUExecutionProvider"]
        )
        self.session = self._cpu_session
        self.using_cpu_fallback = True

    def _probe_directml(self) -> None:
        """Validate DirectML with a realistic-shaped input before a live capture starts.

        The probe uses random input matching real mel-feature statistics (dB-scale
        spectrograms around -55 dB), because an all-zero tensor can pass ops that
        fail on genuine data.
        """
        if "DmlExecutionProvider" not in self.session.get_providers():
            return
        shape = tuple(dimension if isinstance(dimension, int) else 1 for dimension in self.input_shape)
        probe_input = np.random.default_rng(0).normal(-55.0, 18.0, shape).astype(np.float32)
        try:
            self.session.run([self.output_name], {self.input_name: probe_input})
            logger.info("DirectML probe PASSED: %s executing on GPU (device_id=%s).", self.session.get_providers()[0], settings.DML_DEVICE_ID)
        except Exception:
            logger.warning("DirectML probe FAILED for this ONNX graph; falling back to CPU ONNX Runtime. Real inference would have crashed on the GPU path.", exc_info=True)
            self._switch_to_cpu()

    @staticmethod
    def _slaney_mel_filter(sample_rate: int, n_fft: int, n_mels: int) -> np.ndarray:
        """Build librosa-compatible Slaney-normalized triangular mel filters.

        This intentionally avoids ``librosa.feature.melspectrogram``: with the current
        environment it spends minutes in Numba compilation before an inference can start.
        """
        def hz_to_mel(freq: np.ndarray) -> np.ndarray:
            f_sp = 200.0 / 3
            min_log_hz = 1000.0
            min_log_mel = min_log_hz / f_sp
            logstep = np.log(6.4) / 27.0
            result = freq / f_sp
            mask = freq >= min_log_hz
            result[mask] = min_log_mel + np.log(freq[mask] / min_log_hz) / logstep
            return result

        def mel_to_hz(mel: np.ndarray) -> np.ndarray:
            f_sp = 200.0 / 3
            min_log_hz = 1000.0
            min_log_mel = min_log_hz / f_sp
            logstep = np.log(6.4) / 27.0
            result = f_sp * mel
            mask = mel >= min_log_mel
            result[mask] = min_log_hz * np.exp(logstep * (mel[mask] - min_log_mel))
            return result

        mel_points = np.linspace(hz_to_mel(np.array([0.0]))[0], hz_to_mel(np.array([sample_rate / 2]))[0], n_mels + 2)
        hz_points = mel_to_hz(mel_points)
        fft_freqs = np.fft.rfftfreq(n_fft, 1 / sample_rate)
        lower = (fft_freqs[None, :] - hz_points[:-2, None]) / (hz_points[1:-1, None] - hz_points[:-2, None])
        upper = (hz_points[2:, None] - fft_freqs[None, :]) / (hz_points[2:, None] - hz_points[1:-1, None])
        filters = np.maximum(0.0, np.minimum(lower, upper))
        filters *= (2.0 / (hz_points[2:] - hz_points[:-2]))[:, None]
        return filters.astype(np.float32)

    def _ast_features(self, samples: np.ndarray, frames: int, mel_bins: int) -> np.ndarray:
        n_fft = 400
        # librosa defaults to a centered, reflection-padded STFT with a Hann window.
        padded = np.pad(samples, (n_fft // 2, n_fft // 2), mode="reflect")
        _, _, spectrum = stft(
            padded,
            fs=settings.SAMPLE_RATE,
            window="hann",
            nperseg=n_fft,
            noverlap=n_fft - 160,
            nfft=n_fft,
            boundary=None,
            padded=False,
        )
        if self._mel_filter is None or self._mel_filter.shape[0] != mel_bins:
            self._mel_filter = self._slaney_mel_filter(settings.SAMPLE_RATE, n_fft, mel_bins)
        mel = self._mel_filter @ np.square(np.abs(spectrum))
        db = 10.0 * np.log10(np.maximum(mel, 1e-10))
        db -= np.max(db)
        features = db.T
        if features.shape[0] < frames:
            features = np.pad(features, ((0, frames - features.shape[0]), (0, 0)))
        return features[:frames].astype(np.float32, copy=False)

    def predict(self, waveform: np.ndarray) -> float:
        samples = np.asarray(waveform, dtype=np.float32).reshape(-1)
        # The exported AST graph accepts [batch, frames, mel_bins], rather than
        # waveform samples. Match the standard AST 16 kHz frontend.
        if len(self.input_shape) == 3:
            frames = int(self.input_shape[1]) if isinstance(self.input_shape[1], int) else 1024
            mel_bins = int(self.input_shape[2]) if isinstance(self.input_shape[2], int) else 128
            samples = self._ast_features(samples, frames, mel_bins)
            model_input = samples[None, :, :]
        else:
            model_input = samples[None, :]
        try:
            raw_output = self.session.run([self.output_name], {self.input_name: model_input})[0]
        except Exception:
            # This exported graph currently fails in DirectML's Reshape implementation
            # (node_view_2, 0x8007023E) on the RTX 3050 driver/runtime. Retain DirectML
            # as the preferred path but keep the demo functional with ORT CPU execution.
            if self.using_cpu_fallback or "DmlExecutionProvider" not in self.session.get_providers():
                raise
            logger.exception("DirectML inference failed; switching this ONNX session to CPU")
            self._switch_to_cpu()
            raw_output = self.session.run([self.output_name], {self.input_name: model_input})[0]
        output = np.asarray(raw_output).reshape(-1)
        if output.size == 1:
            value = float(output[0])
            return value if 0.0 <= value <= 1.0 else float(1.0 / (1.0 + np.exp(-value)))
        shifted = output - np.max(output)
        probabilities = np.exp(shifted) / np.exp(shifted).sum()
        index = min(max(settings.MODEL_REAL_CLASS_INDEX, 0), len(probabilities) - 1)
        return float(probabilities[index])


def _load(path: Path | None = None) -> tuple[Any, str]:
    model_path = path or settings.resolved_model_path()
    if not model_path.exists() and path is None:
        # The DML-safe export is generated by test/patch_graph_dml.py; fall back to the
        # original export when only that artifact is present (CPU-only deployments).
        fallback = settings.project_root / settings.MODEL_FALLBACK_PATH
        if fallback.exists():
            logger.warning("Configured ONNX model %s missing; using CPU-safe fallback export %s", model_path, fallback)
            model_path = fallback
    if model_path.exists():
        try:
            if model_path.suffix.lower() == ".onnx":
                return OnnxAudioClassifier(model_path), str(model_path)
            raise ValueError("Only the supported ONNX deployment artifact may be loaded.")
        except Exception:
            logger.exception("Unable to load local ONNX model from %s", model_path)
    else:
        logger.error("Configured ONNX model is missing: %s", model_path)
    return NeutralFallbackModel(), "neutral-fallback (configured ONNX model unavailable)"


def get_model() -> Any:
    """Return the cached model, loading it once on the first request."""

    global _model, _model_name
    if _model is None:
        with _model_lock:
            if _model is None:
                _model, _model_name = _load()
    return _model


def get_model_name() -> str:
    get_model()
    return _model_name


def load_model(path: str | None = None) -> Any:
    """Explicitly reload the process-wide model, primarily for admin/tests."""

    global _model, _model_name
    explicit_path = Path(path).expanduser().resolve() if path else None
    with _model_lock:
        _model, _model_name = _load(explicit_path)
        return _model
