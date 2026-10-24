import operator
import time
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.drafting import run_drafting
from app.agents.research import run_research
from app.agents.scoring import run_scoring
from app.db import supabase
from app.scoring_routes import SCORE_THRESHOLD
from app.tools.scraper import scrape_website


# ---------- State ----------
class PipelineState(TypedDict, total=False):
    company_id: str
    force: bool
    company: dict
    research: dict
    score: int
    score_reasoning: str
    decision: str
    subject: str
    body: str
    error: str
    log: Annotated[list[str], operator.add]


# ---------- Helpers ----------
def set_status(company_id: str, status: str) -> None:
    supabase.table("companies").update(
        {"status": status}
    ).eq("id", company_id).execute()


def latest_row(table: str, company_id: str):
    res = (
        supabase.table(table)
        .select("*")
        .eq("company_id", company_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def with_retry(fn, *args, attempts: int = 2, delay: float = 3.0):
    """Retry temporary failures with exponentially increasing waits."""
    last_error = None

    for i in range(attempts):
        try:
            return fn(*args)
        except ValueError:
            # Validation errors are not transient API failures.
            raise
        except Exception as e:
            last_error = e

            if i < attempts - 1:
                time.sleep(delay * (2**i))

    raise last_error


def short(e: Exception) -> str:
    return str(e)[:200]


# ---------- Nodes ----------
def load_node(state: PipelineState) -> dict:
    cid = state["company_id"]

    try:
        res = (
            supabase.table("companies")
            .select("*")
            .eq("id", cid)
            .limit(1)
            .execute()
        )
    except Exception:
        return {
            "error": "Invalid company id",
            "log": ["load: invalid company id"],
        }

    if not res.data:
        return {
            "error": "Company not found",
            "log": ["load: company not found"],
        }

    company = res.data[0]
    status = company.get("status") or "new"

    update: dict = {
        "company": company,
        "log": [f"load: {company['name']} has status '{status}'"],
    }

    research_row = latest_row("research", cid)
    if research_row:
        update["research"] = research_row.get("raw") or {}

    score_row = latest_row("scores", cid)
    if score_row:
        update["score_reasoning"] = score_row.get("reasoning") or ""
        update["score"] = score_row.get("fit_score")

    if status in ("drafted", "skipped") and not state.get("force"):
        update["log"].append(
            f"load: nothing to do, status is '{status}'. "
            "Use force=true to run again."
        )

    return update


def research_node(state: PipelineState) -> dict:
    company = state["company"]
    cid = company["id"]
    website = (company.get("website") or "").strip()

    if not website:
        set_status(cid, "failed")
        return {
            "error": "Company has no website",
            "log": ["research: no website"],
        }

    url = (
        website
        if website.startswith(("http://", "https://"))
        else "https://" + website
    )

    # Website fetching keeps its short retry delay.
    try:
        text = with_retry(
            scrape_website,
            url,
            attempts=2,
            delay=2,
        )
    except Exception as e:
        set_status(cid, "failed")
        return {
            "error": f"Could not read website: {short(e)}",
            "log": ["research: website could not be read"],
        }

    # Research LLM: up to 3 attempts, with 10s then 20s waits.
    try:
        result = with_retry(
            run_research,
            company["name"],
            text,
            attempts=3,
            delay=10,
        )
    except Exception as e:
        set_status(cid, "failed")
        return {
            "error": f"Research agent error: {short(e)}",
            "log": ["research: agent failed"],
        }

    try:
        supabase.table("research").insert(
            {
                "company_id": cid,
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
        return {
            "error": f"Could not save research: {short(e)}",
            "log": ["research: save failed"],
        }

    set_status(cid, "researched")

    return {
        "research": result.model_dump(),
        "log": [
            f"research: done (confidence {result.confidence})"
        ],
    }


def score_node(state: PipelineState) -> dict:
    company = state["company"]
    cid = company["id"]
    research = state.get("research") or {}

    if research.get("confidence") == "low":
        reasoning = (
            "Research confidence was low, so this lead was skipped."
        )

        try:
            supabase.table("scores").insert(
                {
                    "company_id": cid,
                    "fit_score": 0,
                    "reasoning": reasoning,
                }
            ).execute()
        except Exception as e:
            return {
                "error": f"Could not save score: {short(e)}",
                "log": ["score: save failed"],
            }

        set_status(cid, "skipped")

        return {
            "score": 0,
            "decision": "skip",
            "score_reasoning": reasoning,
            "log": ["score: skipped (low research confidence)"],
        }
    # Scoring LLM: up to 3 attempts, with 10s then 20s waits.
    try:
        result = with_retry(
            run_scoring,
            company["name"],
            research,
            attempts=3,
            delay=10,
        )
    except Exception as e:
        return {
            "error": f"Scoring agent error: {short(e)}",
            "log": ["score: agent failed"],
        }

    score = max(0, min(100, int(result.fit_score)))
    decision = "contact" if score >= SCORE_THRESHOLD else "skip"

    try:
        supabase.table("scores").insert(
            {
                "company_id": cid,
                "fit_score": score,
                "reasoning": result.reasoning,
                "raw": result.model_dump(),
            }
        ).execute()
    except Exception as e:
        return {
            "error": f"Could not save score: {short(e)}",
            "log": ["score: save failed"],
        }

    set_status(
        cid,
        "scored" if decision == "contact" else "skipped",
    )

    return {
        "score": score,
        "decision": decision,
        "score_reasoning": result.reasoning,
        "log": [
            f"score: {score}/100, decision '{decision}'"
        ],
    }


def draft_node(state: PipelineState) -> dict:
    company = state["company"]
    cid = company["id"]

    # Draft-generation LLM: up to 3 attempts, with 10s then 20s waits.
    try:
        subject, body, draft = with_retry(
            run_drafting,
            company["name"],
            state.get("research") or {},
            state.get("score_reasoning") or "",
            attempts=3,
            delay=10,
        )
    except Exception as e:
        return {
            "error": f"Drafting agent error: {short(e)}",
            "log": ["draft: agent failed"],
        }

    try:
        supabase.table("drafts").insert(
            {
                "company_id": cid,
                "subject": subject,
                "body": body,
                "approval_status": "pending",
                "raw": draft.model_dump(),
            }
        ).execute()
    except Exception as e:
        return {
            "error": f"Could not save draft: {short(e)}",
            "log": ["draft: save failed"],
        }

    set_status(cid, "drafted")

    return {
        "subject": subject,
        "body": body,
        "log": ["draft: saved as pending"],
    }


# ---------- Routing ----------
def route_after_load(state: PipelineState) -> str:
    if state.get("error"):
        return END

    if state.get("force"):
        return "research_node"

    status = state["company"].get("status") or "new"

    if status in ("new", "failed"):
        return "research_node"

    if status == "researched":
        return (
            "score_node"
            if state.get("research")
            else "research_node"
        )

    if status == "scored":
        if state.get("research") and "score_reasoning" in state:
            return "draft_node"

        if state.get("research"):
            return "score_node"

        return "research_node"

    return END


def route_after_research(state: PipelineState) -> str:
    return END if state.get("error") else "score_node"


def route_after_score(state: PipelineState) -> str:
    if state.get("error"):
        return END

    return (
        "draft_node"
        if state.get("decision") == "contact"
        else END
    )


# ---------- Build the graph ----------
builder = StateGraph(PipelineState)

builder.add_node("load_node", load_node)
builder.add_node("research_node", research_node)
builder.add_node("score_node", score_node)
builder.add_node("draft_node", draft_node)

builder.add_edge(START, "load_node")

builder.add_conditional_edges(
    "load_node",
    route_after_load,
    {
        "research_node": "research_node",
        "score_node": "score_node",
        "draft_node": "draft_node",
        END: END,
    },
)

builder.add_conditional_edges(
    "research_node",
    route_after_research,
    {
        "score_node": "score_node",
        END: END,
    },
)

builder.add_conditional_edges(
    "score_node",
    route_after_score,
    {
        "draft_node": "draft_node",
        END: END,
    },
)

builder.add_edge("draft_node", END)

graph = builder.compile()


# ---------- Public function ----------
def run_pipeline(company_id: str, force: bool = False) -> dict:
    final = graph.invoke(
        {
            "company_id": company_id,
            "force": force,
            "log": [],
        }
    )

    company = final.get("company") or {}
    final_status = None

    if company:
        res = (
            supabase.table("companies")
            .select("status")
            .eq("id", company_id)
            .limit(1)
            .execute()
        )
        final_status = (
            res.data[0]["status"] if res.data else None
        )

    return {
        "company": company.get("name"),
        "final_status": final_status,
        "score": final.get("score"),
        "decision": final.get("decision"),
        "subject": final.get("subject"),
        "error": final.get("error"),
        "log": final.get("log", []),
    }