from pathlib import Path
import re
import shutil
import sys

schema_path = Path("app/schemas.py")
agent_paths = [
    Path("app/agents/scoring.py"),
    Path("app/agents/scoring_best_100.py"),
]

schema_text = schema_path.read_text(encoding="utf-8")

schema_pattern = (
    r"class ScoreResult\(BaseModel\):.*?"
    r"(?=\n\nclass DraftResult)"
)

schema_replacement = '''class ScoreResult(BaseModel):
    industry_fit: int = Field(
        ge=0, le=35,
        description="Industry fit score from 0 to 35."
    )

    visible_need: int = Field(
        ge=0, le=35,
        description="Visible service need score from 0 to 35."
    )

    reachability: int = Field(
        ge=0, le=20,
        description="Freelancer reachability score from 0 to 20."
    )

    evidence_quality: int = Field(
        ge=0, le=10,
        description="Research evidence quality score from 0 to 10."
    )

    fit_score: int = Field(
        ge=0, le=100,
        description="Final score, calculated as the sum of the four category scores."
    )

    reasoning: str = Field(
        description="2-3 sentences explaining the score, citing specific research details."
    )

    matched_services: list[str] = Field(
        description="Which of the freelancer's services this company could realistically use. Empty list if none."
    )
'''

if not re.search(schema_pattern, schema_text, re.S):
    print("ERROR: ScoreResult block not found. No files changed.")
    sys.exit(1)

updated_schema = re.sub(
    schema_pattern,
    lambda _: schema_replacement,
    schema_text,
    count=1,
    flags=re.S,
)

updated_agents = {}

for path in agent_paths:
    text = path.read_text(encoding="utf-8")

    function_pattern = (
        r"def run_scoring\(name: str, research: dict\) -> ScoreResult:"
        r".*\Z"
    )

    match = re.search(function_pattern, text, re.S)

    if not match:
        print(f"ERROR: run_scoring function not found in {path}.")
        print("No files changed.")
        sys.exit(1)

    function_replacement = '''def run_scoring(name: str, research: dict) -> ScoreResult:
    gaps = research.get("gaps") or []

    result = chain.invoke(
        {
            "services": MY_SERVICES,
            "ideal_client": IDEAL_CLIENT,
            "name": name,
            "what_they_do": research.get("what_they_do", "not stated"),
            "audience": research.get("audience", "not stated"),
            "gaps": "; ".join(gaps) if gaps else "none found",
            "confidence": research.get("confidence", "low"),
        }
    )

    total = (
        result.industry_fit
        + result.visible_need
        + result.reachability
        + result.evidence_quality
    )

    return result.model_copy(update={"fit_score": total})
'''

    updated_agents[path] = re.sub(
        function_pattern,
        lambda _: function_replacement,
        text,
        count=1,
        flags=re.S,
    )

# All expected sections were found. Back up the originals before writing.
for path in [schema_path, *agent_paths]:
    shutil.copy2(path, Path(str(path) + ".bak"))

schema_path.write_text(updated_schema, encoding="utf-8")

for path, updated_text in updated_agents.items():
    path.write_text(updated_text, encoding="utf-8")

print("Updated ScoreResult and both scoring agents.")
print("Original files backed up with the .bak extension.")
print("The final fit_score is now calculated from the four category scores.")
