"""Explicit public payloads for voice verification and streaming inference."""

from typing import Literal

from pydantic import BaseModel, Field


class FinalSummary(BaseModel):
    total_windows: int
    avg_score: float = Field(description="Average spoof probability, from 0 to 1.")
    confidence: float
    high_risk_windows: int
    verdict: Literal["real", "fake"]


class VerifyVoiceResponse(BaseModel):
    filename: str
    score: float = Field(description="Spoof probability, from 0 to 1.")
    confidence: float
    verdict: Literal["real", "fake"]
    model_name: str
    window_size_ms: int
    hop_size_ms: int


class StreamStarted(BaseModel):
    session_id: str
    action: Literal["started"] = "started"


class StreamScoreEvent(BaseModel):
    session_id: str
    action: Literal["score"] = "score"
    timestamp_ms: int
    window_start_ms: int
    window_end_ms: int
    score: float = Field(description="Window spoof probability, from 0 to 1.")
    smoothed_score: float
    confidence: float
    verdict: Literal["real", "fake"]


class StreamDone(BaseModel):
    session_id: str
    action: Literal["done"] = "done"
    final_summary: FinalSummary
