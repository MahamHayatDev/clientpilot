from typing import Any

from pydantic import BaseModel, Field, model_validator


class ResearchResult(BaseModel):
    what_they_do: str
    audience: str
    gaps: list[str]
    confidence: str


class ScoreResult(BaseModel):
    industry_fit: int = Field(
        ge=0,
        le=35,
        description="Industry fit score from 0 to 35.",
    )

    visible_need: int = Field(
        ge=0,
        le=35,
        description="Visible service need score from 0 to 35.",
    )

    reachability: int = Field(
        ge=0,
        le=20,
        description="Freelancer reachability score from 0 to 20.",
    )

    evidence_quality: int = Field(
        ge=0,
        le=10,
        description="Research evidence quality score from 0 to 10.",
    )

    fit_score: int = Field(
        ge=0,
        le=100,
        description=(
            "Final score. It is automatically recalculated as the sum of "
            "industry_fit, visible_need, reachability, and evidence_quality."
        ),
    )

    reasoning: str = Field(
        description=(
            "2-3 sentences explaining the score, citing specific research details."
        ),
    )

    matched_services: list[str] = Field(
        description=(
            "Which of the freelancer's services this company could realistically "
            "use. Empty list if none."
        ),
    )

    @model_validator(mode="before")
    @classmethod
    def calculate_fit_score(cls, data: Any) -> Any:
        """Always derive the final score from the four validated score categories."""
        if isinstance(data, dict):
            data = data.copy()
            category_fields = (
                "industry_fit",
                "visible_need",
                "reachability",
                "evidence_quality",
            )
            if all(field in data for field in category_fields):
                try:
                    data["fit_score"] = sum(int(data[field]) for field in category_fields)
                except (TypeError, ValueError):
                    # Let Pydantic report the appropriate field validation error.
                    pass
        return data


class DraftResult(BaseModel):
    subject: str = Field(
        description="Email subject line, 8 words or fewer, specific, no clickbait.",
    )

    body: str = Field(
        description=(
            "Plain-text email body of 60 to 110 words. "
            "No greeting, no signature, no placeholders in brackets."
        ),
    )

    gap_referenced: str = Field(
        description="The specific gap from the research that the message refers to.",
    )
