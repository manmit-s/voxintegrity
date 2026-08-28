from __future__ import annotations

from typing import Any, Iterator, Tuple

import numpy as np
import torch
from datasets import load_dataset
from torch.utils.data import IterableDataset

HF_ASVSPOOF_DATASET = "SpeechAntiSpoofingBenchmarks/ASVspoof2019_LA"

__all__ = ["HF_ASVSPOOF_DATASET", "load_asvspoof2019_la", "VoiceDataset"]


def _normalize_label(raw_label: Any) -> Tuple[int, str]:
    """Map dataset labels to binary bonafide/spoof semantics.

    Returns
    -------
    (label_int, label_name)
        0 / "bonafide" for real speech, 1 / "spoof" for synthetic.
    """
    if raw_label is None:
        raise ValueError("Dataset sample is missing a label field.")

    if isinstance(raw_label, (int, np.integer)):
        label_value = int(raw_label)
        if label_value == 0:
            return 0, "bonafide"
        if label_value == 1:
            return 1, "spoof"

    if isinstance(raw_label, str):
        normalized = raw_label.strip().lower().replace("_", " ")
        if normalized in {"bonafide", "real", "bona fide", "bona fide audio"}:
            return 0, "bonafide"
        if normalized in {"spoof", "fake", "attack"}:
            return 1, "spoof"

    if isinstance(raw_label, dict):
        # Some dataset versions store label as a mapping; normalize the common keys.
        for key in ("label", "value"):
            if key in raw_label:
                return _normalize_label(raw_label[key])

    raise ValueError(f"Unsupported label value for ASVspoof: {raw_label!r}")


def load_asvspoof2019_la(split: str = "eval", streaming: bool = True) -> Iterator[dict]:
    """Stream ASVspoof2019 LA examples without writing raw audio to disk.

    Loads ``SpeechAntiSpoofingBenchmarks/ASVspoof2019_LA`` via the Hugging Face
    ``datasets`` library in streaming mode by default so no audio files are
    persisted locally. The raw waveform is held only in runtime memory.

    Parameters
    ----------
    split : str
        Dataset split requested by the caller. ``"eval"`` is mapped to the
        Hugging Face split name ``"test"`` for ASVspoof2019 LA.
    streaming : bool
        If True, the dataset is loaded in streaming mode (``streaming=True``)
        so nothing is stored locally.

    Yields
    ------
    dict
        ``{"audio": {"array": np.ndarray, "sampling_rate": 16000}, "label": int, "label_name": str}``
        where ``label`` is 0 for bonafide and 1 for spoof.
    """
    normalized_split = str(split).lower()
    if normalized_split == "eval":
        dataset_split = "test"
    else:
        dataset_split = normalized_split

    dataset = load_dataset(HF_ASVSPOOF_DATASET, split=dataset_split, streaming=streaming)

    for example in dataset:
        audio = example.get("audio", {})
        if isinstance(audio, dict):
            waveform = np.asarray(audio.get("array", []), dtype=np.float32)
            sample_rate = int(audio.get("sampling_rate", 16000))
        else:
            waveform = np.asarray(audio, dtype=np.float32)
            sample_rate = 16000

        if waveform.ndim > 1:
            waveform = waveform.reshape(-1)

        label_value, label_name = _normalize_label(example.get("label"))

        yield {
            "audio": {
                "array": waveform.astype(np.float32),
                "sampling_rate": sample_rate,
            },
            "label": int(label_value),
            "label_name": label_name,
        }


class VoiceDataset(IterableDataset):
    """PyTorch ``IterableDataset`` wrapper around the streaming ASVspoof loader.

    Provides compatibility with ``train.py`` which does::

        from src.data_loader import VoiceDataset
        DataLoader(VoiceDataset(split="train"), batch_size=...)

    The dataset is streaming — samples are yielded on-the-fly without writing
    raw audio to disk. Each iteration yields the same contract as
    :func:`load_asvspoof2019_la`::

        {"audio": {"array": ndarray, "sampling_rate": 16000}, "label": int, "label_name": str}

    Parameters
    ----------
    split : str
        Dataset split (``"train"``, ``"dev"``, ``"eval"``). ``"eval"`` is
        internally mapped to ``"test"`` for the HF dataset.
    streaming : bool
        Whether to load in streaming mode. Kept ``True`` by default to avoid
        local persistence of audio.
    """

    def __init__(self, split: str = "train", streaming: bool = True) -> None:
        super().__init__()
        self.split = split
        self.streaming = streaming

    def __iter__(self) -> Iterator[dict]:
        yield from load_asvspoof2019_la(split=self.split, streaming=self.streaming)
