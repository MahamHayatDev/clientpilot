from pydantic import BaseModel, Field


class ResearchResult(BaseModel):
    what_they_do: str
    audience: str
    gaps: list[str]
    confidence: str


class ScoreResult(BaseModel):
    fit_score: int = Field(
        description="Overall fit from 0 to 100, following the scoring rubric exactly."
    )

    reasoning: str = Field(
        description="2-3 sentences explaining the score, citing specific research details."
    )

    matched_services: list[str] = Field(
        description="Which of the freelancer's services this company could realistically use. Empty list if none."
    )


class DraftResult(BaseModel):
    subject: str = Field(
        description="Email subject line, 8 words or fewer, specific, no clickbait."
    )

    body: str = Field(
        description=(
            "Plain-text email body of 60 to 110 words. "
            "No greeting, no signature, no placeholders in brackets."
        )
    )

    gap_referenced: str = Field(
        description="The specific gap from the research that the message refers to."
    )