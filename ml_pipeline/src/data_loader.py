import librosa
from pathlib import Path
from torch.utils.data import Dataset

class VoiceDataset(Dataset):
    def __init__(self, data_dir, sr=16000, duration=4.0):
        self.files = list(Path(data_dir).rglob('*.wav'))
        self.sr = sr
        self.duration = duration

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        path = self.files[idx]
        y, _ = librosa.load(path, sr=self.sr, duration=self.duration)
        label = 0 if 'real' in str(path) else 1
        return y, label
