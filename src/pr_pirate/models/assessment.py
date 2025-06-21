from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Assessment(BaseModel):
    """LLM assessment result for an issue."""

    issue_id: int
    issue_number: int
    repo_full_name: str

    # Scoring metrics (1-10 scale)
    complexity_score: float = Field(ge=1, le=10)
    clarity_score: float = Field(ge=1, le=10)
    scope_score: float = Field(ge=1, le=10)
    feasibility_score: float = Field(ge=1, le=10)

    # Overall assessment
    overall_score: float = Field(ge=1, le=10)
    is_doable: bool
    confidence: float = Field(ge=0, le=1)

    # Reasoning
    reasoning: str
    estimated_effort_hours: Optional[float] = None
    required_skills: list[str] = Field(default_factory=list)
    potential_risks: list[str] = Field(default_factory=list)

    # Metadata
    assessed_at: datetime = Field(default_factory=datetime.now)
    model_used: str = "claude-3-sonnet"
    assessment_version: str = "1.0"

    @property
    def composite_score(self) -> float:
        """Calculate weighted composite score."""
        weights = {
            "feasibility": 0.3,
            "clarity": 0.25,
            "complexity": 0.25,  # Lower complexity is better
            "scope": 0.2,
        }

        # Invert complexity score (lower complexity = higher score)
        adjusted_complexity = 11 - self.complexity_score

        return (
            weights["feasibility"] * self.feasibility_score
            + weights["clarity"] * self.clarity_score
            + weights["complexity"] * adjusted_complexity
            + weights["scope"] * self.scope_score
        )

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}
