# twitter-voice-mcp

An MCP server that generates tweets in your unique voice and manages drafts for Twitter/X.

## Features

- **Voice Analysis**: Analyze your Twitter/X voice from existing tweets or custom text
- **AI-Powered Tweet Generation**: Generate new tweets in your voice about any topic
- **Draft Management**: Create, review, and post tweet drafts
- **Retweet Drafts**: Generate voice-aligned comments for quote tweeting
- **Image Tweet Generation**: Automatically generate tweets for images in a folder
- **Multi-AI Support**: Works with Gemini, OpenAI, or Anthropic models

## Installation

### Prerequisites

- Python 3.10+
- Twitter/X API credentials (Bearer Token)
- AI API key (Gemini, OpenAI, or Anthropic)

### Setup

```bash
# Clone and navigate to directory
git clone <repo-url> twitter-voice-mcp
cd twitter-voice-mcp

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy env template and add your credentials
cp .env.example .env
# Edit .env with your API keys
```

### Environment Variables

```
GEMINI_API_KEY=your-gemini-key
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
TWITTER_BEARER_TOKEN=your-twitter-bearer-token
```

## MCP Client Installation

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "twitter-voice-mcp": {
      "command": "python",
      "args": [
        "/absolute/path/to/twitter-voice-mcp/src/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your-key",
        "TWITTER_BEARER_TOKEN": "your-token"
      }
    }
  }
}
```

### Docker

```dockerfile
FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src /app/src
CMD ["python", "src/server.py"]
```

## Available Tools

- `configure_ai_model` - Set AI provider and model
- `analyze_my_voice` - Analyze voice from tweets
- `import_voice_profile` - Import pre-analyzed profile
- `analyze_from_file` - Analyze voice from text file
- `generate_draft_tweets` - Generate tweets on a topic
- `generate_retweet_drafts` - Generate quote tweet comments
- `list_pending_drafts` - View all draft tweets
- `approve_and_post_draft` - Post approved draft to Twitter
- `export_drafts_csv` - Export drafts to CSV
- `scan_and_draft_tweets_from_images` - Auto-generate tweets from images

## License

MIT
