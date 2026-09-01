"""Lazy, process-wide model loading for voice verification."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

import numpy as np

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


class HuggingFaceAudioClassifier:
    """Small adapter that exposes a common ``predict(waveform)`` interface."""

    def __init__(self, model: Any, feature_extractor: Any) -> None:
        self.model = model.eval()
        self.feature_extractor = feature_extractor
        self.id2label = {
            int(key): str(value).lower()
            for key, value in getattr(model.config, "id2label", {}).items()
        }

    def predict(self, waveform: np.ndarray) -> float:
        import torch

        samples = np.asarray(waveform, dtype=np.float32).reshape(-1)
        inputs = self.feature_extractor(
            samples, sampling_rate=settings.SAMPLE_RATE, return_tensors="pt", padding=True
        )
        with torch.inference_mode():
            logits = self.model(**inputs).logits[0]
            probabilities = torch.softmax(logits, dim=-1).detach().cpu().numpy()

        # Model cards use different label spellings; identify the bonafide class
        # from metadata instead of relying on a class index.
        for index, label in self.id2label.items():
            if any(token in label for token in ("bonafide", "bona_fide", "real", "genuine")):
                return float(probabilities[index])
        for index, label in self.id2label.items():
            if any(token in label for token in ("spoof", "fake", "synthetic")):
                return float(1.0 - probabilities[index])
        # ASVspoof-style binary heads conventionally put bonafide in class 0.
        return float(probabilities[0])


class OnnxAudioClassifier:
    """Adapter for the exported AST ONNX graph and its external weight file."""

    def __init__(self, path: Path) -> None:
        import onnxruntime as ort

        available = set(ort.get_available_providers())
        providers = [name for name in ("DmlExecutionProvider", "CPUExecutionProvider") if name in available]
        self.session = ort.InferenceSession(str(path), providers=providers or ["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape

    def predict(self, waveform: np.ndarray) -> float:
        import librosa

        samples = np.asarray(waveform, dtype=np.float32).reshape(-1)
        # The exported AST graph accepts [batch, frames, mel_bins], rather than
        # waveform samples. Match the standard AST 16 kHz frontend.
        if len(self.input_shape) == 3:
            frames = int(self.input_shape[1]) if isinstance(self.input_shape[1], int) else 1024
            mel_bins = int(self.input_shape[2]) if isinstance(self.input_shape[2], int) else 128
            mel = librosa.feature.melspectrogram(
                y=samples,
                sr=settings.SAMPLE_RATE,
                n_fft=400,
                hop_length=160,
                n_mels=mel_bins,
                power=2.0,
            )
            features = librosa.power_to_db(mel, ref=np.max).T
            if features.shape[0] < frames:
                features = np.pad(features, ((0, frames - features.shape[0]), (0, 0)))
            else:
                features = features[:frames]
            samples = features.astype(np.float32, copy=False)
            model_input = samples[None, :, :]
        else:
            model_input = samples[None, :]
        output = np.asarray(
            self.session.run([self.output_name], {self.input_name: model_input})[0]
        ).reshape(-1)
        if output.size == 1:
            value = float(output[0])
            return value if 0.0 <= value <= 1.0 else float(1.0 / (1.0 + np.exp(-value)))
        shifted = output - np.max(output)
        probabilities = np.exp(shifted) / np.exp(shifted).sum()
        index = min(max(settings.MODEL_REAL_CLASS_INDEX, 0), len(probabilities) - 1)
        return float(probabilities[index])


def _load_local_model(path: Path) -> Any:
    import torch

    try:
        model = torch.jit.load(str(path), map_location="cpu")
    except RuntimeError:
        model = torch.load(str(path), map_location="cpu")

    if isinstance(model, dict) and "model" in model:
        model = model["model"]
    if not hasattr(model, "eval"):
        raise TypeError("Local model must be a Torch module or a checkpoint containing 'model'.")
    return model.eval()


def _load_huggingface_model() -> HuggingFaceAudioClassifier:
    from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

    feature_extractor = AutoFeatureExtractor.from_pretrained(
        settings.MODEL_HF_ID, local_files_only=settings.MODEL_HF_LOCAL_FILES_ONLY
    )
    model = AutoModelForAudioClassification.from_pretrained(
        settings.MODEL_HF_ID,
        trust_remote_code=True,
        local_files_only=settings.MODEL_HF_LOCAL_FILES_ONLY,
    )
    return HuggingFaceAudioClassifier(model, feature_extractor)


def _load(path: Path | None = None) -> tuple[Any, str]:
    model_path = path or settings.resolved_model_path()
    if model_path.exists():
        try:
            if model_path.suffix.lower() == ".onnx":
                return OnnxAudioClassifier(model_path), str(model_path)
            return _load_local_model(model_path), str(model_path)
        except Exception:
            logger.exception("Unable to load local model from %s; trying HF baseline", model_path)

    try:
        return _load_huggingface_model(), settings.MODEL_HF_ID
    except Exception:
        logger.exception("Unable to load Hugging Face baseline; using neutral fallback")
        return NeutralFallbackModel(), "neutral-fallback (no trained model available)"


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
