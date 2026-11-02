import os
import sqlite3
from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def load_config():
    with open(PROJECT_ROOT / "config.yaml") as f:
        return yaml.safe_load(f)

def get_connection():
    cfg = load_config()
    # DB_PATH (environment variable) overrides config.yaml. Used on the server,
    # where we point to the small deploy database.
    db_file = os.environ.get("DB_PATH") or cfg["paths"]["db"]
    db_path = PROJECT_ROOT / db_file          # an absolute path also works here
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)