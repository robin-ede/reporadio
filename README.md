# 📻 RepoRadio - GitHub Issue Audio Summaries

**Discover GitHub issues and generate TTS audio summaries for listening on-the-go.**

RepoRadio transforms GitHub issue discovery into an audio experience. It finds interesting open-source issues, assesses them with AI, and creates audio summaries perfect for your commute home from work.

## 🎯 Perfect for Developers Who Want To

- **Stay informed** about interesting GitHub issues while commuting
- **Discover contribution opportunities** in popular open-source projects  
- **Learn about new projects** through curated issue summaries
- **Multitask effectively** by consuming developer content during travel time

## 🎧 How It Works

1. **Discovery**: Searches GitHub for repositories in categories like LLM, GenAI, MLOps
2. **Filtering**: Finds high-quality issues labeled "good first issue", "bug", "enhancement"  
3. **AI Assessment**: Uses Claude/OpenAI to evaluate issue difficulty and complexity
4. **Audio Generation**: Creates TTS summaries using Replicate's Kokoro model
5. **Broadcasting**: Sends audio files via Discord webhook with Google Drive backup

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- API tokens (see [Environment Setup](#environment-setup))

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/reporadio.git
cd reporadio

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env to add your API keys
```

### Basic Usage

```bash
# Generate audio summary for LLM and GenAI issues
uv run python main.py

# Use specific voice and speed
uv run python main.py --voice af_bella --speed 1.2

# Target specific repositories
uv run python main.py --repos "huggingface/transformers,openai/openai-python"

# Use predefined repository lists
uv run python main.py --repos llm        # Popular LLM repos
uv run python main.py --repos genai      # Generative AI tools
uv run python main.py --repos llmops     # LLMOps platforms
```

## 🔧 Environment Setup

Create a `.env` file with the following tokens:

```bash
# Required: GitHub API access
GITHUB_TOKEN=your_github_token_here

# Required: TTS generation
REPLICATE_API_TOKEN=your_replicate_token_here

# Required: AI assessment (choose one)
ANTHROPIC_API_KEY=your_anthropic_key_here
# OR
OPENAI_API_KEY=your_openai_key_here

# Optional: Server notifications
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_url_here

# Optional: Large file sharing
GOOGLE_DRIVE_CREDENTIALS_PATH=/path/to/service-account-credentials.json
GOOGLE_DRIVE_FOLDER_ID=your_google_drive_folder_id_here
```

### Getting API Keys

- **GitHub Token**: [Personal Access Tokens](https://github.com/settings/tokens)
- **Replicate Token**: [Replicate Dashboard](https://replicate.com/account)
- **Anthropic Key**: [Anthropic Console](https://console.anthropic.com/)
- **OpenAI Key**: [OpenAI API Keys](https://platform.openai.com/api-keys)

## 📱 Discord Integration

Set up Discord webhooks for server deployment monitoring:

1. Create a Discord webhook in your server settings
2. Copy the webhook URL to your `.env` file
3. RepoRadio will send notifications for:
   - ✅ Process start with repository count
   - 🧠 LLM assessment results with top 10 issues
   - 🎤 Audio completion with download links
   - ❌ Error notifications if something fails

Audio files under 8MB are uploaded directly to Discord. Larger files use Google Drive with embedded links.

## ☁️ Google Drive Setup (Optional)

For reliable sharing of large audio files:

1. Create Google Cloud project and enable Drive API
2. Create service account and download JSON credentials
3. Share your target Drive folder with the service account email
4. Set credentials path and folder ID in `.env`

## 🎵 Audio Customization

### Available Voices
- `af_bella` (default) - Clear female voice
- `af_nicole` - Alternative female voice  
- `af_sarah` - Another female option
- Plus male voices: `am_adam`, `am_michael`

### Speed Control
- Range: 0.5x to 2.0x speed
- Default: 1.15x (slightly faster than normal)
- Perfect for commute listening

### Example Commands

```bash
# Slow and clear for complex topics
uv run python main.py --voice af_bella --speed 0.9

# Fast overview for quick consumption  
uv run python main.py --voice af_nicole --speed 1.5

# Skip audio generation, just get the script
uv run python main.py --skip-tts
```

## 🏃‍♂️ Performance Optimization

Speed up execution with parallel processing:

```bash
# Use 5 parallel workers for faster discovery
uv run python main.py --max-workers 5

# Disable Discord for local testing
uv run python main.py --no-discord
```

## 📊 Repository Categories

### Predefined Lists
- **llm**: Large language model projects
- **genai**: Generative AI tools and frameworks  
- **llmops**: LLM deployment and monitoring
- **ml**: General machine learning projects
- **nlp**: Natural language processing libraries

### Topic-Based Discovery
Automatically discovers repositories by GitHub topics:
- `machine-learning`, `artificial-intelligence`
- `llm`, `large-language-models`, `generative-ai`
- `pytorch`, `tensorflow`, `huggingface`
- `mlops`, `model-deployment`

## 🎯 Issue Prioritization

### Scoring Algorithm
Issues are ranked by composite score considering:
- **Label quality**: "good first issue" > "bug" > "enhancement"
- **Age factor**: Recent but not brand new (1-365 days)
- **Engagement**: Comments and reactions
- **Repository health**: Stars, activity, maintenance

### AI Assessment
Each issue is evaluated for:
- **Difficulty**: Easy/Medium/Hard classification
- **Clarity**: How well-defined the problem is
- **Feasibility**: Likelihood of successful contribution
- **Learning value**: Educational benefit for developers

## 🤖 Perfect for Daily Automation

**Ideal workflow for busy developers:**

1. **Schedule** PR Pirate to run at end of workday
2. **Commute** home while listening to curated issue summaries  
3. **Bookmark** interesting issues mentioned in the audio
4. **Contribute** to projects that caught your attention

Set up a cron job or GitHub Action to generate fresh audio summaries:

```bash
# Daily at 5 PM
0 17 * * * cd /path/to/reporadio && uv run python main.py --voice af_bella
```

## 🛠️ Advanced Usage

### Repository Filtering

```bash
# Focus on smaller, manageable projects
uv run python main.py --min-stars 50 --max-stars 1000 --max-repos 15

# Target specific categories with custom limits
uv run python main.py --categories "llm,nlp" --max-issues-per-repo 3
```

### Development Commands

```bash
# Generate script only (no TTS)
uv run python main.py --skip-tts --output-audio "my_summary.wav"

# Test Google Drive connectivity
uv run python test_google_drive.py

# Full parallel execution with Discord notifications
uv run python main.py --max-workers 5 --voice af_bella
```

## 📁 Project Structure

```
reporadio/
├── src/pr_pirate/
│   ├── discovery/          # GitHub API integration
│   ├── llm/               # AI assessment (Claude/OpenAI)
│   ├── tts/               # Text-to-speech (Replicate)
│   ├── models/            # Data models (Pydantic)
│   ├── notifications/     # Discord & Google Drive
│   ├── templates/         # Audio script generation
│   └── utils/             # Database & utilities
├── config/                # Repository lists & settings
├── data/                  # SQLite database
└── main.py               # Radio station entry point
```

## 🚨 Rate Limits & Best Practices

- **GitHub API**: 5,000 requests/hour (authenticated)
- **Replicate TTS**: Pay-per-use model
- **LLM APIs**: Respect provider rate limits
- **Parallel processing**: Default 3 workers, increase carefully

## 🤝 Contributing

Issues and pull requests welcome! This project is perfect for:
- Adding new TTS voices or providers
- Improving issue scoring algorithms  
- Supporting additional notification channels
- Enhancing repository discovery logic

## 📄 License

MIT License - Feel free to use and modify for your own commute audio summaries!

---

**Made for developers who optimize everything, including their commute time.** 🚶‍♂️📻
