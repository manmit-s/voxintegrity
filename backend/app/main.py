from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings
from app.ml_integration.model_loader import get_model_name

app = FastAPI(title=settings.PROJECT_NAME, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
def warm_inference_model() -> None:
    """Validate the configured ONNX artifact before accepting a capture session."""
    get_model_name()

@app.get("/health")
def health():
    return {"status": "ok", "service": "vaani-kavach-backend"}

@app.get("/")
def root():
    return {"message": "Vaani Kavach API - Voice Protection System"}
