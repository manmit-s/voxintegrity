from fastapi import APIRouter
from app.api.v1.endpoints import auth, inference, history

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(inference.router, prefix="/voice", tags=["voice"])
api_router.include_router(history.router, prefix="/history", tags=["history"])
