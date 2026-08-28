from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

import numpy as np
import torch
from sklearn.metrics import accuracy_score, roc_curve
from tqdm.auto import tqdm
from transformers import AutoFeatureExtractor, ASTForAudioClassification

try:
    from data_loader import load_asvspoof2019_la
except ImportError:  # pragma: no cover - support `python ml_pipeline/src/evaluate.py`
    from ml_pipeline.src.data_loader import load_asvspoof2019_la


DEFAULT_MODEL_NAME = "MattyB95/AST-ASVspoof2019-Synthetic-Voice-Detection"
DEFAULT_OUTPUT_PATH = "ml_pipeline/notebooks/baseline_results.json"


def _detect_spoof_index(model: ASTForAudioClassification) -> int:
    """Pick the index for the spoof class in a binary AST classifier."""
    label_map = {int(k): str(v).lower() for k, v in getattr(model.config, "id2label", {}).items()}
    if label_map:
        for idx, label_name in sorted(label_map.items()):
            if label_name == "spoof":
                return idx
    return 1 if getattr(model.config, "num_labels", 2) > 1 else 0


def _compute_eer(y_true: np.ndarray, spoof_scores: np.ndarray) -> float:
    """Compute EER using the ROC curve on spoof probabilities.

    Finds the point where FPR ~= FNR.
    """
    fpr, tpr, _ = roc_curve(y_true, spoof_scores, pos_label=1)
    fnr = 1.0 - tpr
    eer_index = np.argmin(np.abs(fpr - fnr))
    return float(fpr[eer_index])


def evaluate_baseline(
    model_name: str = DEFAULT_MODEL_NAME,
    dataset_split: str = "eval",
    output_path: str = DEFAULT_OUTPUT_PATH,
    max_samples: Optional[int] = None,
    show_progress: bool = True,
) -> dict:
    """Evaluate the baseline model on the ASVspoof eval split and write a JSON summary.

    Consumes audio via :func:`load_asvspoof2019_la` in streaming mode,
    runs inference with ``AutoFeatureExtractor`` + ``ASTForAudioClassification``,
    computes Accuracy and EER, and always dumps the result JSON (even for
    partial ``max_samples`` runs for debugging).

    Parameters
    ----------
    model_name : str
        Hugging Face model identifier.
    dataset_split : str
        Split name per contract (``"eval"`` is mapped to HF ``"test"`` inside the loader).
    output_path : str
        Path to write ``{"model_name","dataset_split","accuracy","eer"}`` JSON.
    max_samples : int | None
        Limit number of samples for debugging. ``None`` evaluates the full split.
    show_progress : bool
        If True, display a tqdm progress bar (CLI). If False, silent iteration
        for library/backend imports.

    Returns
    -------
    dict
        ``{"model_name": str, "dataset_split": str, "accuracy": float, "eer": float}``
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    feature_extractor = AutoFeatureExtractor.from_pretrained(model_name)
    model = ASTForAudioClassification.from_pretrained(model_name).to(device)
    model.eval()

    # Prepare streaming iterator with optional progress bar
    raw_stream = load_asvspoof2019_la(split=dataset_split, streaming=True)
    if show_progress:
        # Use tqdm; total is max_samples if provided (unknown otherwise for streaming)
        stream = tqdm(raw_stream, desc="Evaluating", total=max_samples, unit="sample")
    else:
        stream = raw_stream

    y_true: list[int] = []
    spoof_scores: list[float] = []
    batch_waveforms: list[np.ndarray] = []
    batch_labels: list[int] = []

    for idx, example in enumerate(stream):
        if max_samples is not None and idx >= max_samples:
            break

        waveform = np.asarray(example["audio"]["array"], dtype=np.float32)
        label = int(example["label"])

        batch_waveforms.append(waveform)
        batch_labels.append(label)

        if len(batch_waveforms) == 8:
            inputs = feature_extractor(
                batch_waveforms,
                sampling_rate=16000,
                return_tensors="pt",
                padding=True,
            ).to(device)

            with torch.no_grad():
                logits = model(**inputs).logits

            spoof_index = _detect_spoof_index(model)
            scores = torch.softmax(logits, dim=-1)[:, spoof_index].cpu().numpy().astype(np.float32)

            y_true.extend(batch_labels)
            spoof_scores.extend(scores.tolist())
            batch_waveforms = []
            batch_labels = []

    # Flush remaining partial batch
    if batch_waveforms:
        inputs = feature_extractor(
            batch_waveforms,
            sampling_rate=16000,
            return_tensors="pt",
            padding=True,
        ).to(device)

        with torch.no_grad():
            logits = model(**inputs).logits

        spoof_index = _detect_spoof_index(model)
        scores = torch.softmax(logits, dim=-1)[:, spoof_index].cpu().numpy().astype(np.float32)
        y_true.extend(batch_labels)
        spoof_scores.extend(scores.tolist())

    if not y_true:
        raise ValueError("No samples were processed during baseline evaluation.")

    y_true_arr = np.asarray(y_true, dtype=np.int64)
    score_arr = np.asarray(spoof_scores, dtype=np.float32)
    predictions = (score_arr >= 0.5).astype(np.int64)

    accuracy = float(accuracy_score(y_true_arr, predictions))
    eer = _compute_eer(y_true_arr, score_arr)

    result = {
        "model_name": model_name,
        "dataset_split": dataset_split,
        "accuracy": accuracy,
        "eer": eer,
    }

    # Always write JSON, even for partial runs — contract verification for debugging
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)
        file.write("\n")

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate the ASVspoof baseline model.")
    parser.add_argument("--model-name", type=str, default=DEFAULT_MODEL_NAME, help="HF model id")
    parser.add_argument("--dataset-split", type=str, default="eval", help="Dataset split (eval -> test)")
    parser.add_argument("--output-path", type=str, default=DEFAULT_OUTPUT_PATH, help="Output JSON path")
    parser.add_argument("--max-samples", type=int, default=None, help="Limit samples (None = full split)")
    parser.add_argument(
        "--show-progress",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Show tqdm progress bar (use --no-show-progress for silent mode)",
    )
    args = parser.parse_args()

    result = evaluate_baseline(
        model_name=args.model_name,
        dataset_split=args.dataset_split,
        output_path=args.output_path,
        max_samples=args.max_samples,
        show_progress=args.show_progress,
    )
    print(json.dumps(result, indent=2))
