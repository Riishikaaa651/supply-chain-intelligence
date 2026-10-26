import os
from dotenv import load_dotenv
from groq import Groq
from src.database.db_connection import load_config, PROJECT_ROOT

# Read the API key from the .env file
load_dotenv(PROJECT_ROOT / ".env")


def get_client():
    cfg = load_config()["llm"]
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env")
    return Groq(api_key=api_key, timeout=cfg["timeout_seconds"])


def ask_llm(system_prompt, user_prompt):
    """Send one prompt to the LLM and return the answer text."""
    cfg = load_config()["llm"]
    client = get_client()
    response = client.chat.completions.create(
        model=cfg["model"],
        temperature=cfg["temperature"],
        max_tokens=cfg["max_tokens"],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content

import re
def format_answer(text):
    """Return the LLM answer with one sentence per line."""
    text = (text or "").strip()
    lines = [l.strip(" -•*\t") for l in text.splitlines() if l.strip()]
    if len(lines) <= 1:   # LLM wrote one paragraph, so split it by sentence
        lines = re.split(r"(?<=[.!?])\s+", text)
    return "\n".join(l for l in lines if l)