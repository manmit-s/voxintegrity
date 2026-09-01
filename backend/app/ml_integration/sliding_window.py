"""Reusable sliding-window score smoothing for binary audio inference."""

from collections import deque
from typing import Deque

import numpy as np


class SlidingWindowInference:
    def __init__(self, model, sample_rate: int = 16000, window_seconds: float = 2.0,
                 hop_seconds: float = 0.5, smoothing_window: int = 3):
        self.model = model
        self.sample_rate = sample_rate
        self.window_samples = int(sample_rate * window_seconds)
        self.hop_samples = int(sample_rate * hop_seconds)
        self.score_history: Deque[float] = deque(maxlen=max(1, smoothing_window))
        self.buffer = np.empty(0, dtype=np.float32)

    def add_chunk(self, chunk: np.ndarray) -> list[float]:
        chunk = np.asarray(chunk, dtype=np.float32).reshape(-1)
        if not chunk.size:
            return []
        self.buffer = np.concatenate((self.buffer, chunk))
        results = []
        while self.buffer.size >= self.window_samples:
            score = float(self.model.predict(self.buffer[: self.window_samples]))
            self.score_history.append(score)
            results.append(float(np.mean(self.score_history)))
            self.buffer = self.buffer[self.hop_samples:]
        return results

    def reset(self) -> None:
        self.buffer = np.empty(0, dtype=np.float32)
        self.score_history.clear()
