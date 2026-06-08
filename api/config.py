import os

from shared.env import load_project_env

load_project_env()

DB_NAME = os.environ.get("DB_NAME", "sustainable_meal_planner")
_mongo_host = os.environ.get("MONGO_HOST", "mongo")
_ro_user = os.environ.get("READONLY_USERNAME", "readonly")
_ro_pass = os.environ.get("READONLY_PASSWORD", "")
MONGO_URI = f"mongodb://{_ro_user}:{_ro_pass}@{_mongo_host}:27017/{DB_NAME}"
