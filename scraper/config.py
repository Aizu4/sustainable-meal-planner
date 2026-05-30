import os
from pathlib import Path

import aiohttp

# Load .env from project root (if present) without requiring python-dotenv
_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

RANDOM_ENDPOINT = "https://api.aniagotuje.pl/client/posts/random?category=&diet=&idea="
BASE_URL = "https://aniagotuje.pl"

REQUEST_CONCURRENCY = 3
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

SCRAPE_INTERVAL_MINUTES: int = int(os.environ.get("SCRAPE_INTERVAL_MINUTES", "5"))

DB_NAME: str = os.environ.get("DB_NAME", "sustainable_meal_planner")
_mongo_host = os.environ.get("MONGO_HOST", "mongo")
_rw_user = os.environ.get("READWRITE_USERNAME", "readwrite")
_rw_pass = os.environ.get("READWRITE_PASSWORD", "")
MONGO_URI: str = f"mongodb://{_rw_user}:{_rw_pass}@{_mongo_host}:27017/{DB_NAME}"

# Optional: if set, JSON files are written here in addition to MongoDB
_output_dir = os.environ.get("RECIPES_OUTPUT_DIR", "")
RECIPES_OUTPUT_DIR: Path | None = Path(_output_dir) if _output_dir else None

# Supports either ANTHROPIC_API_KEY (standard) or CLAUDE_API_KEY
ANTHROPIC_API_KEY: str = (
    os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY") or ""
)
