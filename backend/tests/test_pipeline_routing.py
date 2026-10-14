import pytest
from langgraph.graph import END

from app.pipeline import (
    route_after_load,
    route_after_research,
    route_after_score,
    with_retry,
)


def load_state(status, research=None, reasoning=None, **extra):
    state = {"company": {"status": status}, **extra}
    if research is not None:
        state["research"] = research
    if reasoning is not None:
        state["score_reasoning"] = reasoning
    return state


# ----- route_after_load -----
def test_error_ends_the_graph():
    assert route_after_load({"error": "boom"}) == END


def test_force_restarts_from_research():
    assert route_after_load(load_state("drafted", force=True)) == "research_node"


@pytest.mark.parametrize("status", ["new", "failed"])
def test_new_and_failed_start_with_research(status):
    assert route_after_load(load_state(status)) == "research_node"


def test_researched_goes_to_scoring():
    assert route_after_load(load_state("researched", research={"x": 1})) == "score_node"


def test_researched_without_saved_research_redoes_research():
    assert route_after_load(load_state("researched")) == "research_node"


def test_scored_goes_to_drafting():
    state = load_state("scored", research={"x": 1}, reasoning="good fit")
    assert route_after_load(state) == "draft_node"


def test_scored_without_reasoning_goes_back_to_scoring():
    assert route_after_load(load_state("scored", research={"x": 1})) == "score_node"


@pytest.mark.parametrize("status", ["drafted", "skipped", "approved", "rejected"])
def test_finished_companies_are_not_reprocessed(status):
    assert route_after_load(load_state(status)) == END


# ----- other routers -----
def test_research_error_ends_the_graph():
    assert route_after_research({"error": "x"}) == END


def test_research_success_goes_to_scoring():
    assert route_after_research({}) == "score_node"


def test_only_contact_decisions_reach_drafting():
    assert route_after_score({"decision": "contact"}) == "draft_node"
    assert route_after_score({"decision": "skip"}) == END
    assert route_after_score({"decision": "contact", "error": "x"}) == END


# ----- with_retry -----
def test_retry_succeeds_after_a_temporary_failure():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("temporary")
        return "ok"

    assert with_retry(flaky, attempts=3, delay=0) == "ok"
    assert calls["n"] == 2


def test_retry_gives_up_and_raises_the_last_error():
    def always_fails():
        raise RuntimeError("down")

    with pytest.raises(RuntimeError):
        with_retry(always_fails, attempts=2, delay=0)


def test_validation_errors_are_not_retried():
    calls = {"n": 0}

    def invalid():
        calls["n"] += 1
        raise ValueError("bad draft")

    with pytest.raises(ValueError):
        with_retry(invalid, attempts=3, delay=0)
    assert calls["n"] == 1