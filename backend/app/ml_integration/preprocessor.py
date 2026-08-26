import io
import librosa
import numpy as np
from fastapi import UploadFile

TARGET_SR = 16000
MAX_DURATION = 10.0

async def preprocess_audio(file: UploadFile) -> np.ndarray:
    content = await file.read()
    # Load with librosa - placeholder for now
    # y, sr = librosa.load(io.BytesIO(content), sr=TARGET_SR, duration=MAX_DURATION)
    # For prototype, return dummy waveform
    y = np.zeros(int(TARGET_SR * 2), dtype=np.float32)
    return y

def extract_mfcc(waveform: np.ndarray, sr: int = TARGET_SR, n_mfcc: int = 40):
    return librosa.feature.mfcc(y=waveform, sr=sr, n_mfcc=n_mfcc)
