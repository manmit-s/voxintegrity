from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Vaani Kavach"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "change-me-in-production"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    MODEL_PATH: str = "ml_pipeline/weights/ast_model.onnx"

    class Config:
        env_file = ".env"

settings = Settings()
