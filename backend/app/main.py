import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agents.research import run_research
from app.db import supabase
from app.scoring_routes import router as scoring_router
from app.draft_routes import router as draft_router
from app.pipeline_routes import router as pipeline_router
from app.dashboard_routes import router as dashboard_router
from app.automation_routes import router as automation_router
from app.health_routes import router as health_router
from app.tools.scraper import scrape_website


# Configure application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


app = FastAPI(title="ClientPilot API")


# Allow the Next.js dashboard to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register application routes
app.include_router(scoring_router)
app.include_router(draft_router)
app.include_router(pipeline_router)
app.include_router(dashboard_router)
app.include_router(automation_router)
app.include_router(health_router)


def set_status(company_id: str, status: str) -> None:
    supabase.table("companies").update(
        {"status": status}
    ).eq("id", company_id).execute()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/research/{company_id}")
def research_company(company_id: str):
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
        logger.exception("Failed to load company: %s", company_id)
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
    website = (company.get("website") or "").strip()

    if not website:
        raise HTTPException(
            status_code=422,
            detail="Company has no website",
        )

    url = (
        website
        if website.startswith(("http://", "https://"))
        else "https://" + website
    )

    # 2. Scrape the website
    try:
        text = scrape_website(url)
    except Exception as e:
        logger.exception(
            "Website scraping failed for company %s",
            company_id,
        )
        set_status(company["id"], "failed")
        raise HTTPException(
            status_code=422,
            detail=f"Could not read website: {e}",
        )

    # 3. Run the Research Agent
    try:
        result = run_research(company["name"], text)
    except Exception as e:
        logger.exception(
            "Research agent failed for company %s",
            company_id,
        )
        set_status(company["id"], "failed")
        raise HTTPException(
            status_code=502,
            detail=f"Research agent error: {e}",
        )

    # 4. Save the research results
    try:
        supabase.table("research").insert(
            {
                "company_id": company["id"],
                "summary": (
                    f"{result.what_they_do} "
                    f"Audience: {result.audience}"
                ),
                "gaps": "\n".join(
                    f"- {gap}" for gap in result.gaps
                ),
                "raw": result.model_dump(),
            }
        ).execute()
    except Exception as e:
        logger.exception(
            "Failed to save research for company %s",
            company_id,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Could not save research: {e}",
        )

    # 5. Update the company status
    try:
        set_status(company["id"], "researched")
    except Exception:
        logger.exception(
            "Failed to update company status: %s",
            company_id,
        )
        raise HTTPException(
            status_code=500,
            detail="Research was saved, but company status could not be updated.",
        )

    logger.info(
        "Research completed successfully for company %s",
        company_id,
    )

    return {
        "company": company["name"],
        "research": result.model_dump(),
    }