from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl


class Repository(BaseModel):
    """GitHub repository model with filtering criteria."""

    id: int
    name: str
    full_name: str
    description: Optional[str] = None
    html_url: HttpUrl
    stars: int = Field(alias="stargazers_count")
    forks: int = Field(alias="forks_count")
    language: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    license_name: Optional[str] = Field(None, alias="license")
    created_at: datetime
    updated_at: datetime
    pushed_at: Optional[datetime] = None
    open_issues_count: int
    has_issues: bool = True
    archived: bool = False
    disabled: bool = False

    @property
    def is_viable(self) -> bool:
        """Check if repository meets basic viability criteria."""
        return (
            self.has_issues
            and not self.archived
            and not self.disabled
            and self.stars >= 10  # Minimum star threshold
            and self.open_issues_count > 0
            and self.language in {"Python", "JavaScript", "TypeScript", "Go", "Rust"}
        )

    @property
    def activity_score(self) -> float:
        """Calculate repository activity score (0-1)."""
        if not self.pushed_at:
            return 0.0

        days_since_push = (datetime.now() - self.pushed_at.replace(tzinfo=None)).days

        # Fresh repos score higher
        if days_since_push <= 7:
            return 1.0
        elif days_since_push <= 30:
            return 0.8
        elif days_since_push <= 90:
            return 0.5
        else:
            return 0.2

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat(), HttpUrl: str}
