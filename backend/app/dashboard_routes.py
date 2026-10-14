from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid

from app.db import supabase

router = APIRouter()

WAITING = ("pending", "edited")


# ---------- Helpers ----------
def latest_by_company(table: str, columns: str) -> dict:
    """Newest row per company_id. `columns` must include company_id and created_at."""
    rows = (
        supabase.table(table)
        .select(columns)
        .order("created_at", desc=True)
        .limit(1000)
        .execute()
        .data
        or []
    )
    out: dict = {}
    for row in rows:
        out.setdefault(row["company_id"], row)
    return out


def clean_site(url: str) -> str:
    u = url.strip().lower()
    for prefix in ("https://", "http://", "www."):
        if u.startswith(prefix):
            u = u[len(prefix):]
    return u.rstrip("/")


def get_draft_or_404(draft_id: str) -> dict:
    try:
        res = supabase.table("drafts").select("*").eq("id", draft_id).limit(1).execute()
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid draft id")
    if not res.data:
        raise HTTPException(status_code=404, detail="Draft not found")
    return res.data[0]


def set_company_status(company_id: str, status: str) -> None:
    supabase.table("companies").update({"status": status}).eq("id", company_id).execute()


# ---------- Request models ----------
class CompanyIn(BaseModel):
    name: str
    website: str


class BulkIn(BaseModel):
    companies: list[CompanyIn]


class DraftEdit(BaseModel):
    subject: str
    body: str


# ---------- Companies ----------
@router.get("/companies")
def list_companies():
    companies = (
        supabase.table("companies")
        .select("*")
        .order("created_at", desc=True)
        .limit(1000)
        .execute()
        .data
        or []
    )
    scores = latest_by_company("scores", "company_id,fit_score,created_at")
    return [
        {
            "id": c["id"],
            "name": c["name"],
            "website": c.get("website"),
            "status": c.get("status") or "new",
            "created_at": c.get("created_at"),
            "fit_score": scores.get(c["id"], {}).get("fit_score"),
        }
        for c in companies
    ]


@router.post("/companies/bulk")
def add_companies(payload: BulkIn):
    if len(payload.companies) > 200:
        raise HTTPException(status_code=400, detail="Maximum 200 companies per upload")

    existing = supabase.table("companies").select("website").limit(1000).execute().data or []
    seen = {clean_site(c.get("website") or "") for c in existing}

    to_insert = []
    skipped = 0
    for c in payload.companies:
        name = c.name.strip()
        site = c.website.strip()
        key = clean_site(site)
        if not name or not key or key in seen:
            skipped += 1
            continue
        seen.add(key)
        to_insert.append({"name": name[:200], "website": site})

    if to_insert:
        try:
            supabase.table("companies").insert(to_insert).execute()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not save companies: {str(e)[:200]}")

    return {"added": len(to_insert), "skipped": skipped}


@router.get("/companies/{company_id}")
def company_detail(company_id: str):
    # Validate the ID and show the actual value if it is malformed.
    try:
        uuid.UUID(company_id)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid company id: {company_id!r}",
        )

    # Report database errors separately instead of treating every error as an invalid ID.
    try:
        res = (
            supabase.table("companies")
            .select("*")
            .eq("id", company_id)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)[:200]}",
        )

    if not res.data:
        raise HTTPException(status_code=404, detail="Company not found")

    def newest(table: str):
        r = (
            supabase.table(table)
            .select("*")
            .eq("company_id", company_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return r.data[0] if r.data else None

    return {
        "company": res.data[0],
        "research": newest("research"),
        "score": newest("scores"),
        "draft": newest("drafts"),
    }


# ---------- Drafts (approval queue) ----------
@router.get("/drafts")
def list_drafts(view: str = "waiting"):
    if view not in ("waiting", "approved", "rejected"):
        raise HTTPException(status_code=422, detail="view must be waiting, approved or rejected")

    latest = latest_by_company("drafts", "*")
    companies = {
        c["id"]: c
        for c in (
            supabase.table("companies")
            .select("id,name,website")
            .limit(1000)
            .execute()
            .data
            or []
        )
    }
    scores = latest_by_company("scores", "company_id,fit_score,reasoning,created_at")

    def keep(d: dict) -> bool:
        s = d.get("approval_status")
        if view == "waiting":
            return s in WAITING
        return s == view

    items = []
    for d in latest.values():
        if not keep(d):
            continue
        company = companies.get(d["company_id"], {})
        score = scores.get(d["company_id"], {})
        items.append(
            {
                "id": d["id"],
                "company_id": d["company_id"],
                "company_name": company.get("name", "Unknown"),
                "company_website": company.get("website"),
                "fit_score": score.get("fit_score"),
                "score_reasoning": score.get("reasoning"),
                "subject": d.get("subject") or "",
                "body": d.get("body") or "",
                "approval_status": d.get("approval_status"),
                "created_at": d.get("created_at"),
            }
        )
    items.sort(key=lambda x: x["created_at"] or "", reverse=True)
    return items


@router.patch("/drafts/{draft_id}")
def edit_draft(draft_id: str, payload: DraftEdit):
    draft = get_draft_or_404(draft_id)
    if draft.get("approval_status") not in WAITING:
        raise HTTPException(status_code=409, detail="Only waiting drafts can be edited")

    subject = payload.subject.strip()
    body = payload.body.strip()
    if not subject or not body:
        raise HTTPException(status_code=422, detail="Subject and body cannot be empty")

    supabase.table("drafts").update(
        {"subject": subject, "body": body, "approval_status": "edited"}
    ).eq("id", draft_id).execute()
    return {"id": draft_id, "approval_status": "edited"}


@router.post("/drafts/{draft_id}/approve")
def approve_draft(draft_id: str):
    draft = get_draft_or_404(draft_id)
    if draft.get("approval_status") not in WAITING:
        raise HTTPException(status_code=409, detail="Draft is not waiting for approval")
    supabase.table("drafts").update({"approval_status": "approved"}).eq("id", draft_id).execute()
    set_company_status(draft["company_id"], "approved")
    return {"id": draft_id, "approval_status": "approved"}


@router.post("/drafts/{draft_id}/reject")
def reject_draft(draft_id: str):
    draft = get_draft_or_404(draft_id)
    if draft.get("approval_status") not in WAITING:
        raise HTTPException(status_code=409, detail="Draft is not waiting for approval")
    supabase.table("drafts").update({"approval_status": "rejected"}).eq("id", draft_id).execute()
    set_company_status(draft["company_id"], "rejected")
    return {"id": draft_id, "approval_status": "rejected"}


# ---------- Analytics ----------
@router.get("/stats")
def stats():
    companies = supabase.table("companies").select("status").limit(1000).execute().data or []
    by_status: dict[str, int] = {}
    for c in companies:
        s = c.get("status") or "new"
        by_status[s] = by_status.get(s, 0) + 1

    scores = latest_by_company("scores", "company_id,fit_score,created_at")
    values = [s["fit_score"] for s in scores.values() if s.get("fit_score") is not None]
    avg_score = round(sum(values) / len(values), 1) if values else None

    drafts = latest_by_company("drafts", "*")
    waiting = sum(1 for d in drafts.values() if d.get("approval_status") in WAITING)
    approved = sum(1 for d in drafts.values() if d.get("approval_status") == "approved")
    rejected = sum(1 for d in drafts.values() if d.get("approval_status") == "rejected")
    decided = approved + rejected

    return {
        "total": len(companies),
        "by_status": by_status,
        "avg_score": avg_score,
        "waiting": waiting,
        "approved": approved,
        "rejected": rejected,
        "approval_rate": round(approved / decided * 100) if decided else None,
    }