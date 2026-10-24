import argparse
import json
import re
import statistics
import time
from datetime import date
from pathlib import Path

from app.agents.drafting import run_drafting
from app.agents.scoring import run_scoring
from app.config import MODEL_NAME
from app.scoring_routes import SCORE_THRESHOLD

HERE = Path(__file__).parent
PAUSE_SECONDS = 6
RETRY_WAIT_SECONDS = 10
CATEGORY_FIELDS = ("industry_fit", "visible_need", "reachability", "evidence_quality")
FAKE_CLAIMS = ["our clients", "my clients", "i helped", "we helped", "guarantee", "increase your revenue"]


def pct(a, b):
    return round(100 * a / b) if b else None


def fmt(value, suffix=""):
    return "n/a" if value is None else f"{value}{suffix}"


def load_cases():
    return json.loads((HERE / "cases.json").read_text(encoding="utf-8"))


def call_with_wait(fn, *args, tries=3, wait=RETRY_WAIT_SECONDS):
    for attempt in range(tries):
        try:
            return fn(*args)
        except ValueError:
            raise
        except Exception as exc:
            if attempt == tries - 1:
                raise
            print(f"   Temporary error, attempt {attempt + 1}/{tries}. Retrying in {wait}s: {str(exc)[:100]}")
            time.sleep(wait)


def score_case(case):
    """Return the final score and category-level diagnostics."""
    research = case["research"]
    if research.get("confidence") == "low":
        return {
            "score": 0,
            "category_scores": {field: None for field in CATEGORY_FIELDS},
            "category_total": None,
            "category_total_matches": None,
            "reasoning": "Research confidence is low; lead skipped.",
            "matched_services": [],
        }

    try:
        result = call_with_wait(run_scoring, case["name"], research)
    finally:
        time.sleep(PAUSE_SECONDS)

    categories = {field: int(getattr(result, field)) for field in CATEGORY_FIELDS}
    category_total = sum(categories.values())
    score = max(0, min(100, int(result.fit_score)))
    return {
        "score": score,
        "category_scores": categories,
        "category_total": category_total,
        "category_total_matches": category_total == score,
        "reasoning": result.reasoning,
        "matched_services": result.matched_services,
    }


def eval_scoring(cases, repeat_n):
    print(f"\nSCORING EVAL: {len(cases)} cases, threshold {SCORE_THRESHOLD}")
    rows = []

    for case in cases:
        try:
            scored = score_case(case)
            score = scored["score"]
            decision = "contact" if score >= SCORE_THRESHOLD else "skip"
            row = {
                "name": case["name"], "tier": case["tier"],
                "expected": case["expected"], "score": score,
                "decision": decision, "correct": decision == case["expected"],
                "category_scores": scored["category_scores"],
                "category_total": scored["category_total"],
                "category_total_matches": scored["category_total_matches"],
                "reasoning": scored["reasoning"],
                "matched_services": scored["matched_services"], "error": None,
            }
            status = "OK  " if row["correct"] else "MISS"
            print(f"  {status} {case['name']:<24} score {score:>3} expected {case['expected']}")
            if row["category_total_matches"] is False:
                print(f"   WARNING: category total {row['category_total']} != final score {score}")
        except Exception as exc:
            row = {
                "name": case["name"], "tier": case["tier"],
                "expected": case["expected"], "score": None,
                "decision": "error", "correct": None,
                "category_scores": {field: None for field in CATEGORY_FIELDS},
                "category_total": None, "category_total_matches": None,
                "error": str(exc)[:200],
            }
            print(f"  ERROR {case['name']:<24} {str(exc)[:120]}")
        rows.append(row)

    scored_rows = [r for r in rows if r["score"] is not None]
    failed_rows = [r for r in rows if r["score"] is None]
    clear = [r for r in scored_rows if r["tier"] == "clear"]
    borderline = [r for r in scored_rows if r["tier"] == "borderline"]

    tp = sum(r["expected"] == "contact" and r["decision"] == "contact" for r in scored_rows)
    fp = sum(r["expected"] == "skip" and r["decision"] == "contact" for r in scored_rows)
    fn = sum(r["expected"] == "contact" and r["decision"] == "skip" for r in scored_rows)
    good_scores = [r["score"] for r in scored_rows if r["expected"] == "contact"]
    bad_scores = [r["score"] for r in scored_rows if r["expected"] == "skip"]

    print(f"\nCONSISTENCY CHECK: re-scoring up to {repeat_n} cases")
    first_by_name = {r["name"]: r for r in scored_rows}
    candidates = [c for c in cases if c["name"] in first_by_name and c["research"].get("confidence") != "low"][:repeat_n]
    total_diffs = []
    category_diffs = {field: [] for field in CATEGORY_FIELDS}
    consistency_rows = []

    for case in candidates:
        try:
            second = score_case(case)
            first = first_by_name[case["name"]]
            diff = abs(second["score"] - first["score"])
            total_diffs.append(diff)
            comparison = {}
            for field in CATEGORY_FIELDS:
                a = first["category_scores"].get(field)
                b = second["category_scores"].get(field)
                d = abs(a - b) if a is not None and b is not None else None
                comparison[field] = {"first": a, "second": b, "absolute_difference": d}
                if d is not None:
                    category_diffs[field].append(d)
            consistency_rows.append({
                "name": case["name"], "first_score": first["score"],
                "second_score": second["score"], "absolute_score_difference": diff,
                "category_comparison": comparison,
            })
            print(f"  {case['name']:<24} first {first['score']:>3} second {second['score']:>3} diff {diff:>2}")
        except Exception as exc:
            print(f"  ERROR repeating {case['name']}: {str(exc)[:100]}")
            consistency_rows.append({"name": case["name"], "error": str(exc)[:200]})

    return {
        "cases": len(rows), "completed": len(scored_rows), "failed": len(failed_rows),
        "accuracy": pct(sum(r["correct"] for r in scored_rows), len(scored_rows)),
        "accuracy_clear": pct(sum(r["correct"] for r in clear), len(clear)),
        "accuracy_borderline": pct(sum(r["correct"] for r in borderline), len(borderline)),
        "precision_contact": pct(tp, tp + fp), "recall_contact": pct(tp, tp + fn),
        "avg_score_good_leads": round(statistics.mean(good_scores), 1) if good_scores else None,
        "avg_score_bad_leads": round(statistics.mean(bad_scores), 1) if bad_scores else None,
        "consistency_avg_diff": round(statistics.mean(total_diffs), 1) if total_diffs else None,
        "consistency_max_diff": max(total_diffs) if total_diffs else None,
        "category_consistency_avg_diff": {
            field: round(statistics.mean(vals), 1) if vals else None
            for field, vals in category_diffs.items()
        },
        "consistency_rows": consistency_rows, "rows": rows,
    }


def research_text(research):
    parts = [research.get("what_they_do", ""), research.get("audience", "")]
    parts += list(research.get("gaps") or [])
    return " ".join(parts).lower()


def significant_words(text):
    return {word for word in re.findall(r"[a-z]{4,}", text.lower())}


def check_draft(draft, research):
    problems = []
    source = research_text(research)
    source_numbers = set(re.findall(r"\d+", source))
    for number in re.findall(r"\d+", draft.body):
        if number not in source_numbers:
            problems.append(f"number not in research: {number}")
            break
    lowered = draft.body.lower()
    for phrase in FAKE_CLAIMS:
        if phrase in lowered:
            problems.append(f"unsupported claim: {phrase}")
    gaps = research.get("gaps") or []
    if gaps:
        mentioned = significant_words(draft.gap_referenced)
        grounded = any(len(mentioned & significant_words(gap)) >= 2 for gap in gaps)
        if not grounded:
            problems.append("gap_referenced does not match any researched gap")
    return problems


def eval_drafting(cases):
    print(f"\nDRAFTING EVAL: {len(cases)} cases")
    results = []
    for case in cases:
        try:
            result = call_with_wait(run_drafting, case["name"], case["research"], "Strong fit with the freelancer's services.")
            _, _, draft = result
            problems = check_draft(draft, case["research"])
            row = {"name": case["name"], "ok": not problems, "problems": problems, "words": len(draft.body.split()), "error": None}
        except Exception as exc:
            row = {"name": case["name"], "ok": False, "problems": [], "words": None, "error": str(exc)[:200]}
        results.append(row)
        if row["error"]:
            print(f"  ERROR {case['name']:<24} {row['error'][:120]}")
        elif row["ok"]:
            print(f"  OK   {case['name']}")
        else:
            print(f"  FAIL {case['name']:<24} {'; '.join(row['problems'])}")
        time.sleep(PAUSE_SECONDS)

    successful = [r for r in results if r["words"] is not None]
    passed = [r for r in successful if r["ok"]]
    word_counts = [r["words"] for r in successful]
    return {
        "cases": len(results), "completed": len(successful), "failed": len(results) - len(successful),
        "pass_rate": pct(len(passed), len(successful)),
        "avg_words": round(statistics.mean(word_counts)) if word_counts else None,
        "rows": results,
    }


def write_reports(scoring, drafting):
    (HERE / "results.json").write_text(
        json.dumps({"scoring": scoring, "drafting": drafting}, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# ClientPilot evaluation results", "",
        f"Run date: {date.today().isoformat()} | Model: {MODEL_NAME} | Score threshold: {SCORE_THRESHOLD}", "",
        "Labels were written by the project author. Borderline cases are judgment calls.", "",
        "## Lead scoring", "", "| Metric | Result |", "|---|---|",
        f"| Cases attempted | {scoring['cases']} |",
        f"| Cases completed | {scoring['completed']} |",
        f"| Cases failed | {scoring['failed']} |",
        f"| Decision accuracy (completed cases) | {fmt(scoring['accuracy'], '%')} |",
        f"| Decision accuracy (clear cases) | {fmt(scoring['accuracy_clear'], '%')} |",
        f"| Decision accuracy (borderline cases) | {fmt(scoring['accuracy_borderline'], '%')} |",
        f"| Precision (contacted leads that were good) | {fmt(scoring['precision_contact'], '%')} |",
        f"| Recall (good leads that were contacted) | {fmt(scoring['recall_contact'], '%')} |",
        f"| Average score, good leads | {fmt(scoring['avg_score_good_leads'])} |",
        f"| Average score, bad leads | {fmt(scoring['avg_score_bad_leads'])} |",
        f"| Score consistency (average difference) | {fmt(scoring['consistency_avg_diff'])} points |",
        f"| Score consistency (maximum difference) | {fmt(scoring['consistency_max_diff'])} points |",
        "", "### Average category-score differences on repeat runs", "",
        "| Category | Average absolute difference |", "|---|---:|",
    ]
    for field, value in scoring["category_consistency_avg_diff"].items():
        lines.append(f"| {field} | {fmt(value)} points |")

    lines += [
        "", "Failed cases are excluded from scoring metrics.", "",
        "## Lead-level scoring diagnostics", "",
        "| Company | Score | Industry /35 | Need /35 | Reachability /20 | Evidence /10 | Decision | Expected | Correct |",
        "|---|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for row in scoring["rows"]:
        cats = row.get("category_scores") or {}
        val = lambda field: "n/a" if cats.get(field) is None else str(cats[field])
        score = row["score"] if row["score"] is not None else "n/a"
        correct = "n/a" if row["correct"] is None else str(row["correct"])
        lines.append(
            f"| {row['name']} | {score} | {val('industry_fit')} | {val('visible_need')} | "
            f"{val('reachability')} | {val('evidence_quality')} | {row['decision']} | "
            f"{row['expected']} | {correct} |"
        )

    lines += ["", "### Reasoning and matched services", ""]
    for row in scoring["rows"]:
        lines += [
            f"#### {row['name']}", "",
            f"- Reasoning: {row.get('reasoning') or row.get('error') or 'No reasoning available.'}",
            f"- Matched services: {', '.join(row.get('matched_services') or []) or 'None identified'}",
        ]
        if row.get("category_total_matches") is False:
            lines.append(f"- WARNING: category total ({row.get('category_total')}) does not match score ({row.get('score')}).")
        lines.append("")

    lines += ["## Repeat-run consistency details", ""]
    for row in scoring["consistency_rows"]:
        if row.get("error"):
            lines += [f"### {row['name']}", "", f"- Repeat error: {row['error']}", ""]
            continue
        lines += [
            f"### {row['name']}", "",
            f"- Total score: {row['first_score']} -> {row['second_score']}",
            f"- Absolute total-score difference: {row['absolute_score_difference']}",
        ]
        for field, values in row["category_comparison"].items():
            lines.append(f"- {field}: {values['first']} -> {values['second']} (difference: {values['absolute_difference']})")
        lines.append("")

    if drafting is not None:
        lines += [
            "## Outreach drafting", "", "| Metric | Result |", "|---|---|",
            f"| Drafts attempted | {drafting['cases']} |",
            f"| Drafts completed | {drafting['completed']} |",
            f"| Draft-generation failures | {drafting['failed']} |",
            f"| Passed quality checks | {fmt(drafting['pass_rate'], '%')} |",
            f"| Average body length | {fmt(drafting['avg_words'])} words |", "",
            "Quality checks flag unsupported numbers, banned phrases, and gaps that do not match the research.", "",
        ]
    (HERE / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Only run the first N scoring cases")
    parser.add_argument("--repeat", type=int, default=5, help="Cases to re-score for consistency")
    parser.add_argument("--draft-n", type=int, default=8, help="Number of drafts to test")
    parser.add_argument("--skip-drafting", action="store_true", help="Skip the drafting evaluation")
    args = parser.parse_args()

    cases = load_cases()
    scoring_cases = cases[:args.limit] if args.limit > 0 else cases
    scoring = eval_scoring(scoring_cases, max(0, args.repeat))
    drafting = None
    if not args.skip_drafting:
        pool = [c for c in cases if c["expected"] == "contact" and c["tier"] == "clear"]
        drafting = eval_drafting(pool[:max(0, args.draft_n)])
    write_reports(scoring, drafting)
    print("\nEvaluation finished.")
    print(f"Scoring: {scoring['completed']} completed, {scoring['failed']} failed.")
    if drafting is not None:
        print(f"Drafting: {drafting['completed']} completed, {drafting['failed']} failed.")
    print("Reports saved to evals\\RESULTS.md and evals\\results.json")


if __name__ == "__main__":
    main()
