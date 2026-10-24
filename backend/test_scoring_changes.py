import json
from pathlib import Path

from app.agents.scoring import run_scoring

CASES_FILE = Path("evals/cases.json")

TARGET_COMPANIES = [
    "LedgerLoop",
    "InvoiceFlow",
    "BudgetBee",
    "MidBank Digital",
]


def main():
    cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))

    case_lookup = {case["name"]: case for case in cases}

    for name in TARGET_COMPANIES:
        case = case_lookup.get(name)

        if case is None:
            print(f"\nERROR: {name} was not found in cases.json")
            continue

        research = case["research"]

        print("\n" + "=" * 60)
        print(f"COMPANY: {name}")
        print("Running scoring model...")

        try:
            result = run_scoring(name, research)

            category_total = (
                result.industry_fit
                + result.visible_need
                + result.reachability
                + result.evidence_quality
            )

            print(f"Industry fit:     {result.industry_fit}/35")
            print(f"Visible need:     {result.visible_need}/35")
            print(f"Reachability:     {result.reachability}/20")
            print(f"Evidence quality: {result.evidence_quality}/10")
            print(f"Final score:      {result.fit_score}/100")
            print(f"Category sum:     {category_total}/100")
            print(f"Expected decision:{case['expected']}")
            print(f"Actual decision:  {'contact' if result.fit_score >= 50 else 'skip'}")
            print(f"Matched services: {result.matched_services}")
            print(f"Reasoning:        {result.reasoning}")

            if category_total != result.fit_score:
                print("WARNING: Category sum does not match final score.")

        except Exception as exc:
            print(f"ERROR while scoring {name}: {exc}")

    print("\nTargeted scoring tests completed.")


if __name__ == "__main__":
    main()
