from pathlib import Path
from typing import Optional
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Float,
    Text,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class RepositoryDB(Base):
    """SQLAlchemy model for repositories."""

    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    full_name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    html_url = Column(String, nullable=False)
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    language = Column(String)
    topics = Column(JSON)
    license_name = Column(String)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    pushed_at = Column(DateTime)
    open_issues_count = Column(Integer, default=0)
    has_issues = Column(Boolean, default=True)
    archived = Column(Boolean, default=False)
    disabled = Column(Boolean, default=False)

    # Discovery metadata
    discovered_at = Column(DateTime, nullable=False)
    last_checked = Column(DateTime)


class IssueDB(Base):
    """SQLAlchemy model for issues."""

    __tablename__ = "issues"

    id = Column(Integer, primary_key=True)
    number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text)
    html_url = Column(String, nullable=False)
    state = Column(String, nullable=False)
    labels = Column(JSON)
    assignee = Column(String)
    assignees = Column(JSON)
    comments = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    author_association = Column(String)

    # Repository context
    repo_id = Column(Integer, nullable=False)
    repo_full_name = Column(String, nullable=False)

    # Processing metadata
    status = Column(String, default="discovered")
    discovered_at = Column(DateTime, nullable=False)
    processed_at = Column(DateTime)


class AssessmentDB(Base):
    """SQLAlchemy model for assessments."""

    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True)
    issue_id = Column(Integer, nullable=False)
    issue_number = Column(Integer, nullable=False)
    repo_full_name = Column(String, nullable=False)

    # Scoring metrics
    complexity_score = Column(Float, nullable=False)
    clarity_score = Column(Float, nullable=False)
    scope_score = Column(Float, nullable=False)
    feasibility_score = Column(Float, nullable=False)
    overall_score = Column(Float, nullable=False)

    is_doable = Column(Boolean, nullable=False)
    confidence = Column(Float, nullable=False)

    # Reasoning
    reasoning = Column(Text, nullable=False)
    estimated_effort_hours = Column(Float)
    required_skills = Column(JSON)
    potential_risks = Column(JSON)

    # Metadata
    assessed_at = Column(DateTime, nullable=False)
    model_used = Column(String, default="claude-3-sonnet")
    assessment_version = Column(String, default="1.0")


class DatabaseManager:
    """Database connection and session management."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path("data/pr_pirate.db")

        # Ensure directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(f"sqlite:///{db_path}")
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # Create tables
        Base.metadata.create_all(bind=self.engine)  # type: ignore

    def get_session(self):
        """Get database session."""
        return self.SessionLocal()

    def close(self):
        """Close database connection."""
        self.engine.dispose()  # type: ignore
