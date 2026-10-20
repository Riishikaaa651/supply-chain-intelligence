import os
from dotenv import load_dotenv
from groq import Groq

from src.database.db_connection import load_config, PROJECT_ROOT

load_dotenv(PROJECT_ROOT / ".env")


def get_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found. Check your .env file.")
    timeout = load_config()["llm"]["timeout_seconds"]
    return Groq(api_key=api_key, timeout=timeout)


def ask_llm(user_prompt, system_prompt="You are a supply chain analyst.", **overrides):
    cfg = load_config()["llm"]
    client = get_client()

    response = client.chat.completions.create(
        model=overrides.get("model", cfg["model"]),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=overrides.get("temperature", cfg["temperature"]),
        max_tokens=overrides.get("max_tokens", cfg["max_tokens"]),
    )
    return response.choices[0].message.content