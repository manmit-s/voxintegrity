import collections
from typing import Deque, List

import numpy as np

SAMPLE_RATE = 16000
WINDOW_SECONDS = 3.0
HOP_SECONDS = 0.5
SMOOTHING_WINDOW = 3


class SlidingWindowInference:
    def __init__(
        self,
        model,
        sample_rate: int = SAMPLE_RATE,
        window_seconds: float = WINDOW_SECONDS,
        hop_seconds: float = HOP_SECONDS,
        smoothing_window: int = SMOOTHING_WINDOW,
    ):
        self.model = model
        self.sample_rate = sample_rate
        self.window_samples = int(sample_rate * window_seconds)
        self.hop_samples = int(sample_rate * hop_seconds)
        self.smoothing_window = max(1, smoothing_window)
        self.buffer = np.empty(0, dtype=np.float32)
        self.score_history: Deque[float] = collections.deque(maxlen=self.smoothing_window)

    def add_chunk(self, chunk: np.ndarray) -> List[float]:
        if chunk is None:
            return []

        chunk = np.asarray(chunk, dtype=np.float32).ravel()
        if chunk.size == 0:
            return []

        if self.buffer.size == 0:
            self.buffer = chunk.copy()
        else:
            self.buffer = np.concatenate((self.buffer, chunk)).astype(np.float32, copy=False)

        results: List[float] = []
        while self.buffer.size >= self.window_samples:
            window = self.buffer[: self.window_samples].astype(np.float32, copy=False)
            self.buffer = self.buffer[self.hop_samples :]

            raw_score = float(self.model.predict(window))
            self.score_history.append(raw_score)
            smoothed_score = float(np.mean(list(self.score_history))) if self.score_history else raw_score
            results.append(smoothed_score)

        return results

    def reset(self) -> None:
        self.buffer = np.empty(0, dtype=np.float32)
        self.score_history.clear()

    @property
    def current_buffer_length(self) -> int:
        return int(self.buffer.size)
