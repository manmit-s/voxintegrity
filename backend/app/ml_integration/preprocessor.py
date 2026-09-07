import io

import librosa
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from fastapi import UploadFile

from app.core.config import settings

TARGET_SR = 16000

async def preprocess_audio(file: UploadFile) -> np.ndarray:
    """Decode an uploaded recording into the mono 16 kHz AST waveform format."""
    content = await file.read()
    if not content:
        raise ValueError("Audio upload is empty.")
    try:
        decoded, sample_rate = sf.read(io.BytesIO(content), dtype="float32", always_2d=True)
        waveform = decoded.mean(axis=1)
        if sample_rate != settings.SAMPLE_RATE:
            divisor = np.gcd(sample_rate, settings.SAMPLE_RATE)
            waveform = resample_poly(waveform, settings.SAMPLE_RATE // divisor, sample_rate // divisor)
    except RuntimeError:
        # Keep a decoder fallback for browser-produced MP3/M4A containers not supported by libsndfile.
        waveform, _ = librosa.load(io.BytesIO(content), sr=settings.SAMPLE_RATE, mono=True, dtype=np.float32)
    waveform = np.asarray(waveform, dtype=np.float32).reshape(-1)
    if not waveform.size:
        raise ValueError("Audio upload contains no decodable samples.")
    # This protects against the former stub regression for real, non-silent recordings.
    if not np.any(np.abs(waveform) > 1e-7):
        raise ValueError("Audio upload decoded to silence; choose a recording with speech.")
    return waveform

def extract_mfcc(waveform: np.ndarray, sr: int = TARGET_SR, n_mfcc: int = 40):
    return librosa.feature.mfcc(y=waveform, sr=sr, n_mfcc=n_mfcc)
