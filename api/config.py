import os
from pathlib import Path

_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

DB_NAME: str = os.environ.get("DB_NAME", "sustainable_meal_planner")
_mongo_host = os.environ.get("MONGO_HOST", "mongo")
_ro_user = os.environ.get("READONLY_USERNAME", "readonly")
_ro_pass = os.environ.get("READONLY_PASSWORD", "")
MONGO_URI: str = f"mongodb://{_ro_user}:{_ro_pass}@{_mongo_host}:27017/{DB_NAME}"
