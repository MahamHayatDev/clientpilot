import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.dashboard_routes import latest_by_company
from app.db import supabase

router = APIRouter()


@router.get("/outbox")
def outbox():
    """Approved drafts that have not been delivered to the user yet."""
    latest = latest_by_company("drafts", "*")
    ready = [
        d
        for d in latest.values()
        if d.get("approval_status") == "approved" and not d.get("logged_at")
    ]
    if not ready:
        return []

    companies = {
        c["id"]: c
        for c in (
            supabase.table("companies").select("id,name,website").limit(1000).execute().data
            or []
        )
    }

    items = []
    for d in sorted(ready, key=lambda x: x.get("created_at") or ""):
        company = companies.get(d["company_id"], {})
        items.append(
            {
                "id": d["id"],
                "company_name": company.get("name", "Unknown"),
                "company_website": company.get("website") or "",
                "subject": d.get("subject") or "",
                "body": d.get("body") or "",
            }
        )
    return items


@router.post("/outbox/{draft_id}/logged")
def mark_logged(draft_id: str):
    try:
        uuid.UUID(draft_id)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid draft id: {draft_id!r}")

    try:
        res = supabase.table("drafts").select("*").eq("id", draft_id).limit(1).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)[:200]}")

    if not res.data:
        raise HTTPException(status_code=404, detail="Draft not found")

    draft = res.data[0]
    if draft.get("approval_status") != "approved":
        raise HTTPException(status_code=409, detail="Only approved drafts can be logged")

    if draft.get("logged_at"):
        return {"id": draft_id, "logged": True, "already": True}

    supabase.table("drafts").update(
        {"logged_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", draft_id).execute()
    return {"id": draft_id, "logged": True, "already": False}