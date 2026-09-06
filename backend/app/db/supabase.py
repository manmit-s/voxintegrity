from supabase import create_client, Client
from app.core.config import settings

def get_supabase() -> Client | None:
    service_key = settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_KEY
    if not settings.SUPABASE_URL or not service_key:
        return None
    return create_client(settings.SUPABASE_URL, service_key)

supabase: Client | None = get_supabase()
