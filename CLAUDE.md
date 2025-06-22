# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Dependencies and Environment:**
```bash
# Install dependencies (uses uv package manager)
uv sync

# Set up environment variables (copy .env.example to .env and fill in values)
cp .env.example .env
# Edit .env to add your API keys

# Run the main script (generates TTS audio summary)
uv run python main.py

# Run with specific repositories
uv run python main.py --repos "huggingface/transformers,openai/openai-python"

# Run with predefined repository lists
uv run python main.py --repos llm        # Popular LLM repositories
uv run python main.py --repos genai      # Generative AI tools
uv run python main.py --repos llmops     # LLMOps and deployment tools

# Customize discovery and audio parameters
uv run python main.py --categories "llm,genai,nlp" --min-stars 50 --max-stars 10000 --max-repos 30 --voice "af_bella" --speed 1.2

# Speed up repository discovery, issue discovery, and assessment with parallel processing
uv run python main.py --max-workers 5 --voice "af_bella"

# Generate script only (skip TTS)
uv run python main.py --skip-tts --output-audio "my_summary.wav"

# Disable Discord notifications (for local testing)
uv run python main.py --no-discord
```

**Environment Setup:**
- Requires Python 3.11+
- Requires API tokens in `.env` file:
  - `GITHUB_TOKEN` for GitHub API access
  - `REPLICATE_API_TOKEN` for TTS generation
  - `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` for LLM assessment
  - `DISCORD_WEBHOOK_URL` for server notifications (optional)
  - `GOOGLE_DRIVE_CREDENTIALS_PATH` and `GOOGLE_DRIVE_FOLDER_ID` for file uploads (optional)
- Uses uv for dependency management (not pip/conda)

**Discord Webhook Setup (Optional):**
1. Create a Discord webhook in your server settings
2. Copy the webhook URL to your `.env` file
3. RepoRadio will send notifications for: start, LLM results, completion, errors
4. Audio files under 8MB will be uploaded to Discord (if no Google Drive)

**Google Drive Setup (Optional):**
1. Create a Google Cloud project and enable the Drive API
2. Create a service account and download the JSON credentials file
3. Create a Google Drive folder and get its folder ID from the URL
4. Set `GOOGLE_DRIVE_CREDENTIALS_PATH` and `GOOGLE_DRIVE_FOLDER_ID` in `.env`
5. Audio files of any size will be uploaded to Google Drive and shared via Discord link

## Architecture Overview

**Core Components:**
- **Discovery Engine** (`src/reporadio/discovery/`): GitHub API integration for repository and issue discovery
- **LLM Integration** (`src/reporadio/llm/`): Issue assessment using Claude/OpenAI APIs
- **TTS Integration** (`src/reporadio/tts/`): Text-to-speech using Replicate Kokoro model
- **Data Models** (`src/reporadio/models/`): Pydantic models for Repository, Issue, and Assessment entities
- **Database Layer** (`src/reporadio/utils/database.py`): SQLite-based persistence using SQLAlchemy
- **Configuration** (`config/`): Repository lists and filtering settings
- **Templates** (`src/reporadio/templates/`): Audio script generation templates
- **Notifications** (`src/reporadio/notifications/`): Discord webhook and Google Drive integration

**Key Design Patterns:**
- Uses PyGithub for GitHub API interactions with built-in rate limiting and retry logic
- Pydantic models for data validation and serialization
- Rich console library for CLI output and user experience
- Tenacity for robust retry mechanisms on API calls
- Modular architecture separating discovery, models, and utilities

**Database Schema:**
- SQLite database stored at `data/reporadio.db`
- Tracks discovered repositories and issues to avoid duplicates
- Repository filtering based on stars, activity, language, and topics

**Configuration System:**
- `config/settings.py`: Core configuration with topic categories, filtering criteria
- `config/repo_lists.py`: Predefined repository lists by category (llm, genai, llmops, ml, nlp)
- Supports both topic-based discovery and explicit repository targeting

**Repository Discovery Logic:**
- Searches GitHub by topics defined in TARGET_TOPICS
- Filters by stars (10-10,000), language support, activity (180 days), and issue availability
- Deduplicates repositories and respects API rate limits

**Issue Discovery Logic:**
- Prioritizes issues with labels: "good first issue", "bug", "enhancement", "help wanted"
- Filters out issues with problematic labels: "wontfix", "invalid", "discussion"
- Age filtering: between 1-365 days old
- Limits to 20 issues per repository

## Current Implementation Status

This project has evolved from issue discovery to **TTS Audio Summary Generation** - it discovers GitHub issues, assesses them with LLMs, and generates audio summaries for listening on-the-go.

**Working Features:**
- GitHub repository discovery by topics or specific repo lists
- Parallel repository search across multiple topics
- Parallel issue discovery across multiple repositories
- Issue filtering and prioritization with advanced scoring
- Parallel LLM-based issue assessment (difficulty, complexity, feasibility)
- TTS audio generation using Replicate's Kokoro model
- Rich CLI interface with progress indicators and previews
- Discord webhook notifications for server deployment monitoring
- Google Drive integration for reliable audio file sharing
- Rate limit handling and API error recovery
- Environment-based configuration with `.env` support

**Audio Workflow:**
1. **Discovery**: Find repositories and extract top issues
2. **Assessment**: LLM evaluates each issue for difficulty and clarity
3. **Ranking**: Issues sorted from easiest to hardest
4. **Script Generation**: Creates TTS-friendly narrative
5. **Audio Synthesis**: Replicate Kokoro TTS creates audio file

**CLI Options:**
- `--output-audio PATH`: Custom audio file location
- `--voice VOICE`: Choose TTS voice (af_bella, af_nicole, af_sarah, etc.)
- `--speed FLOAT`: Adjust speech speed (0.5-2.0)  
- `--max-workers INT`: Parallel workers for repository search, issue discovery, and LLM assessment (default: 3)
- `--skip-tts`: Generate script only, skip audio creation
- `--no-discord`: Disable Discord notifications (useful for local testing)