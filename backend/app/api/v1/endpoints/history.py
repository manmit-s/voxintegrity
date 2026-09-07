from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
from app.db.supabase import supabase

router = APIRouter()

@router.get("/")
def get_history(user=Depends(get_current_user)):
    if supabase is None:
        raise HTTPException(status_code=503, detail="Supabase is not configured.")
    try:
        response = (
            supabase.table("verification_sessions")
            .select("*, score_events(*)")
            .eq("user_id", str(user.id))
            .order("created_at", desc=True)
            .execute()
        )
        return {"history": response.data, "count": len(response.data)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to load verification history.") from exc

@router.get("/{record_id}")
def get_record(record_id: str, user=Depends(get_current_user)):
    if supabase is None:
        raise HTTPException(status_code=503, detail="Supabase is not configured.")
    response = (
        supabase.table("verification_sessions")
        .select("*, score_events(*)")
        .eq("id", record_id)
        .eq("user_id", str(user.id))
        .maybe_single()
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Verification record not found.")
    return response.data
