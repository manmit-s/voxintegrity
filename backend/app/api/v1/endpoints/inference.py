import numpy as np
from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect

from app.ml_integration.model_loader import get_model
from app.ml_integration.preprocessor import preprocess_audio
from app.ml_integration.sliding_window import SlidingWindowInference

router = APIRouter()


@router.post("/verify")
async def verify_voice(file: UploadFile = File(...)):
    try:
        waveform = await preprocess_audio(file)
        model = get_model()
        score = float(model.predict(waveform))
        verdict = "spoof" if score >= 0.5 else "bonafide"
        return {"filename": file.filename, "score": score, "verdict": verdict}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/detect-deepfake")
async def detect_deepfake(file: UploadFile = File(...)):
    return {"result": "pending-model-integration", "filename": file.filename}


@router.websocket("/ws/stream")
async def stream_inference(websocket: WebSocket):
    await websocket.accept()
    model = get_model()
    sliding_window = SlidingWindowInference(model=model)

    try:
        while True:
            try:
                message = await websocket.receive()
            except RuntimeError:
                break

            if "bytes" not in message or not message["bytes"]:
                continue

            chunk = message["bytes"]
            if len(chunk) % 4 != 0:
                chunk = chunk[: len(chunk) - (len(chunk) % 4)]

            if not chunk:
                continue

            audio_chunk = np.frombuffer(chunk, dtype=np.float32).astype(np.float32, copy=False)
            scores = sliding_window.add_chunk(audio_chunk)

            for score in scores:
                verdict = "spoof" if score >= 0.5 else "bonafide"
                payload = {"spoof_score": round(float(score), 6), "verdict": verdict}
                try:
                    await websocket.send_json(payload)
                except Exception:
                    break

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        sliding_window.reset()
        try:
            await websocket.close()
        except Exception:
            pass
