import os
from pathlib import Path

from aiohttp import ClientTimeout

from shared.env import load_project_env

load_project_env()

RANDOM_ENDPOINT = "https://api.aniagotuje.pl/client/posts/random?category=&diet=&idea="
BASE_URL = "https://aniagotuje.pl"

REQUEST_CONCURRENCY = int(os.environ.get("REQUEST_CONCURRENCY", "3"))
REQUEST_TIMEOUT = ClientTimeout(total=int(os.environ.get("REQUEST_TIMEOUT_SECONDS", "30")))
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

SCRAPE_INTERVAL_MINUTES = int(os.environ.get("SCRAPE_INTERVAL_MINUTES", "5"))
URL_BATCH_CALLS = int(os.environ.get("URL_BATCH_CALLS", "5"))
MAX_PAGE_TEXT_CHARS = int(os.environ.get("MAX_PAGE_TEXT_CHARS", "10000"))

HTTP_MAX_RETRIES = int(os.environ.get("HTTP_MAX_RETRIES", "3"))
HTTP_BACKOFF_BASE_SECONDS = float(os.environ.get("HTTP_BACKOFF_BASE_SECONDS", "1.0"))

RECIPE_PARSER_MODEL = os.environ.get("RECIPE_PARSER_MODEL", "claude-sonnet-4-6")
INGREDIENT_ENRICHER_MODEL = os.environ.get(
    "INGREDIENT_ENRICHER_MODEL", "claude-haiku-4-5-20251001"
)

DB_NAME = os.environ.get("DB_NAME", "sustainable_meal_planner")
_mongo_host = os.environ.get("MONGO_HOST", "mongo")
_rw_user = os.environ.get("READWRITE_USERNAME", "readwrite")
_rw_pass = os.environ.get("READWRITE_PASSWORD", "")
MONGO_URI = f"mongodb://{_rw_user}:{_rw_pass}@{_mongo_host}:27017/{DB_NAME}"

_output_dir = os.environ.get("RECIPES_OUTPUT_DIR", "")
RECIPES_OUTPUT_DIR: Path | None = Path(_output_dir) if _output_dir else None

ANTHROPIC_API_KEY = (
    os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY") or ""
)
if not ANTHROPIC_API_KEY:
    raise RuntimeError(
        "ANTHROPIC_API_KEY (or CLAUDE_API_KEY) must be set for the scraper to run."
    )
