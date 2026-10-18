"""Central configuration. Values come from environment variables first,
then from Streamlit secrets (.streamlit/secrets.toml)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("TASKFLOW_DATA_DIR", ROOT / "data"))
DB_PATH = DATA_DIR / "taskflow.db"
ASSETS = ROOT / "assets"
APP_NAME = "TaskFlow"
COOKIE = "tf_session"
SESSION_DAYS = 30


def get(name: str, default: str = "") -> str:
    val = os.getenv(name)
    if val:
        return val
    try:  # works in the main thread and in the background scheduler
        import streamlit as st
        return str(st.secrets.get(name, default))
    except Exception:
        return default


def flag(name: str, default: bool = False) -> bool:
    return get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}
