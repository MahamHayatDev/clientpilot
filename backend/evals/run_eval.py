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

FAKE_CLAIMS = [
    "our clients",
    "my clients",
    "i helped",
    "we helped",
    "guarantee",
    "increase your revenue",
]


def pct(a, b):
    return round(100 * a / b) if b else None


def fmt(value, suffix=""):
    return "n/a" if value is None else f"{value}{suffix}"


def load_cases():
    return json.loads(
        (HERE / "cases.json").read_text(encoding="utf-8")
    )


def call_with_wait(fn, *args, tries=3, wait=RETRY_WAIT_SECONDS):
    """Retry temporary failures, then raise the final error."""
    for attempt in range(tries):
        try:
            return fn(*args)

        except ValueError:
            raise

        except Exception as exc:
            if attempt == tries - 1:
                raise

            print(
                f"   Temporary error, attempt {attempt + 1}/{tries}. "
                f"Retrying in {wait}s: {str(exc)[:100]}"
            )
            time.sleep(wait)


# ---------------- Scoring eval ----------------

def score_case(case):
    research = case["research"]

    # Avoid model calls when research is too thin.
    if research.get("confidence") == "low":
        return 0

    try:
        result = call_with_wait(
            run_scoring,
            case["name"],
            research,
        )
    finally:
        time.sleep(PAUSE_SECONDS)

    return max(0, min(100, int(result.fit_score)))


def eval_scoring(cases, repeat_n):
    print(
        f"\nSCORING EVAL: {len(cases)} cases, "
        f"threshold {SCORE_THRESHOLD}"
    )

    rows = []

    for case in cases:
        try:
            score = score_case(case)
            decision = (
                "contact"
                if score >= SCORE_THRESHOLD
                else "skip"
            )
            correct = decision == case["expected"]

            row = {
                "name": case["name"],
                "tier": case["tier"],
                "expected": case["expected"],
                "score": score,
                "decision": decision,
                "correct": correct,
                "error": None,
            }

            status = "OK  " if correct else "MISS"

            print(
                f"  {status} {case['name']:<24} "
                f"score {score:>3} "
                f" expected {case['expected']}"
            )

        except Exception as exc:
            row = {
                "name": case["name"],
                "tier": case["tier"],
                "expected": case["expected"],
                "score": None,
                "decision": "error",
                "correct": None,
                "error": str(exc)[:200],
            }

            print(
                f"  ERROR {case['name']:<24} "
                f"{str(exc)[:120]}"
            )

        rows.append(row)

    # Only successfully scored cases count toward score metrics.
    scored_rows = [
        row for row in rows
        if row["score"] is not None
    ]

    failed_rows = [
        row for row in rows
        if row["score"] is None
    ]

    clear = [
        row for row in scored_rows
        if row["tier"] == "clear"
    ]

    borderline = [
        row for row in scored_rows
        if row["tier"] == "borderline"
    ]

    true_positive = sum(
        1 for row in scored_rows
        if row["expected"] == "contact"
        and row["decision"] == "contact"
    )

    false_positive = sum(
        1 for row in scored_rows
        if row["expected"] == "skip"
        and row["decision"] == "contact"
    )

    false_negative = sum(
        1 for row in scored_rows
        if row["expected"] == "contact"
        and row["decision"] == "skip"
    )

    good_scores = [
        row["score"] for row in scored_rows
        if row["expected"] == "contact"
    ]

    bad_scores = [
        row["score"] for row in scored_rows
        if row["expected"] == "skip"
    ]

    # Consistency check: only repeat cases with a successful first score.
    print(
        f"\nCONSISTENCY CHECK: re-scoring up to {repeat_n} cases"
    )

    first_scores = {
        row["name"]: row["score"]
        for row in scored_rows
    }

    repeat_candidates = [
        case for case in cases
        if case["name"] in first_scores
        and case["research"].get("confidence") != "low"
    ][:repeat_n]

    differences = []

    for case in repeat_candidates:
        try:
            second_score = score_case(case)
            first_score = first_scores[case["name"]]

            difference = abs(second_score - first_score)
            differences.append(difference)

            print(
                f"  {case['name']:<24} "
                f"first {first_score:>3} "
                f"second {second_score:>3}"
            )

        except Exception as exc:
            print(
                f"  ERROR repeating {case['name']}: "
                f"{str(exc)[:100]}"
            )

    successful_count = len(scored_rows)

    accuracy = pct(
        sum(row["correct"] for row in scored_rows),
        successful_count,
    )

    accuracy_clear = pct(
        sum(row["correct"] for row in clear),
        len(clear),
    )

    accuracy_borderline = pct(
        sum(row["correct"] for row in borderline),
        len(borderline),
    )

    return {
        "cases": len(rows),
        "completed": successful_count,
        "failed": len(failed_rows),
        "accuracy": accuracy,
        "accuracy_clear": accuracy_clear,
        "accuracy_borderline": accuracy_borderline,
        "precision_contact": pct(
            true_positive,
            true_positive + false_positive,
        ),
        "recall_contact": pct(
            true_positive,
            true_positive + false_negative,
        ),
        "avg_score_good_leads": (
            round(statistics.mean(good_scores), 1)
            if good_scores else None
        ),
        "avg_score_bad_leads": (
            round(statistics.mean(bad_scores), 1)
            if bad_scores else None
        ),
        "consistency_avg_diff": (
            round(statistics.mean(differences), 1)
            if differences else None
        ),
        "consistency_max_diff": (
            max(differences) if differences else None
        ),
        "rows": rows,
    }


# ---------------- Drafting eval ----------------

def research_text(research):
    parts = [
        research.get("what_they_do", ""),
        research.get("audience", ""),
    ]

    parts += list(research.get("gaps") or [])

    return " ".join(parts).lower()


def significant_words(text):
    return {
        word
        for word in re.findall(r"[a-z]{4,}", text.lower())
    }


def check_draft(draft, research):
    problems = []
    source = research_text(research)

    # Flag numbers that do not appear in the research.
    source_numbers = set(re.findall(r"\d+", source))

    for number in re.findall(r"\d+", draft.body):
        if number not in source_numbers:
            problems.append(
                f"number not in research: {number}"
            )
            break

    # Flag unsupported personal claims and promises.
    lowered = draft.body.lower()

    for phrase in FAKE_CLAIMS:
        if phrase in lowered:
            problems.append(
                f"unsupported claim: {phrase}"
            )

    # Check that the referenced gap matches the research.
    gaps = research.get("gaps") or []

    if gaps:
        mentioned = significant_words(
            draft.gap_referenced
        )

        grounded = any(
            len(mentioned & significant_words(gap)) >= 2
            for gap in gaps
        )

        if not grounded:
            problems.append(
                "gap_referenced does not match any researched gap"
            )

    return problems


def eval_drafting(cases):
    print(f"\nDRAFTING EVAL: {len(cases)} cases")

    results = []

    for case in cases:
        try:
            result = call_with_wait(
                run_drafting,
                case["name"],
                case["research"],
                "Strong fit with the freelancer's services.",
            )

            _, _, draft = result

            problems = check_draft(
                draft,
                case["research"],
            )

            row = {
                "name": case["name"],
                "ok": not problems,
                "problems": problems,
                "words": len(draft.body.split()),
                "error": None,
            }

        except Exception as exc:
            row = {
                "name": case["name"],
                "ok": False,
                "problems": [],
                "words": None,
                "error": str(exc)[:200],
            }

        results.append(row)

        if row["error"]:
            print(
                f"  ERROR {case['name']:<24} "
                f"{row['error'][:120]}"
            )

        elif row["ok"]:
            print(f"  OK   {case['name']}")

        else:
            print(
                f"  FAIL {case['name']:<24} "
                f"{'; '.join(row['problems'])}"
            )

        time.sleep(PAUSE_SECONDS)

    successful_drafts = [
        row for row in results
        if row["words"] is not None
    ]

    passed_drafts = [
        row for row in successful_drafts
        if row["ok"]
    ]

    word_counts = [
        row["words"] for row in successful_drafts
    ]

    return {
        "cases": len(results),
        "completed": len(successful_drafts),
        "failed": len(results) - len(successful_drafts),
        "pass_rate": pct(
            len(passed_drafts),
            len(successful_drafts),
        ),
        "avg_words": (
            round(statistics.mean(word_counts))
            if word_counts else None
        ),
        "rows": results,
    }


# ---------------- Reports ----------------

def write_reports(scoring, drafting):
    output = {
        "scoring": scoring,
        "drafting": drafting,
    }

    (HERE / "results.json").write_text(
        json.dumps(output, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# ClientPilot evaluation results",
        "",
        (
            f"Run date: {date.today().isoformat()} | "
            f"Model: {MODEL_NAME} | "
            f"Score threshold: {SCORE_THRESHOLD}"
        ),
        "",
        (
            "Labels were written by the project author. "
            "Borderline cases are judgment calls."
        ),
        "",
        "## Lead scoring",
        "",
        "| Metric | Result |",
        "|---|---|",
        f"| Cases attempted | {scoring['cases']} |",
        f"| Cases completed | {scoring['completed']} |",
        f"| Cases failed | {scoring['failed']} |",
        (
            f"| Decision accuracy (completed cases) | "
            f"{fmt(scoring['accuracy'], '%')} |"
        ),
        (
            f"| Decision accuracy (clear cases) | "
            f"{fmt(scoring['accuracy_clear'], '%')} |"
        ),
        (
            f"| Decision accuracy (borderline cases) | "
            f"{fmt(scoring['accuracy_borderline'], '%')} |"
        ),
        (
            f"| Precision (contacted leads that were good) | "
            f"{fmt(scoring['precision_contact'], '%')} |"
        ),
        (
            f"| Recall (good leads that were contacted) | "
            f"{fmt(scoring['recall_contact'], '%')} |"
        ),
        (
            f"| Average score, good leads | "
            f"{fmt(scoring['avg_score_good_leads'])} |"
        ),
        (
            f"| Average score, bad leads | "
            f"{fmt(scoring['avg_score_bad_leads'])} |"
        ),
        (
            f"| Score consistency (average difference) | "
            f"{fmt(scoring['consistency_avg_diff'])} points |"
        ),
        (
            f"| Score consistency (maximum difference) | "
            f"{fmt(scoring['consistency_max_diff'])} points |"
        ),
        "",
        "Failed cases are excluded from scoring metrics.",
        "",
    ]

    if drafting is not None:
        lines += [
            "## Outreach drafting",
            "",
            "| Metric | Result |",
            "|---|---|",
            f"| Drafts attempted | {drafting['cases']} |",
            f"| Drafts completed | {drafting['completed']} |",
            f"| Draft-generation failures | {drafting['failed']} |",
            (
                f"| Passed quality checks | "
                f"{fmt(drafting['pass_rate'], '%')} |"
            ),
            (
                f"| Average body length | "
                f"{fmt(drafting['avg_words'])} words |"
            ),
            "",
            (
                "Quality checks flag unsupported numbers, "
                "banned phrases, and gaps that do not match "
                "the research."
            ),
            "",
        ]

    (HERE / "RESULTS.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


# ---------------- Main ----------------

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Only run the first N scoring cases",
    )

    parser.add_argument(
        "--repeat",
        type=int,
        default=5,
        help="Cases to re-score for consistency",
    )

    parser.add_argument(
        "--draft-n",
        type=int,
        default=8,
        help="Number of drafts to test",
    )

    parser.add_argument(
        "--skip-drafting",
        action="store_true",
        help="Skip the drafting evaluation",
    )

    args = parser.parse_args()

    cases = load_cases()

    scoring_cases = (
        cases[:args.limit]
        if args.limit > 0
        else cases
    )

    scoring = eval_scoring(
        scoring_cases,
        max(0, args.repeat),
    )

    drafting = None

    if not args.skip_drafting:
        pool = [
            case for case in cases
            if case["expected"] == "contact"
            and case["tier"] == "clear"
        ]

        drafting = eval_drafting(
            pool[:max(0, args.draft_n)]
        )

    write_reports(scoring, drafting)

    print("\nEvaluation finished.")
    print(
        f"Scoring: {scoring['completed']} completed, "
        f"{scoring['failed']} failed."
    )

    if drafting is not None:
        print(
            f"Drafting: {drafting['completed']} completed, "
            f"{drafting['failed']} failed."
        )

    print(
        "Reports saved to evals\\RESULTS.md "
        "and evals\\results.json"
    )


if __name__ == "__main__":
    main()