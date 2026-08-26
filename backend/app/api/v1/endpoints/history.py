from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_history(user_id: str | None = None):
    # Placeholder - fetch from Supabase
    return {"history": [], "count": 0}

@router.get("/{record_id}")
def get_record(record_id: str):
    return {"record_id": record_id, "status": "not-found"}
