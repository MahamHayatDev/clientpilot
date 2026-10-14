import logging
import threading
import time

from fastapi import APIRouter, HTTPException, Query

from app.db import supabase
from app.pipeline import run_pipeline

router = APIRouter()
log = logging.getLogger("clientpilot")

BATCH_DELAY_SECONDS = 4  # pause between companies to respect free-tier limits

_lock = threading.Lock()
_running: set[str] = set()
_state = {"batch": False}


def _claim(company_id: str) -> bool:
    with _lock:
        if company_id in _running:
            return False
        _running.add(company_id)
        return True


def _release(company_id: str) -> None:
    with _lock:
        _running.discard(company_id)


@router.post("/pipeline/{company_id}")
def pipeline_one(company_id: str, force: bool = False):
    if not _claim(company_id):
        raise HTTPException(status_code=409, detail="This company is already being processed")

    started = time.time()
    try:
        result = run_pipeline(company_id, force=force)
    except Exception as e:
        log.exception("pipeline crashed for %s", company_id)
        raise HTTPException(status_code=500, detail=f"Pipeline crashed: {str(e)[:300]}")
    finally:
        _release(company_id)

    log.info(
        "pipeline %s finished in %.1fs, status=%s, error=%s",
        company_id,
        time.time() - started,
        result.get("final_status"),
        result.get("error"),
    )

    if result["error"] == "Company not found":
        raise HTTPException(status_code=404, detail="Company not found")
    if result["error"] == "Invalid company id":
        raise HTTPException(status_code=422, detail="Invalid company id")
    return result


@router.post("/pipeline-batch")
def pipeline_batch(limit: int = Query(5, ge=1, le=10)):
    with _lock:
        if _state["batch"]:
            raise HTTPException(status_code=409, detail="A batch is already running")
        _state["batch"] = True

    started = time.time()
    results = []
    try:
        res = (
            supabase.table("companies")
            .select("id,name")
            .eq("status", "new")
            .order("created_at")
            .limit(limit)
            .execute()
        )

        for i, company in enumerate(res.data or []):
            if not _claim(company["id"]):
                results.append(
                    {
                        "company": company["name"],
                        "final_status": "new",
                        "score": None,
                        "error": "Already being processed elsewhere",
                    }
                )
                continue

            if i > 0:
                time.sleep(BATCH_DELAY_SECONDS)
            try:
                outcome = run_pipeline(company["id"])
            except Exception as e:
                log.exception("batch item crashed for %s", company["id"])
                outcome = {
                    "company": company["name"],
                    "final_status": "failed",
                    "error": f"Pipeline crashed: {str(e)[:200]}",
                }
            finally:
                _release(company["id"])

            results.append(
                {
                    "company": outcome.get("company") or company["name"],
                    "final_status": outcome.get("final_status"),
                    "score": outcome.get("score"),
                    "error": outcome.get("error"),
                }
            )
    finally:
        with _lock:
            _state["batch"] = False

    log.info("batch finished: %d companies in %.1fs", len(results), time.time() - started)
    return {"processed": len(results), "results": results}