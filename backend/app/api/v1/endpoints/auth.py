from fastapi import APIRouter, HTTPException, Depends
from app.core.security import create_access_token, verify_password, get_password_hash

router = APIRouter()

@router.post("/register")
def register(email: str, password: str):
    # Placeholder - integrate with Supabase Auth
    hashed = get_password_hash(password)
    return {"email": email, "status": "registered"}

@router.post("/login")
def login(email: str, password: str):
    token = create_access_token({"sub": email})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me")
def me():
    return {"user": "vaani-kavach-user", "authenticated": False}
