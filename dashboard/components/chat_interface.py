import requests
import streamlit as st

from src.database.db_connection import load_config

_cfg = load_config()["api"]
API = f"http://{_cfg['host']}:{_cfg['port']}"
TIMEOUT = 90          # the LLM can be slow, so wait up to 90 seconds


@st.cache_data(ttl=300)
def preset_questions(risk_type):
    r = requests.get(f"{API}/whatif/questions", params={"risk_type": risk_type}, timeout=10)
    r.raise_for_status()
    return r.json()["questions"]


def post_api(path, payload):
    """Call the API. Returns (data, error_message); one of them is always None."""
    try:
        r = requests.post(f"{API}{path}", json=payload, timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json(), None
        try:
            detail = r.json().get("detail", r.text)
        except ValueError:
            detail = r.text
        return None, f"API error {r.status_code}: {detail}"
    except requests.exceptions.RequestException as e:
        return None, f"Could not reach the API: {e}"