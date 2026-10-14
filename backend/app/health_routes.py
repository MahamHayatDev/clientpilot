from fastapi import APIRouter, HTTPException

from app.config import MODEL_NAME
from app.db import supabase

router = APIRouter()


@router.get("/health/deep")
def health_deep():
    checks = {"model": MODEL_NAME}
    try:
        supabase.table("companies").select("id").limit(1).execute()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)[:100]}"
        raise HTTPException(status_code=503, detail=checks)
    return {"status": "ok", **checks}