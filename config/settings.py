"""Configuration settings for PR Pirate."""

from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# GitHub API settings
GITHUB_API_BASE_URL = "https://api.github.com"
RATE_LIMIT_BUFFER = 100  # Keep this many requests in reserve

# Repository discovery settings
TARGET_TOPICS = {
    "llm": [
        "llm",
        "large-language-model",
        "language-model",
        "gpt",
        "bert",
        "transformer",
    ],
    "genai": ["generative-ai", "genai", "ai-generation", "artificial-intelligence"],
    "llmops": ["llmops", "mlops", "ai-ops", "model-deployment", "ai-infrastructure"],
    "ml": [
        "machine-learning",
        "deep-learning",
        "neural-network",
        "pytorch",
        "tensorflow",
    ],
    "nlp": [
        "nlp",
        "natural-language-processing",
        "text-processing",
        "language-understanding",
    ],
}

SUPPORTED_LANGUAGES = {"Python", "JavaScript", "TypeScript", "Go", "Rust", "Java"}

# Repository filtering
MIN_STARS = 10
MAX_STARS = 10000
MIN_ACTIVITY_DAYS = 180  # Repository must be active within this many days
MAX_REPOS_PER_CATEGORY = 50

# Issue discovery settings
GOOD_ISSUE_LABELS = {
    "good first issue",
    "good-first-issue",
    "beginner",
    "easy",
    "bug",
    "enhancement",
    "feature",
    "help wanted",
    "hacktoberfest",
}

BAD_ISSUE_LABELS = {
    "wontfix",
    "invalid",
    "duplicate",
    "question",
    "discussion",
    "needs-design",
    "breaking-change",
    "major",
    "epic",
    "tracking",
}

MAX_ISSUES_PER_REPO = 20
MAX_ISSUE_AGE_DAYS = 365
MIN_ISSUE_AGE_DAYS = 1

# Database settings
DATABASE_PATH = DATA_DIR / "pr_pirate.db"

# Logging settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
