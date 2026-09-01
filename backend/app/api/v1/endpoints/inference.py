"""Public REST and WebSocket endpoints for voice-spoof inference."""

from __future__ import annotations

import asyncio
import base64
import binascii
from collections import deque
from typing import Any

import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.ml_integration.preprocessor import preprocess_audio
from app.ml_integration.model_loader import get_model, get_model_name

router = APIRouter()


def _prediction_score(model: Any, waveform: np.ndarray) -> float:
    """Run an adapter or a simple local Torch model and return a bonafide score."""
    if not waveform.size:
        raise ValueError("Audio contains no samples.")

    waveform = np.nan_to_num(waveform.astype(np.float32, copy=False))
    if hasattr(model, "predict"):
        result = model.predict(waveform)
    else:
        # Local Torch modules are expected to return one probability/logit per sample.
        import torch

        with torch.inference_mode():
            result = model(torch.from_numpy(waveform).unsqueeze(0))
        if hasattr(result, "logits"):
            result = result.logits
        values = torch.as_tensor(result).detach().cpu().flatten()
        if values.numel() == 1:
            result = torch.sigmoid(values[0]).item()
        else:
            result = torch.softmax(values, dim=0)[0].item()

    if isinstance(result, dict):
        result = result.get("score", result.get("bonafide_score"))
    score = float(result)
    if not np.isfinite(score):
        raise ValueError("Model returned a non-finite score.")
    return float(np.clip(score, 0.0, 1.0))


def _verdict(score: float) -> str:
    return "real" if score >= settings.VERDICT_THRESHOLD else "fake"


@router.post("/verify")
async def verify_voice(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=422, detail="An audio file is required.")
    try:
        waveform = await preprocess_audio(file)
        model = get_model()
        score = await asyncio.to_thread(_prediction_score, model, waveform)
        return {
            "filename": file.filename,
            "score": score,
            "verdict": _verdict(score),
            "confidence": max(score, 1.0 - score),
            "model_name": get_model_name(),
            "window_size_ms": settings.WINDOW_SIZE_MS,
            "hop_size_ms": settings.HOP_SIZE_MS,
        }
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _summary(scores: list[float]) -> dict[str, Any]:
    average = float(np.mean(scores)) if scores else 0.5
    return {
        "total_windows": len(scores),
        "avg_score": average,
        "high_risk_windows": sum(score < settings.VERDICT_THRESHOLD for score in scores),
        "verdict": _verdict(average),
    }


@router.websocket("/stream-inference")
async def stream_inference(websocket: WebSocket) -> None:
    """Receive base64 PCM16 chunks and emit a prediction for every hop window."""
    await websocket.accept()
    window_frames = settings.SAMPLE_RATE * settings.WINDOW_SIZE_MS // 1000
    hop_frames = settings.SAMPLE_RATE * settings.HOP_SIZE_MS // 1000
    if window_frames <= 0 or hop_frames <= 0:
        await websocket.send_json({"action": "error", "detail": "Invalid window configuration."})
        await websocket.close(code=1011)
        return

    session_id: str | None = None
    audio_buffer = np.empty(0, dtype=np.float32)
    buffer_start_frame = 0
    total_frames = 0
    next_window_end = window_frames
    scores: list[float] = []
    smoothing = deque(maxlen=max(1, settings.SCORE_SMOOTHING_WINDOWS))
    sent_done = False

    try:
        while True:
            message = await websocket.receive_json()
            action = message.get("action")

            if action == "start":
                if message.get("audio_format") != "pcm16_16khz":
                    await websocket.send_json({"action": "error", "detail": "audio_format must be pcm16_16khz."})
                    continue
                session_id = str(message.get("session_id") or "")
                if not session_id:
                    await websocket.send_json({"action": "error", "detail": "session_id is required."})
                    continue
                audio_buffer = np.empty(0, dtype=np.float32)
                buffer_start_frame = total_frames = 0
                next_window_end = window_frames
                scores.clear()
                smoothing.clear()
                await websocket.send_json({"session_id": session_id, "action": "started"})
                continue

            if action == "stop":
                if session_id and message.get("session_id") not in (None, session_id):
                    await websocket.send_json({"action": "error", "detail": "session_id does not match."})
                    continue
                await websocket.send_json({"session_id": session_id, "action": "done", "final_summary": _summary(scores)})
                sent_done = True
                await websocket.close()
                return

            if action != "chunk" or not session_id:
                await websocket.send_json({"action": "error", "detail": "Send start before PCM chunks."})
                continue
            if message.get("session_id") != session_id:
                await websocket.send_json({"action": "error", "detail": "session_id does not match."})
                continue

            try:
                raw = base64.b64decode(message["audio_bytes"], validate=True)
                if len(raw) % 2:
                    raise ValueError("PCM16 payload must contain complete 16-bit samples.")
                chunk = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
            except (KeyError, ValueError, binascii.Error) as exc:
                await websocket.send_json({"action": "error", "detail": f"Invalid audio chunk: {exc}"})
                continue

            audio_buffer = np.concatenate((audio_buffer, chunk))
            total_frames += len(chunk)
            model = get_model()

            while total_frames >= next_window_end:
                start_frame = next_window_end - window_frames
                start_index = start_frame - buffer_start_frame
                end_index = next_window_end - buffer_start_frame
                waveform = audio_buffer[start_index:end_index]
                score = await asyncio.to_thread(_prediction_score, model, waveform)
                scores.append(score)
                smoothing.append(score)
                smoothed_score = float(np.mean(smoothing))
                await websocket.send_json(
                    {
                        "session_id": session_id,
                        "timestamp_ms": round(next_window_end * 1000 / settings.SAMPLE_RATE),
                        "window_start_ms": round(start_frame * 1000 / settings.SAMPLE_RATE),
                        "window_end_ms": round(next_window_end * 1000 / settings.SAMPLE_RATE),
                        "score": score,
                        "smoothed_score": smoothed_score,
                        "verdict": _verdict(smoothed_score),
                        "buffer_info": {
                            "total_frames_received": total_frames,
                            "windows_processed": len(scores),
                        },
                    }
                )
                next_window_end += hop_frames

            # Retain only enough audio for the next overlapping window.
            if len(audio_buffer) > window_frames:
                discarded = len(audio_buffer) - window_frames
                audio_buffer = audio_buffer[discarded:]
                buffer_start_frame += discarded
    except WebSocketDisconnect:
        return
    finally:
        if session_id and not sent_done:
            # The socket may already be gone; no final payload can be delivered then.
            try:
                await websocket.send_json({"session_id": session_id, "action": "done", "final_summary": _summary(scores)})
            except Exception:
                pass


@router.websocket("/ws/stream")
async def stream_binary_compat(websocket: WebSocket) -> None:
    """Compatibility endpoint for microphone clients sending raw float32 frames."""
    await websocket.accept()
    from app.ml_integration.sliding_window import SlidingWindowInference

    pipeline = SlidingWindowInference(
        get_model(),
        sample_rate=settings.SAMPLE_RATE,
        window_seconds=settings.WINDOW_SIZE_MS / 1000,
        hop_seconds=settings.HOP_SIZE_MS / 1000,
        smoothing_window=settings.SCORE_SMOOTHING_WINDOWS,
    )
    try:
        while True:
            raw = await websocket.receive_bytes()
            usable = len(raw) - (len(raw) % 4)
            if usable <= 0:
                continue
            for score in pipeline.add_chunk(np.frombuffer(raw[:usable], dtype="<f4")):
                await websocket.send_json({
                    "score": float(score),
                    "smoothed_score": float(score),
                    "spoof_score": float(1.0 - score),
                    "verdict": _verdict(float(score)),
                })
    except WebSocketDisconnect:
        pass
    finally:
        pipeline.reset()
