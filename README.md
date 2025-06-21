# 🏴‍☠️ PR Pirate

Automated GitHub issue discovery and fixing using AI. This tool crawls GitHub for issues on LLM/GenAI repositories, assesses their difficulty using AI, and attempts to automatically fix them.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- GitHub Personal Access Token
- uv package manager

### Installation

1. **Install uv** (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Clone and setup**:
```bash
git clone <repo-url>
cd pr-pirate
```

3. **Install dependencies**:
```bash
uv sync
```

4. **Set up GitHub token**:
```bash
export GITHUB_TOKEN=your_github_token_here
```

### Testing the Discovery Phase

Run the discovery phase to find repositories and issues:

```bash
uv run python main.py
```

This will:
- 🔍 Search GitHub for LLM/GenAI repositories
- 📊 Filter repositories based on activity, stars, and language
- 🎯 Find suitable issues in top repositories
- 📋 Display a summary of discovered issues

## 🏗️ Project Structure

```
pr-pirate/
├── src/pr_pirate/
│   ├── discovery/          # GitHub discovery engines
│   ├── models/            # Data models (Repository, Issue, etc.)
│   └── utils/             # Database and utility functions
├── config/                # Configuration settings
├── tests/                 # Test files
├── main.py               # CLI entry point
└── pyproject.toml        # Project configuration
```

## 🎯 Features (Discovery Phase)

### Repository Discovery
- **Topic-based search**: Targets LLM, GenAI, LLMOps repositories
- **Smart filtering**: Stars, activity, language, issue count
- **Rate limiting**: Respects GitHub API limits
- **Deduplication**: Removes duplicate repositories

### Issue Discovery  
- **Label-based filtering**: Prioritizes "good first issue", "bug", etc.
- **Quality assessment**: Filters by age, description quality, complexity indicators
- **Priority scoring**: Ranks issues by feasibility and impact
- **Batch processing**: Efficiently processes multiple repositories

## 🔧 Configuration

Edit `config/settings.py` to customize:

- **Target topics**: Add/remove GitHub topics to search
- **Languages**: Supported programming languages  
- **Filtering criteria**: Stars, activity thresholds
- **Issue preferences**: Label preferences, age limits

## 📊 Example Output

```
🏴‍☠️ PR Pirate - Discovery Phase

🔧 Initializing components...
✓ GitHub client initialized
Rate Limits:
  Core: 4852/5000 (resets at 2024-01-15 15:30:00)
  Search: 29/30 (resets at 2024-01-15 14:35:00)

🔍 Starting repository discovery...
✓ Found 15 repositories

🎯 Starting issue discovery...
✓ Found 23 suitable issues

🎉 Discovery Complete!
  • Found 15 repositories  
  • Found 23 suitable issues

🏆 Top Issues:
  1. [langchain-ai/langchain] #1234: Fix memory leak in chat history
  2. [openai/openai-python] #567: Add retry logic for rate limits
  ...
```

## 🚧 Coming Next

- **LLM Assessment**: Claude-based difficulty scoring
- **Repository Management**: Automated forking and cloning
- **Code Fixing**: AI-powered issue resolution
- **PR Generation**: Automated pull request creation

## 🤝 Contributing

This is an active development project. Current focus is on the discovery phase implementation.

## 📝 License

MIT License - see LICENSE file for details.
