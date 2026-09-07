from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Runtime configuration for the API and its inference pipeline."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Vaani Kavach"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "change-me-in-production"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    # Resolve this relative to the repository root when no absolute path is supplied.
    # This ONNX graph uses the sibling ast_finetuned_fp32.onnx.data file for weights.
    MODEL_PATH: str = "ml_pipeline/weights/ast_finetuned_fp32.onnx"
    # DirectML adapter ordinal. Set DML_DEVICE_ID in .env if the RTX is not adapter 0.
    DML_DEVICE_ID: int = 0
    WINDOW_SIZE_MS: int = 2000
    HOP_SIZE_MS: int = 500
    SCORE_SMOOTHING_WINDOWS: int = 3
    SAMPLE_RATE: int = 16000
    VERDICT_THRESHOLD: float = 0.5
    MODEL_REAL_CLASS_INDEX: int = 0
    SUPABASE_SERVICE_KEY: str = ""

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    def resolved_model_path(self) -> Path:
        path = Path(self.MODEL_PATH).expanduser()
        return path if path.is_absolute() else self.project_root / path

settings = Settings()
