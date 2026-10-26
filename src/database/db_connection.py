import sqlite3
from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def load_config():
    with open(PROJECT_ROOT / "config.yaml") as f:
        return yaml.safe_load(f)

def get_connection():
    cfg = load_config()
    db_path = PROJECT_ROOT / cfg["paths"]["db"]
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)