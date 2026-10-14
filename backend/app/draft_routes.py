from fastapi import APIRouter, HTTPException

from app.agents.drafting import run_drafting
from app.db import supabase

router = APIRouter()


def set_status(company_id: str, status: str) -> None:
    supabase.table("companies").update(
        {"status": status}
    ).eq("id", company_id).execute()


@router.post("/draft/{company_id}")
def draft_company(company_id: str):
    # 1. Load the company
    try:
        res = (
            supabase.table("companies")
            .select("*")
            .eq("id", company_id)
            .limit(1)
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=422,
            detail="Invalid company id",
        )

    if not res.data:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    company = res.data[0]

    # 2. Only scored or already drafted companies can be drafted
    if company.get("status") not in ("scored", "drafted"):
        raise HTTPException(
            status_code=409,
            detail=(
                f"Company status is '{company.get('status')}'. "
                "Only companies with status 'scored' can be drafted."
            ),
        )

    # 3. Load the latest research
    research_res = (
        supabase.table("research")
        .select("*")
        .eq("company_id", company_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    # 4. Load the latest score
    score_res = (
        supabase.table("scores")
        .select("*")
        .eq("company_id", company_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not research_res.data or not score_res.data:
        raise HTTPException(
            status_code=409,
            detail="Research or score is missing. Run those steps first.",
        )

    research = research_res.data[0].get("raw") or {}
    score_reasoning = score_res.data[0].get("reasoning") or ""

    # 5. Generate the email draft
    try:
        subject, body, draft = run_drafting(
            company["name"],
            research,
            score_reasoning,
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Drafting agent error: {e}",
        )

    # 6. Save the draft for human approval
    try:
        supabase.table("drafts").insert(
            {
                "company_id": company_id,
                "subject": subject,
                "body": body,
                "approval_status": "pending",
                "raw": draft.model_dump(),
            }
        ).execute()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not save draft: {e}",
        )

    # 7. Update the company status
    set_status(company_id, "drafted")

    return {
        "company": company["name"],
        "subject": subject,
        "body": body,
        "gap_referenced": draft.gap_referenced,
        "approval_status": "pending",
        "status": "drafted",
    }