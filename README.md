# Vaani Kavach

> AI-powered real-time detection of voice cloning and synthetic-speech impersonation attacks.
> Built for **Smart India Hackathon 2026 — PS 26104**, sponsored by AICTE Cyber Security Cell.

<!-- TODO: replace with an actual banner/demo GIF once the live-graph UI is working -->

## The problem

Neural voice cloning now needs only a few seconds of reference audio to produce a convincing
fake. Threat actors are using this to impersonate CXOs, officials, and trusted contacts to push
through fraudulent fund transfers and social-engineering attacks over phone calls and VoIP —
and caller ID, call-backs, and "I know their voice" are no longer reliable defenses.

**Vaani Kavach** analyzes an audio stream in near real time and produces a live, continuously
updating "spoof score" — flagging the likely use of a cloned or AI-generated voice before a
sensitive action (a fund transfer, a confidential disclosure) is taken.

## What it does

- Ingests audio in short overlapping windows (sliding-window inference) from a file or a live
  microphone feed
- Runs each window through a speech-deepfake detection model and produces a bonafide/spoof
  confidence score
- Smooths scores across a rolling window and streams them to the frontend as they're computed
- Renders a **live score graph** during playback/call, and a **post-session summary** —
  score distribution, percentage of the session flagged high-risk, and an overall verdict

## What it does *not* claim to do

Being upfront about scope, because overclaiming here is worse than a modest, honest system:

- This is **near-real-time**, not frame-by-frame instantaneous — scores update on a
  configurable hop interval (see [Latency](#latency-notes)), not every audio sample
- Multi-class attribution (e.g. distinguishing a voice-changer from a TTS clone from a replay
  attack) is a stretch goal, not the core deliverable — the core deliverable is bonafide vs.
  spoofed
- Accuracy is benchmarked in-domain (ASVspoof-style data); performance on spoofing methods
  unseen during training/fine-tuning is expected to be weaker, and we say so in our results
  rather than hiding it

## Architecture

```
┌─────────────────┐      ┌──────────────────────┐      ┌────────────────────┐
│   Frontend       │◄────►│   Backend (FastAPI)   │◄────►│   ML Pipeline       │
│   React + Vite   │  WS  │   REST + WebSocket    │      │   HF Transformers   │
│                  │      │                        │      │   (AST / wav2vec2)  │
└─────────────────┘      └──────────────────────┘      └────────────────────┘
                                     │
                                     ▼
                              ┌─────────────┐
                              │  Supabase    │
                              │  (auth/history)│
                              └─────────────┘
```

- **Frontend** — records/streams audio, renders the live score graph and post-session summary
- **Backend** — FastAPI service exposing REST + WebSocket endpoints; loads the trained model
  once at startup and serves sliding-window inference
- **ML pipeline** — separate, versioned training/fine-tuning code; produces a frozen model
  artifact that the backend loads. Training code and serving code share the same
  feature-extraction logic to avoid train/serve skew (see [Repo structure](#repo-structure))

## Repo structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/     # auth, inference (REST + WS), history
│   │   ├── core/                 # config, security
│   │   ├── db/                   # Supabase client
│   │   ├── ml_integration/       # model_loader.py, preprocessor.py
│   │   │                         #   preprocessor.py wraps ml_pipeline/src/feature_extraction.py
│   │   │                         #   — never reimplements it
│   │   └── schemas/              # Pydantic request/response contracts
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/           # VoiceRecorder, live score chart
│       ├── pages/                # Verify, History
│       └── services/             # api.js, supabaseClient.js
├── ml_pipeline/
│   ├── configs/hyperparams.yaml
│   ├── data/                     # raw/ and processed/ — gitignored, pulled at runtime
│   ├── notebooks/                # exploration + baseline eval, not production code
│   ├── src/
│   │   ├── architecture.py
│   │   ├── data_loader.py
│   │   ├── feature_extraction.py # single source of truth — backend imports this
│   │   ├── train.py
│   │   └── evaluate.py
│   └── weights/                  # gitignored — model artifacts, not committed
└── README.md
```

## Model

- **Baseline (Day 1–2):** [`MattyB95/AST-ASVspoof2019-Synthetic-Voice-Detection`](https://huggingface.co/MattyB95/AST-ASVspoof2019-Synthetic-Voice-Detection),
  an Audio Spectrogram Transformer pretrained and fine-tuned on ASVspoof2019 LA. Used to get the
  full pipeline (ingest → inference → live score → summary) working end-to-end before any
  custom training.
- **Target:** fine-tune a wav2vec2/AASIST-style front end on ASVspoof2019 LA (+ augmentation)
  for improved accuracy and better generalization to unseen spoofing methods.
- **Dataset:** [ASVspoof 2019 LA](https://www.asvspoof.org/index2019.html) — loaded via the
  Hugging Face `datasets`/`huggingface_hub` API directly into the training environment (Colab),
  not stored locally.

<!-- TODO: fill in once you have numbers — don't ship this table empty -->
| Model | Dataset | Accuracy | EER |
|---|---|---|---|
| AST baseline (off-the-shelf) | ASVspoof2019 LA (eval) | TBD | TBD |
| Fine-tuned (ours) | ASVspoof2019 LA (eval) | TBD | TBD |

## Latency notes

Real-time detection is achieved via **sliding-window inference**, not a streaming-native
architecture:

- Window size: `~2–3s` of audio per inference call
- Hop size: `~0.5–1s` — this is the actual cadence at which the displayed score updates
- Scores are smoothed (rolling average) across the last few windows before being sent to the
  frontend, to avoid a single noisy window causing a visible flicker

This is the same general approach used in production anti-spoofing and diarization systems —
we are not inventing a new trick, we're applying the field's standard one.

## Getting started

<!-- TODO: confirm these commands once Docker/compose setup is finalized -->

```bash
# clone
git clone <repo-url>
cd <repo-name>

# backend
cd backend
cp .env.example .env      # fill in Supabase keys, model path, etc.
pip install -r requirements.txt
uvicorn app.main:app --reload

# frontend
cd frontend
npm install
npm run dev
```

### ML pipeline (training/fine-tuning)

Dataset and training are meant to run in Colab (GPU access, no need to bring large audio data
locally):

```bash
cd ml_pipeline
pip install -r requirements-ml.txt
# see notebooks/01_data_exploration.ipynb to pull ASVspoof2019 via the HF datasets API
# see notebooks/02_baseline_test.ipynb for baseline model evaluation
python src/train.py --config configs/hyperparams.yaml
```

## Team

<!-- TODO: confirm final role split before submission -->

| Name | Role |
|---|---|
| Manmit Samal | AI/ML, Backend |
| Devyani | AI/ML |
| Tanvi | DevOps, AI/ML |
| Soham | General Purpose |
| Vedant | General Purpose |
| Ninad | General Purpose |

## Acknowledgements

- [ASVspoof Challenge](https://www.asvspoof.org/) for the benchmark dataset
- [MattyB95](https://huggingface.co/MattyB95) for the pretrained baseline models on Hugging Face

---

<!-- TODO: pick a license before making the repo public -->
## License

TBD