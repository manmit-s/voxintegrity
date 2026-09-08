# Vaani Kavach Repository Audit

Date: 2026-09-08

## Scope

This audit covered the FastAPI entry point, model loading, REST and WebSocket inference paths, Supabase integration, frontend routing and history rendering, Python syntax, frontend build/lint, and the Dockerfile. Existing worktree changes were left untouched.

## Validation Summary

| Check | Result | Evidence |
|---|---|---|
| `Push-Location frontend; npm run build` | PASS | Vite transformed 134 modules and produced `frontend/dist` successfully. |
| `Push-Location frontend; npm run lint` | FAIL | ESLint 8.57.1 could not find an ESLint configuration file. |
| `Push-Location backend; python -c "import app.main"` | FAIL | `ModuleNotFoundError: No module named 'supabase'`. |
| `python -m compileall -q backend/app` | PASS | Backend Python files compile. |
| VS Code diagnostics on touched entry files | PASS | No editor errors reported. |
| Docker image build | NOT RUN | The Docker build command was skipped, so container-specific behavior remains unverified. |

## Critical Issues

### 1. Backend cannot start in the active environment

**Severity:** Blocker

**Reproduction:**

```powershell
Push-Location backend
python -c "import app.main"
Pop-Location
```

**Observed:**

```text
ModuleNotFoundError: No module named 'supabase'
```

The import chain is `app.main` -> `api.v1.router` -> `endpoints.auth` -> `db.supabase`, where `from supabase import create_client, Client` fails. `supabase==2.3.0` is listed in [backend/requirements.txt](backend/requirements.txt), but the interpreter used by the active backend terminal does not have the requirements installed.

**Impact:** Uvicorn cannot import the application, so `/health`, REST verification, authentication, history, and WebSocket inference are all unavailable in this environment.

**Remediation:** Create or activate the backend virtual environment and run `python -m pip install -r backend/requirements.txt` (or install from `backend`), then repeat the import check. Add a documented environment bootstrap command and a CI smoke test that imports `app.main`.

### 2. The Docker image does not contain the configured model artifacts

**Severity:** Blocker for real inference deployments

The Dockerfile copies only `app`:

```dockerfile
COPY app ./app
```

The default model path in [backend/app/core/config.py](backend/app/core/config.py) points to `ml_pipeline/weights/ast_finetuned_fp32_dml.onnx`, and the fallback points to the sibling CPU export. Neither `ml_pipeline/weights` nor the model's external `.onnx.data` file is copied into the image. The `.gitignore` also ignores model artifacts except `.gitkeep`.

**Impact:** A container built from this repository cannot load the intended ONNX model. [backend/app/ml_integration/model_loader.py](backend/app/ml_integration/model_loader.py) falls back to `NeutralFallbackModel`, which returns `0.5` for every input. The API can appear healthy while returning a neutral, non-ML result.

**Remediation:** Decide how production obtains the model: package an explicitly versioned artifact, download it during deployment, or mount it as a volume. Set `MODEL_PATH` to an absolute/container path and make startup fail loudly when a real model is required instead of silently serving constant scores. Add a startup test that asserts the loaded model is not `NeutralFallbackModel` in production mode.

### 3. The configured relative model path is not portable to the container

**Severity:** High

`settings.project_root` uses `Path(__file__).resolve().parents[3]`. In the source checkout this reaches the repository root, but with the Dockerfile layout (`/app/app/core/config.py`) it resolves above `/app`. Therefore the default relative `ml_pipeline/weights/...` path is resolved against the wrong location even if the model were copied into `/app`.

**Impact:** Container deployments can report a missing model despite having an artifact in the expected application directory.

**Remediation:** Use an explicit deployment root, such as a `MODEL_PATH` environment variable, or derive the container path from a deliberate fixed layout. Test `settings.resolved_model_path()` in both a checkout and container-like layout.

## High-Priority Integration Issues

### 4. WebSocket sessions are not persisted to history

**Severity:** High

The main capture workflow uses `openInferenceStream()` in [frontend/src/services/api.js](frontend/src/services/api.js), but the WebSocket stop branch in [backend/app/api/v1/endpoints/inference.py](backend/app/api/v1/endpoints/inference.py) only sends `StreamDone` and closes the socket. It never calls `_save_session()`.

The REST `/verify` path does call `_save_session()`, but it is not the path used by the live microphone/file workflow.

**Impact:** A user can complete a live analysis and see a summary, but the result is absent from Supabase history.

**Remediation:** On a valid WebSocket stop, persist the summary and score events once, including elapsed duration. Ensure disconnect/finalization is idempotent so a normal stop does not create duplicates and an unexpected disconnect follows the intended retention policy.

### 5. History API data does not match the History page data model

**Severity:** High

The backend returns Supabase rows with fields such as `id`, `created_at`, `call_duration`, `spoof_score`, `percent_high_risk`, and `verdict` from [backend/app/api/v1/endpoints/history.py](backend/app/api/v1/endpoints/history.py). The frontend [frontend/src/pages/History.jsx](frontend/src/pages/History.jsx) renders `item.file`, `item.date`, and `item.confidence`.

**Impact:** When API history rows are present, file/date/confidence columns render blank or incorrect values. The page's fallback mock rows hide this until a non-empty API response replaces them.

**Remediation:** Define a shared response contract or normalize API records in the frontend. Map `created_at` to the displayed date, `spoof_score` to an explicit confidence/verdict presentation, and provide a stable filename field if the database stores one. Add a fixture-based rendering test.

### 6. History is not reachable from the active frontend router

**Severity:** High

[frontend/src/App.jsx](frontend/src/App.jsx) imports the console and mock screens but does not import or register `History`. There is no `/history` route.

**Impact:** Even if backend persistence and the History component were correct, users cannot navigate to session history through the active application.

**Remediation:** Add the route and a visible navigation path from the active console, or remove the unused page until the workflow is complete. Verify direct navigation and browser refresh behavior.

## Medium-Priority Issues

### 7. Frontend lint is configured as a script but has no configuration

**Severity:** Medium

`frontend/package.json` defines `npm run lint` as `eslint . --ext js,jsx`, but no ESLint configuration exists. The command fails before checking source code with “ESLint couldn't find a configuration file.” It also traversed the generated `dist` directory after the successful build.

**Remediation:** Add a project ESLint configuration compatible with the React/Vite codebase and ignore `dist`, or remove the script until linting is intentionally configured. Run lint in CI after the config is added.

### 8. README setup instructions reference a missing backend `.env.example`

**Severity:** Medium

[README.md](README.md) instructs users to run `cp .env.example .env` from `backend`, but no `backend/.env.example` exists in the repository. The only environment template is `frontend/.env.example`.

**Impact:** A new contributor cannot follow the documented setup without guessing the required Supabase, model, CORS, and runtime settings.

**Remediation:** Add `backend/.env.example` with safe placeholders and document which values are required for local auth/history and which are optional for model-only smoke tests. Update the commands for Windows PowerShell as well as POSIX shells.

### 9. Authentication makes API functionality unavailable without Supabase, while the active frontend has no auth flow

**Severity:** Medium

`get_current_user()` rejects requests when `supabase` is unconfigured, and `/verify` and `/history` depend on it. The active `App.jsx` routes do not provide login/register UI. The frontend has a `login()` API helper, but no active page calls it.

**Impact:** A fresh local install can build the UI but cannot use REST verification or history unless Supabase credentials and an existing authenticated session are supplied externally. The live WebSocket endpoint does not authenticate the socket at all.

**Remediation:** Choose and document one supported local mode. For production, authenticate WebSockets and expose a complete auth flow. For development, provide an explicit mock-user mode guarded by an environment flag rather than silently weakening production auth.

### 10. `_prediction_score()` cannot handle a dictionary model result as written

**Severity:** Medium

In [backend/app/api/v1/endpoints/inference.py](backend/app/api/v1/endpoints/inference.py), the result is converted with `float(model.predict(waveform))` before the following dictionary check. A model adapter returning `{"score": ...}` therefore raises `TypeError` before the check executes.

**Impact:** Future adapter implementations that return structured predictions will produce a 500 response instead of being normalized.

**Remediation:** Inspect the raw result first, then extract the configured key, and only afterward convert to `float`. Add unit tests for scalar, dictionary, non-finite, and out-of-range results.

## Lower-Priority / Coverage Gaps

### 11. No automated application test suite or CI test execution

**Severity:** Medium

The `test/` directory contains manual probes and scripts, but there is no pytest suite, frontend test script, or CI workflow that runs startup, REST, WebSocket, or contract tests. The existing checks cannot detect the history mismatch, missing route, or WebSocket persistence regression.

**Remediation:** Add focused tests for model path resolution, score normalization, WebSocket start/chunk/stop, session persistence, auth failures, and frontend history normalization. Add backend import and frontend build/lint jobs to CI.

### 12. Docker compatibility remains unverified

**Severity:** Medium, unverified

`backend/requirements.txt` pins `onnxruntime-directml`, while the Dockerfile uses `python:3.11-slim`, a Linux base image. DirectML is Windows-oriented, so the dependency may fail to install or may not provide the intended execution provider in Linux. The Docker build was not run because the command was skipped.

**Remediation:** Use a Linux-compatible `onnxruntime` dependency for Linux containers, keep DirectML in a Windows-specific requirements path, or publish separate images. Run and record a real `docker build` and container `/health` smoke test.

## Recommended Order of Work

1. Install and lock the backend environment, then make `import app.main` and `/health` pass.
2. Establish an explicit model delivery strategy and fix container path resolution.
3. Add WebSocket session persistence and protect it with an integration test.
4. Register the History route and normalize the backend/frontend history contract.
5. Add backend environment documentation and a deliberate local-auth mode.
6. Configure linting and add CI tests for startup, build, and the core inference workflow.
