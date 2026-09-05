# Vaani Kavach ML Approach and Progress Report

## 1. Executive Summary

The machine-learning work follows a sensible progression:

1. Understand the audio data and confirm that it can be used by the chosen model.
2. Establish a pretrained baseline using an Audio Spectrogram Transformer (AST).
3. Fine-tune the model on ASVspoof2019-LA data and export it for application use.
4. Test how well the ASVspoof-trained model works on a different, more realistic deepfake-audio dataset.
5. Adapt the model to that new domain using transfer learning.

The initial pretrained AST model reported **91.00% accuracy** and **5.08% EER** on the ASVspoof evaluation setup. When the ASVspoof fine-tuned model was used directly on the Gary Stafford dataset, its default 0.50 threshold produced only **53.05% accuracy**, although its **81.55% ROC-AUC** showed that it still learned useful ranking information. Calibrating the decision threshold improved the reported accuracy to **78.67%**.

The strongest reported result came from fine-tuning only the classifier head on the Gary Stafford data: **84.49% accuracy** and **97.94% ROC-AUC** on the notebook's validation split. These results are promising, but they should be treated as reported experiment results rather than fully reproducible measurements because the notebooks do not contain saved execution outputs and some referenced artifacts are external.

## 2. Problem Definition

The system classifies an audio recording as one of two classes:

- **Bonafide / real:** naturally recorded human speech.
- **Spoof / fake:** speech generated or manipulated by a synthetic-voice or deepfake system.

This is a binary classification problem. The model receives an audio waveform and returns a score or probability indicating how likely the recording is to be fake.

## 3. Overall Approach

The project uses an **Audio Spectrogram Transformer (AST)**. An AST converts audio into a time-frequency representation and uses Transformer attention to identify patterns associated with real or synthetic speech.

The pipeline standardizes audio before inference:

- Convert stereo audio to mono.
- Resample audio to **16 kHz**.
- Crop long recordings or zero-pad short recordings to **4 seconds**, equivalent to 64,000 samples at 16 kHz.
- Convert the audio into model features with the AST feature extractor.
- Predict the real/fake class.

The experiments use two related but different datasets:

| Dataset | Role |
| --- | --- |
| ASVspoof2019-LA | Baseline evaluation and initial fine-tuning |
| Gary Stafford deepfake-audio-detection | Cross-domain evaluation and domain adaptation |

The second dataset is important because a model can perform well on the data used during development but fail when audio comes from different recording conditions, platforms, codecs, speakers, or generation systems.

## 4. Notebook-by-Notebook Progress

### 4.1 Data exploration - `01_data_exploration.ipynb`

The first notebook investigates the ASVspoof2019-LA test split using Hugging Face streaming. Streaming means that samples are read incrementally instead of downloading the entire dataset into memory or storing all raw audio locally.

The notebook checks waveform shape, data type, duration, amplitude statistics, sampling rate, and labels. It also displays a waveform and a mel spectrogram.

An **mel spectrogram** shows how much audio energy exists in different frequency bands over time. The mel scale is designed to approximate how humans perceive pitch, making it useful for speech and audio classification.

The notebook treats the labels as:

- `bonafide = 0`
- `spoof = 1`

The exploration concludes that the audio is available at 16 kHz and is compatible with the later AST pipeline. The label distribution inspection is limited to the first 200 streamed samples, so it should not be considered a full dataset analysis.

### 4.2 Pretrained baseline - `02_baseline_test.ipynb`

The second notebook evaluates the pretrained model:

`MattyB95/AST-ASVspoof2019-Synthetic-Voice-Detection`

It evaluates up to 500 examples from the Hugging Face `test` split. The AST feature extractor handles the model-specific input preparation.

The reported baseline results are:

| Metric | Result |
| --- | ---: |
| Accuracy | **91.00%** |
| EER | **5.08%** |

**Accuracy** is the percentage of examples classified correctly.

**Equal Error Rate (EER)** is the point where the false acceptance rate and false rejection rate are approximately equal. A lower EER is better. In this project, it gives a compact measure of how well the model separates real and fake audio around an operating threshold.

This baseline creates a reference point for judging whether later fine-tuning improves the model. The accompanying `baseline_results.json` records the same values. The JSON calls the split `eval`, while the notebook actually loads the Hugging Face `test` split; this is a naming difference in the experiment artifact, not necessarily a modeling difference.

### 4.3 ASVspoof fine-tuning - `03_finetuning.ipynb`

The third notebook fine-tunes AST on locally mounted ASVspoof2019-LA training data. Labels are read from the official protocol file, and the audio files are loaded from FLAC files.

Preprocessing is made explicit:

- Load audio with `librosa`.
- Convert to mono.
- Resample to 16 kHz.
- Crop or zero-pad to 4 seconds.

The training configuration uses:

- Optimizer: **AdamW**
- Learning rate: `1e-5`
- Batch size: `4`
- Epochs: `1`
- Loss: cross-entropy
- Checkpoint interval: every 500 batches

**AdamW** is a gradient-based optimizer commonly used for Transformer models. It updates model weights to reduce prediction error while applying weight decay to help control overfitting.

**Cross-entropy loss** measures how different the model's predicted class probabilities are from the correct labels. Lower loss generally means that the model is making more confident correct predictions.

The loop reports loss and accuracy while training and saves model and optimizer checkpoints. A later notebook expects a checkpoint named `ast_epoch1_batch6000.pt`.

No saved output confirms the final training accuracy, loss, dataset size, or successful completion of that exact checkpoint. The notebook also has no active validation loop, so this stage establishes a training checkpoint rather than a complete generalization evaluation.

### 4.4 Checkpoint evaluation and export - `04_finetuning_evaluation.ipynb`

The fourth notebook prepares the ASVspoof development set and loads the fine-tuned checkpoint. It recreates the same 16 kHz, mono, 4-second preprocessing so that training and inference use a consistent input format.

The development evaluation loop exists, but it is commented out. Therefore, the notebook as written does not actively generate the development predictions required by the next results notebook.

The notebook exports the model into deployment-friendly formats:

- FP32 PyTorch checkpoint: `ast_finetuned_fp32.pth`
- ONNX model: `ast_finetuned_fp32.onnx`

**FP32** means the model weights use standard 32-bit floating-point values. This is straightforward and numerically stable, although it may use more memory than reduced-precision formats.

**ONNX** is an interchange format that allows a model trained in one framework to run in other inference environments. The notebook checks the ONNX graph and compares PyTorch and ONNX logits using `np.allclose`.

The ONNX export uses opset 14, a dynamic batch dimension, and an input shape of `[1, 1024, 128]`. The notebooks do not preserve the numerical export comparison or model file sizes in their outputs.

### 4.5 First fine-tuning results - `05_finetuning_results.ipynb`

The fifth notebook is designed to analyze predictions saved in `dev_eval_A_checkpoint.npz`. It calculates a broad set of metrics:

- Accuracy
- Balanced accuracy
- Precision and recall
- F1 score
- Matthews correlation coefficient (MCC)
- ROC-AUC
- Confusion matrix
- False acceptance rate (FAR)
- False rejection rate (FRR)
- EER

**Precision** answers: when the model predicts a class, how often is it correct?

**Recall** answers: of all examples that truly belong to a class, how many did the model find?

**F1 score** combines precision and recall into one value. It is useful when both missed detections and false alarms matter.

**ROC-AUC** measures how well the model ranks positive examples above negative examples over many possible thresholds. A value near 1.0 is strong; 0.5 is close to random ranking.

**MCC** summarizes all four confusion-matrix outcomes and is useful when class balance or error types make accuracy misleading.

The required `.npz` prediction file is not present in the workspace, and no saved outputs are included. Consequently, exact Fine-Tune A metrics cannot be independently confirmed from the repository.

### 4.6 Cross-domain evaluation - `06_evaluate_ast_model_on_gary_stafford_dataset.ipynb`

The sixth notebook tests the exported model on the Gary Stafford deepfake-audio-detection dataset. This is a **zero-shot evaluation**: the model is evaluated on the new dataset without first being fine-tuned on it.

The notebook reports 1,866 examples, balanced between 933 real and 933 synthetic recordings. It applies the same mono conversion, 16 kHz resampling, and 4-second crop/pad process. It evaluates both the PyTorch and ONNX versions and reports that their predictions match 100%.

The results show why the decision threshold matters:

| Metric | Default threshold 0.50 | EER threshold 0.9997 | Youden threshold 0.9996 |
| --- | ---: | ---: | ---: |
| Accuracy | 53.05% | 76.74% | **78.67%** |
| ROC-AUC | 81.55% | 81.55% | 81.55% |

At the default threshold, almost every recording is classified as fake. The reported result is 933 of 933 fake recordings detected, but only 57 of 933 real recordings detected. This produces poor accuracy even though the ROC-AUC remains useful.

This demonstrates **domain shift**: the statistical properties of the new audio domain differ from the ASVspoof training domain. It also demonstrates **calibration**: selecting a threshold appropriate for the new domain can improve final class decisions without changing the underlying ranking quality measured by ROC-AUC.

The calibrated thresholds were selected using the same dataset being reported, so these accuracy values are not an unbiased estimate of future production performance. A separate calibration set should be used for a stronger evaluation.

### 4.7 Gary Stafford fine-tuning - `07_finetune_on_gary_stafford_dataset.ipynb`

The seventh notebook adapts the model to the Gary Stafford domain. It creates a stratified 80/20 split with seed 42, reported as 1,492 training examples and 374 validation examples.

Training-only augmentation is applied:

- Random gain between `0.8` and `1.2`.
- Small Gaussian noise with standard deviation `0.002`.

The notebook uses **transfer learning**. Instead of training a large AST model from scratch, it starts from an existing model and reuses its learned audio representation. All model parameters except the classifier are frozen, so only the final classification head is trained. This is also called **linear probing**.

The training configuration is:

- Batch size: `16`
- Maximum epochs: `6`
- Learning rate: `1e-3`
- Optimizer: AdamW
- Weight decay: `0.01`
- Loss: cross-entropy
- Early stopping patience: `2` epochs
- Best checkpoint criterion: validation ROC-AUC

**Early stopping** stops training when validation performance stops improving. This reduces wasted training and can reduce overfitting.

The reported comparison is:

| Model state | Accuracy | ROC-AUC |
| --- | ---: | ---: |
| Zero-shot, threshold 0.50 | 53.05% | 81.55% |
| Calibrated zero-shot | 78.67% | 81.55% |
| Gary Stafford linear probe | **84.49%** | **97.94%** |

The notebook reports 185 of 187 synthetic validation examples detected and recommends `ast_gary_finetuned_best.pth` as the deployment artifact.

There is one important implementation issue: the code tracks the best validation-AUC weights but does not reload those weights before generating the final classification report. The final report may therefore describe the last epoch rather than the best epoch. The reported results should be re-run after explicitly loading the best checkpoint.

## 5. What the Results Mean

The experiments show three separate lessons:

1. The pretrained AST model is effective on ASVspoof-style audio.
2. Directly applying that model to a different audio domain causes a large threshold and calibration problem.
3. Even limited domain-specific training of the classifier head substantially improves separation on the Gary Stafford validation split.

The increase from 81.55% to 97.94% ROC-AUC suggests that the pretrained AST representation contains useful general audio information and that the classifier can be adapted to the new domain. However, the validation split comes from the same source dataset used for fine-tuning, so it does not prove performance on unseen platforms, speakers, codecs, or deepfake generators.

## 6. Current Progress Summary

### Completed or substantially implemented

- ASVspoof audio and label exploration.
- Pretrained AST baseline evaluation.
- ASVspoof fine-tuning code and checkpointing.
- PyTorch and ONNX export path.
- Cross-domain evaluation on Gary Stafford data.
- Threshold calibration experiment.
- Gary Stafford classifier-head fine-tuning with augmentation and early stopping.
- Reported best artifact: `ast_gary_finetuned_best.pth`.

### Incomplete or requiring verification

- Persisted notebook outputs are missing, so several reported numbers cannot be independently reproduced from the notebooks alone.
- The ASVspoof development evaluation loop is commented out.
- `dev_eval_A_checkpoint.npz` is not available in the repository.
- Training and validation results should be regenerated and saved as artifacts.
- The best Gary Stafford checkpoint must be reloaded before the final metrics are calculated.
- An independent test set is needed after Gary Stafford fine-tuning.

## 7. Recommended Next Steps

1. Re-run notebooks 04 through 07 and save outputs, metrics, confusion matrices, and prediction artifacts.
2. Fix notebook 07 so it reloads `best_model_weights` before calculating the final report.
3. Keep calibration data separate from the final test data.
4. Add an independent test split or cross-validation for the Gary Stafford dataset.
5. Record the number and identity of skipped or failed audio decodes instead of silently converting failures to zero audio.
6. Compare the final PyTorch and ONNX models on a fixed test set and save the maximum absolute logit difference.
7. Evaluate on audio from additional speakers, generators, platforms, and compression levels to measure robustness.
8. Choose the production threshold using an explicit operational goal, such as minimizing false accusations or maintaining a required fake-detection recall.

## 8. Glossary

| Term | Plain-English meaning |
| --- | --- |
| AST | Audio Spectrogram Transformer; a Transformer model that analyzes time-frequency audio features. |
| Audio waveform | The raw sequence of air-pressure measurements represented as numbers. |
| Mel spectrogram | A visual and numerical representation of audio energy over time and perceptual frequency bands. |
| Feature extractor | Prepares raw audio in the exact format expected by a model. |
| Fine-tuning | Further training an existing model on a task-specific dataset. |
| Transfer learning | Reusing knowledge learned from one dataset for a related task or domain. |
| Linear probing | Freezing the main model and training only its final classifier. |
| Domain shift | A difference between the data used for training and the data encountered during evaluation or deployment. |
| Threshold | The score boundary used to convert a probability or score into a class decision. |
| Calibration | Selecting or adjusting a threshold so decisions match the desired real-world error trade-off. |
| ROC-AUC | A threshold-independent measure of how well scores rank one class above the other. |
| EER | The point where false acceptance and false rejection rates are approximately equal. |
| ONNX | A portable model format for running neural networks across frameworks and runtimes. |
| AdamW | An optimizer commonly used to train Transformer models. |
| Epoch | One complete pass through the training data. |
| Checkpoint | A saved copy of model weights, usually used to resume training or deploy a model. |

## 9. Source Notebooks

- `01_data_exploration.ipynb`
- `02_baseline_test.ipynb`
- `03_finetuning.ipynb`
- `04_finetuning_evaluation.ipynb`
- `05_finetuning_results.ipynb`
- `06_evaluate_ast_model_on_gary_stafford_dataset.ipynb`
- `07_finetune_on_gary_stafford_dataset.ipynb`
- `baseline_results.json`