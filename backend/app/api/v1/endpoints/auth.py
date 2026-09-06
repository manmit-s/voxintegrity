from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db.supabase import supabase

router = APIRouter()


class AuthRequest(BaseModel):
    email: str
    password: str


def _auth_response(response):
    session = response.session
    user = response.user
    return {
        "access_token": session.access_token if session else None,
        "refresh_token": session.refresh_token if session else None,
        "token_type": "bearer",
        "user": (
            user.model_dump()
            if hasattr(user, "model_dump")
            else user.dict()
            if hasattr(user, "dict")
            else user
        ),
    }

@router.post("/register")
def register(payload: AuthRequest):
    if supabase is None:
        raise HTTPException(status_code=503, detail="Supabase is not configured.")
    try:
        response = supabase.auth.sign_up({"email": payload.email, "password": payload.password})
        return _auth_response(response)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.post("/login")
def login(payload: AuthRequest):
    if supabase is None:
        raise HTTPException(status_code=503, detail="Supabase is not configured.")
    try:
        response = supabase.auth.sign_in_with_password(
            {"email": payload.email, "password": payload.password}
        )
        return _auth_response(response)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid email or password.") from exc

