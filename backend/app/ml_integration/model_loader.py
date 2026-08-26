from pathlib import Path
from app.core.config import settings

_model = None

class DummyModel:
    def predict(self, waveform):
        return 0.92

def get_model():
    global _model
    if _model is None:
        model_path = Path(settings.MODEL_PATH)
        if model_path.exists():
            # TODO: load torch model
            _model = DummyModel()
        else:
            _model = DummyModel()
    return _model

def load_model(path: str | None = None):
    return get_model()
