"""Public REST and WebSocket endpoints for voice-spoof inference."""

from __future__ import annotations

import asyncio
import base64
import binascii
from collections import deque
from typing import Any

import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.core.security import get_current_user
from app.db.supabase import supabase
from app.ml_integration.preprocessor import preprocess_audio
from app.ml_integration.model_loader import get_model, get_model_name
from app.schemas.inference import FinalSummary, StreamDone, StreamScoreEvent, StreamStarted, VerifyVoiceResponse

router = APIRouter()


def _save_session(user_id: str, summary: dict[str, Any], scores: list[float], duration_seconds: float | None = None):
    if supabase is None:
        return
    session = (
        supabase.table("verification_sessions")
        .insert({
            "user_id": user_id,
            "call_duration": duration_seconds,
            "spoof_score": summary["avg_score"],
            "percent_high_risk": (summary["high_risk_windows"] / len(scores) * 100) if scores else 0,
            "verdict": summary["verdict"],
        })
        .execute()
    )
    if session.data and scores:
        session_id = session.data[0]["id"]
        supabase.table("score_events").insert([
            {
                "call_verification_id": session_id,
                "timestamp_offset": index,
                "spoof_score": score,
            }
            for index, score in enumerate(scores)
        ]).execute()


def _prediction_score(model: Any, waveform: np.ndarray) -> float:
    """Run the ONNX adapter and return a spoof probability."""
    if not waveform.size:
        raise ValueError("Audio contains no samples.")

    waveform = np.nan_to_num(waveform.astype(np.float32, copy=False))
    if not hasattr(model, "predict"):
        raise TypeError("Configured inference model does not provide predict().")
    result = model.predict(waveform)
    if isinstance(result, dict):
        result = result.get("score", result.get("bonafide_score"))
    # The deployed AST adapter returns class-0 (bonafide) probability. Public API scores
    # are deliberately spoof probabilities so the chart and summary use one clear meaning.
    score = 1.0 - float(result)
    if not np.isfinite(score):
        raise ValueError("Model returned a non-finite score.")
    return float(np.clip(score, 0.0, 1.0))


def _verdict(score: float) -> str:
    return "fake" if score >= settings.VERDICT_THRESHOLD else "real"


@router.post("/verify", response_model=VerifyVoiceResponse)
async def verify_voice(file: UploadFile = File(...), user=Depends(get_current_user)):
    if not file.filename:
        raise HTTPException(status_code=422, detail="An audio file is required.")
    try:
        waveform = await preprocess_audio(file)
        model = get_model()
        score = await asyncio.to_thread(_prediction_score, model, waveform)
        result = {
            "filename": file.filename,
            "score": score,
            "verdict": _verdict(score),
            "confidence": max(score, 1.0 - score),
            "model_name": get_model_name(),
            "window_size_ms": settings.WINDOW_SIZE_MS,
            "hop_size_ms": settings.HOP_SIZE_MS,
        }
        _save_session(str(user.id), _summary([score]), [score])
        return result
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _summary(scores: list[float]) -> dict[str, Any]:
    average = float(np.mean(scores)) if scores else 0.5
    return {
        "total_windows": len(scores),
        "avg_score": average,
        "confidence": max(average, 1.0 - average),
        "high_risk_windows": sum(score >= settings.VERDICT_THRESHOLD for score in scores),
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
                await websocket.send_json(StreamStarted(session_id=session_id).model_dump())
                continue

            if action == "stop":
                if session_id and message.get("session_id") not in (None, session_id):
                    await websocket.send_json({"action": "error", "detail": "session_id does not match."})
                    continue
                await websocket.send_json(StreamDone(session_id=session_id, final_summary=FinalSummary(**_summary(scores))).model_dump())
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
                await websocket.send_json(StreamScoreEvent(
                    session_id=session_id,
                    timestamp_ms=round(next_window_end * 1000 / settings.SAMPLE_RATE),
                    window_start_ms=round(start_frame * 1000 / settings.SAMPLE_RATE),
                    window_end_ms=round(next_window_end * 1000 / settings.SAMPLE_RATE),
                    score=score,
                    smoothed_score=smoothed_score,
                    confidence=max(smoothed_score, 1.0 - smoothed_score),
                    verdict=_verdict(smoothed_score),
                ).model_dump())
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
                await websocket.send_json(StreamDone(session_id=session_id, final_summary=FinalSummary(**_summary(scores))).model_dump())
            except Exception:
                pass
