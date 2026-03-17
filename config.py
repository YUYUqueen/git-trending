import os
from pathlib import Path

# Load .env file if it exists
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

# API tokens
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITEE_TOKEN = os.getenv("GITEE_TOKEN", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Storage
DB_PATH = os.getenv("DB_PATH", "data/trending.db")

# Retry
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1  # seconds
