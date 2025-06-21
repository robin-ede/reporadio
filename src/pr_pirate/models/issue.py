from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl


class IssueStatus(str, Enum):
    """Issue processing status."""

    DISCOVERED = "discovered"
    FILTERED_OUT = "filtered_out"
    QUEUED = "queued"
    ASSESSING = "assessing"
    ASSESSED = "assessed"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Issue(BaseModel):
    """GitHub issue model with processing metadata."""

    id: int
    number: int
    title: str
    body: Optional[str] = None
    html_url: HttpUrl
    state: str  # "open" or "closed"
    labels: List[str] = Field(default_factory=list)
    assignee: Optional[str] = None
    assignees: List[str] = Field(default_factory=list)
    comments: int
    created_at: datetime
    updated_at: datetime
    author_association: str

    # Repository context
    repo_id: int
    repo_full_name: str

    # Processing metadata
    status: IssueStatus = IssueStatus.DISCOVERED
    discovered_at: datetime = Field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None

    @property
    def is_good_candidate(self) -> bool:
        """Check if issue is a good candidate for automated fixing."""
        good_labels = {
            "good first issue",
            "good-first-issue",
            "beginner",
            "easy",
            "bug",
            "enhancement",
            "feature",
            "help wanted",
        }

        bad_labels = {
            "wontfix",
            "invalid",
            "duplicate",
            "question",
            "discussion",
            "needs-design",
            "breaking-change",
        }

        # Convert labels to lowercase for comparison
        issue_labels = {label.lower() for label in self.labels}

        return (
            self.state == "open"
            and not self.assignees  # Not already assigned
            and len(issue_labels & good_labels) > 0  # Has good labels
            and len(issue_labels & bad_labels) == 0  # No bad labels
            and self.comments <= 10  # Not overly discussed
            and bool(self.title)  # Has a title
            and (len(self.body) >= 50 if self.body else True)  # Reasonable description
        )

    @property
    def age_days(self) -> int:
        """Age of issue in days."""
        return (datetime.now() - self.created_at.replace(tzinfo=None)).days

    @property
    def priority_score(self) -> float:
        """Calculate priority score (0-1) based on various factors."""
        score = 0.5  # Base score

        # Label-based scoring
        high_priority_labels = {"bug", "critical", "urgent"}
        medium_priority_labels = {"enhancement", "feature", "good first issue"}

        issue_labels = {label.lower() for label in self.labels}

        if issue_labels & high_priority_labels:
            score += 0.3
        elif issue_labels & medium_priority_labels:
            score += 0.2

        # Age-based scoring (newer issues get slight boost)
        if self.age_days <= 7:
            score += 0.1
        elif self.age_days <= 30:
            score += 0.05

        # Comment activity (some discussion is good, too much isn't)
        if 1 <= self.comments <= 3:
            score += 0.1
        elif self.comments > 10:
            score -= 0.2

        return min(1.0, max(0.0, score))

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat(), HttpUrl: str}
