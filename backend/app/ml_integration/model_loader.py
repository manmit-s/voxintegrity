import threading
from pathlib import Path
from typing import Optional

import numpy as np
import onnxruntime as ort
from transformers import AutoFeatureExtractor

from app.core.config import settings

MODEL_REPO_ID = "MattyB95/AST-ASVspoof2019-Synthetic-Voice-Detection"


class ASTDirectMLModel:
    _instance: Optional["ASTDirectMLModel"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_path: str | None = None):
        if getattr(self, "_initialized", False):
            return

        raw_path = model_path or settings.MODEL_PATH
        self.model_path = Path(raw_path)
        if not self.model_path.is_absolute():
            self.model_path = (Path(__file__).resolve().parents[3] / self.model_path).resolve()

        self.session = None
        self.feature_extractor = None
        self._load_model()
        self._initialized = True

    def _load_model(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(f"ONNX model not found at: {self.model_path}")

        session_options = ort.SessionOptions()
        session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        try:
            self.session = ort.InferenceSession(
                str(self.model_path),
                sess_options=session_options,
                providers=["DmlExecutionProvider", "CPUExecutionProvider"],
                provider_options=[{"device_id": 0}, {}],
            )
        except Exception:
            self.session = ort.InferenceSession(
                str(self.model_path),
                sess_options=session_options,
                providers=["CPUExecutionProvider"],
            )

        self.feature_extractor = AutoFeatureExtractor.from_pretrained(MODEL_REPO_ID)

    def preprocess(self, waveform: np.ndarray, sampling_rate: int = 16000):
        audio = np.asarray(waveform, dtype=np.float32).ravel()
        if audio.size == 0:
            raise ValueError("Waveform is empty.")

        inputs = self.feature_extractor(
            audio,
            sampling_rate=sampling_rate,
            return_tensors="np",
        )
        if not isinstance(inputs, dict):
            raise TypeError("Feature extractor did not return a tensor dictionary.")
        return inputs

    def predict(self, waveform: np.ndarray, sampling_rate: int = 16000) -> float:
        if self.session is None:
            raise RuntimeError("ONNX model is not loaded.")

        features = self.preprocess(waveform, sampling_rate=sampling_rate)
        session_inputs = self.session.get_inputs()
        ort_inputs = {}

        for session_input in session_inputs:
            name = session_input.name
            if name in features:
                ort_inputs[name] = features[name]
                continue

            normalized = {k.lower().replace("-", "_"): v for k, v in features.items()}
            for key, value in normalized.items():
                if key in name.lower().replace("-", "_") or name.lower().replace("-", "_") in key:
                    ort_inputs[name] = value
                    break

        if not ort_inputs:
            raise ValueError("Could not map model inputs to feature extractor output.")

        outputs = self.session.run(None, ort_inputs)
        logits = np.asarray(outputs[0], dtype=np.float32)
        if logits.ndim == 1:
            logits = logits.reshape(1, -1)

        logits = logits - np.max(logits, axis=-1, keepdims=True)
        exp_scores = np.exp(logits)
        probs = exp_scores / np.sum(exp_scores, axis=-1, keepdims=True)
        return float(probs[0][1])


def get_model(model_path: str | None = None):
    return ASTDirectMLModel(model_path=model_path or settings.MODEL_PATH)


def load_model(path: str | None = None):
    return get_model(path)
