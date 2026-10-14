from fastapi import APIRouter, HTTPException

from app.agents.scoring import run_scoring
from app.db import supabase

router = APIRouter()

SCORE_THRESHOLD = 50  # Companies scoring below this are skipped


def set_status(company_id: str, status: str) -> None:
    supabase.table("companies").update(
        {"status": status}
    ).eq("id", company_id).execute()


@router.post("/score/{company_id}")
def score_company(company_id: str):
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
        raise HTTPException(status_code=422, detail="Invalid company id")

    if not res.data:
        raise HTTPException(status_code=404, detail="Company not found")

    company = res.data[0]

    # 2. Load the company's most recent research
    research_res = (
        supabase.table("research")
        .select("*")
        .eq("company_id", company_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not research_res.data:
        raise HTTPException(
            status_code=409,
            detail="No research found. Run /research/{company_id} first.",
        )

    research = research_res.data[0].get("raw") or {}

    # 3. Skip thin research without spending another API call
    if research.get("confidence") == "low":
        supabase.table("scores").insert(
            {
                "company_id": company_id,
                "fit_score": 0,
                "reasoning": "Research confidence was low, so this lead was skipped.",
            }
        ).execute()

        set_status(company_id, "skipped")

        return {
            "company": company["name"],
            "fit_score": 0,
            "decision": "skip",
            "reasoning": "Research confidence was low.",
            "status": "skipped",
        }

    # 4. Run the scoring agent
    try:
        result = run_scoring(company["name"], research)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Scoring agent error: {e}",
        )

    score = max(0, min(100, int(result.fit_score)))
    decision = "contact" if score >= SCORE_THRESHOLD else "skip"
    status = "scored" if decision == "contact" else "skipped"

    # 5. Save the score
    try:
        supabase.table("scores").insert(
            {
                "company_id": company_id,
                "fit_score": score,
                "reasoning": result.reasoning,
                "raw": result.model_dump(),
            }
        ).execute()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not save score: {e}",
        )

    set_status(company_id, status)

    return {
        "company": company["name"],
        "fit_score": score,
        "decision": decision,
        "reasoning": result.reasoning,
        "matched_services": result.matched_services,
        "status": status,
    }