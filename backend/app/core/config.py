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
    MODEL_PATH: str = "ml_pipeline/weights/ast_model.onnx"
    MODEL_HF_ID: str = "MattyB95/AST-ASVspoof2019-Synthetic-Voice-Detection"
    # Set this to true for offline deployments that should use an existing HF cache only.
    MODEL_HF_LOCAL_FILES_ONLY: bool = False
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
