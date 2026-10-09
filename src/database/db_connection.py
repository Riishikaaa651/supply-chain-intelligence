import sqlite3
from pathlib import Path
import yaml

# project root = 3 levels up from this file (src/database/db_connection.py)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

def load_config():
    with open(PROJECT_ROOT / "config.yaml") as f:
        return yaml.safe_load(f)


def get_connection():
    config = load_config()
    db_path = PROJECT_ROOT / config["paths"]["db"]
    return sqlite3.connect(db_path)