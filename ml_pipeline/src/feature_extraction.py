import librosa
import numpy as np

def extract_features(waveform, sr=16000, n_mfcc=40, n_fft=2048):
    mfcc = librosa.feature.mfcc(y=waveform, sr=sr, n_mfcc=n_mfcc, n_fft=n_fft)
    delta = librosa.feature.delta(mfcc)
    delta2 = librosa.feature.delta(mfcc, order=2)
    features = np.concatenate([mfcc, delta, delta2], axis=0)
    return features

def normalize(features):
    return (features - features.mean()) / (features.std() + 1e-8)
