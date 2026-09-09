# Vaani Kavach

AI-powered real-time detection of voice cloning and synthetic-speech impersonation attacks for Smart India Hackathon 2026 PS26104.

## 1. Problem statement

Voice cloning and synthetic speech generation tools can now produce convincing impersonations from a very short reference sample, making caller identity and voice familiarity unreliable in sensitive scenarios. As a result, fraud and social-engineering risks increase for executive impersonation, financial approvals, and trusted-person interactions. Vaani Kavach is designed to provide a near-real-time spoof-risk signal that helps flag suspicious or AI-generated audio before a risky action is taken.

## 2. Key features

The current implementation in this repo includes:

- Live microphone and file-based verification through the React frontend and FastAPI backend
- Sliding-window audio analysis using a 2-second window and 0.5-second hop
- REST endpoint for uploaded audio verification
- WebSocket endpoint for real-time streaming inference and score events
- Visible live spoof telemetry and verdict display in the frontend
- Final summary with average score, confidence, and verdict
- Supabase-backed auth and history retrieval for authenticated users
- Session history page that loads recent verification records from the backend
- ONNX model adapter with CPU fallback logic when the local model is unavailable

The active backend route wiring is in `backend/app/api/v1/router.py`, and the actual inference flow is implemented in `backend/app/api/v1/endpoints/inference.py`.

## 3. Architecture overview

The project is organized into three main working layers:

- Frontend: React + Vite app in `frontend/`
  - App entry: `frontend/src/App.jsx`
  - Recorder logic: `frontend/src/components/VoiceRecorder.jsx`
  - Verification page: `frontend/src/pages/Verify.jsx`
  - History page: `frontend/src/pages/History.jsx`
  - API layers: `frontend/src/services/api.js` and `frontend/src/services/supabaseClient.js`

- Backend: FastAPI service in `backend/app/`
  - Router: `backend/app/api/v1/router.py`
  - Auth endpoints: `backend/app/api/v1/endpoints/auth.py`
  - History endpoints: `backend/app/api/v1/endpoints/history.py`
  - Inference endpoints: `backend/app/api/v1/endpoints/inference.py`
  - Runtime config: `backend/app/core/config.py`
  - Model loader: `backend/app/ml_integration/model_loader.py`
  - Audio preprocessing: `backend/app/ml_integration/preprocessor.py`
  - Supabase client: `backend/app/db/supabase.py`

- ML pipeline: training and export code in `ml_pipeline/`
  - Configs: `ml_pipeline/configs/hyperparams.yaml`
  - Source code: `ml_pipeline/src/`
  - Notebooks: `ml_pipeline/notebooks/`
  - Model artifacts: `ml_pipeline/weights/`

The backend loads a local ONNX artifact and serves the result to the frontend through REST and WebSocket APIs. The frontend records audio or accepts uploads, sends chunks to the backend, and renders the live score graph and final verdict.

## 4. Tech stack

### Backend
From `backend/requirements.txt`:

- Python: 3.11 (Dockerfile targets `python:3.11-slim`)
- FastAPI: 0.110.0
- Uvicorn: 0.27.0
- Pydantic: 2.6.0
- pydantic-settings: 2.1.0
- python-multipart: 0.0.6
- python-jose: 3.3.0
- passlib: 1.7.4
- supabase: 2.3.0
- gotrue: 2.0.0
- httpx: 0.24.1
- librosa: 0.10.1
- numpy: 1.26.0
- onnxruntime-directml: 1.23.0

### Frontend
From `frontend/package.json`:

- React: 18.2.0
- React DOM: 18.2.0
- Vite: 5.0.0
- React Router DOM: 6.22.0
- Axios: 1.6.0
- @supabase/supabase-js: 2.39.0
- Recharts: 2.15.1
- ESLint: 8.55.0

## 5. Setup instructions

### Prerequisites

- Python 3.11
- Node.js and npm
- Git access to the repository
- Local access to the ONNX model payloads used by the backend

### Backend setup

From the repo root:

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Frontend setup

From the repo root:

```bash
cd frontend
npm install
```

### Model weights

The ONNX model files are not committed to Git. The runtime configuration expects the model in the local repo under:

- `ml_pipeline/weights/ast_finetuned_fp32_dml.onnx`
- `ml_pipeline/weights/ast_finetuned_fp32_dml.onnx.data`

These files are local runtime assets and are intentionally kept out of Git tracking, which is why the `ml_pipeline/weights/` directory is ignored by Git. The backend resolves the model path from `backend/app/core/config.py` and loads the local artifact at startup.

## 6. Environment variables required

The backend settings are defined in `backend/app/core/config.py`, and the frontend example template is in `frontend/.env.example`.

### Backend environment variables

- `SECRET_KEY`
- `BACKEND_CORS_ORIGINS`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `MODEL_PATH`
- `MODEL_FALLBACK_PATH`
- `DML_DEVICE_ID`
- `WINDOW_SIZE_MS`
- `HOP_SIZE_MS`
- `SCORE_SMOOTHING_WINDOWS`
- `SAMPLE_RATE`
- `VERDICT_THRESHOLD`
- `MODEL_REAL_CLASS_INDEX`
- `SUPABASE_SERVICE_KEY`

Do not commit actual secret values to the repo. Keep them in a local `.env` file inside the `backend/` directory if needed for your local environment.

### Frontend environment variables

From `frontend/.env.example`:

- `VITE_API_URL`
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`

## 7. How to run

Run the backend first, then the frontend.

### Start the backend

```bash
cd backend
# activate the virtual environment if not already active
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Start the frontend

```bash
cd frontend
npm run dev
```

### Health check

Open the backend health route in a browser or terminal:

```text
http://localhost:8000/health
```

Expected response:

```json
{"status": "ok", "service": "vaani-kavach-backend"}
```

## 8. API endpoints

The API is mounted under `/api/v1` via `backend/app/api/v1/router.py`.

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Root API welcome response |
| `/health` | GET | Health-check endpoint |
| `/api/v1/auth/register` | POST | Register a user through Supabase |
| `/api/v1/auth/login` | POST | Sign in with email/password |
| `/api/v1/voice/verify` | POST | Upload an audio file and receive a single verification result |
| `/api/v1/history/` | GET | Fetch the current authenticated user’s verification history |
| `/api/v1/history/{record_id}` | GET | Fetch one verification record by ID |
| `/api/v1/voice/stream-inference` | WebSocket | Real-time PCM16 streaming verification with live score outputs |

### WebSocket flow

The live inference websocket expects JSON messages with action types such as:

- `start`
- `chunk`
- `stop`

It sends `session_id` and `audio_format` metadata to begin the capture, emits score events for each sliding window, and produces a final summary when the stream ends.

## 9. Testing

The repo includes a manual microphone smoke-test script at `test/mic_live_test.py`.

Run it while the backend is running:

```bash
python test/mic_live_test.py
```

This script:

- connects to `ws://localhost:8000/api/v1/voice/stream-inference`
- starts a microphone capture session
- sends PCM16 chunks from the microphone in real time
- prints the incoming live score events until interrupted

This is a runtime smoke test rather than a formal automated test suite.

## 10. Team and roles

The repo includes a team and Git workflow map in `Git_Sanity_SIH_2026.md`.

| Member | Role in workflow |
|---|---|
| Manmit | Repository owner + PR reviewer/merger |
| Soham | Collaborator + feature branches |
| Vedant | Collaborator + feature branches |
| Ninad | Collaborator + feature branches |
| Devyani | Collaborator + feature branches |
| Tanvi | Collaborator + feature branches |

## 11. Known limitations and scope

### In scope

The implemented solution is scoped to:

- spoof-risk detection via sliding-window inference
- live verification from microphone or uploaded audio
- real-time frontend telemetry and final verdict display
- authenticated session history when Supabase is configured
- local ONNX inference with CPU fallback behavior

### Out of scope / future work

The repo also documents explicit future-scope boundaries in `WOW_factors.md` and `Git_Sanity_SIH_2026.md`, including:

- multi-class attack-type attribution (voice-changer vs. TTS vs. replay)
- multilingual or multi-accent tuning beyond the initial dataset
- telecom or banking SDK integration
- on-device NPU or native call-app inference
- broader production deployment beyond the hackathon prototype boundary

This is a working prototype focused on demonstrating a real-time spoof-risk detection flow rather than a full commercial anti-spoofing deployment.

## 12. Acknowledgements

- ASVspoof Challenge for benchmark evaluation data
- Hugging Face model publishers and supporting open-source evaluation workflows used during exploration and baseline validation

---

## License

The repository does not currently declare a public license file, so licensing status remains to be finalized before wider distribution.
