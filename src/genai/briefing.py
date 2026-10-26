from src.database import queries
from src.database.db_connection import get_connection, load_config
from src.genai.prompt_templates import build_prompt, format_lines
from src.genai.llm_client import ask_llm

# The 4 kinds of explanation we can generate
VALID_KINDS = ["delay_briefing", "delay_whatif", "shortage_briefing", "shortage_whatif"]


def _get_facts(kind, order_item_id):
    """Collect all facts the LLM needs from the database."""
    if kind.startswith("delay"):
        facts = queries.get_delay_facts(order_item_id)
        if facts is not None:
            facts.update(queries.get_delay_context())
    else:
        facts = queries.get_shortage_facts(order_item_id)
    return facts


def _cache_lookup(kind, key, version, question):
    """Return a saved answer if we already generated it, else None."""
    df = queries.run_query("""
        SELECT response FROM llm_briefings
        WHERE kind = ? AND entity_key = ? AND prompt_version = ?
          AND COALESCE(question, '') = ?
        ORDER BY id DESC LIMIT 1
    """, params=(kind, key, version, question or ""))
    return df.iloc[0]["response"] if len(df) else None


def _cache_save(kind, key, version, question, answer):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO llm_briefings (kind, entity_key, prompt_version, question, response) "
            "VALUES (?, ?, ?, ?, ?)",
            (kind, key, version, question, answer),
        )
        conn.commit()
    finally:
        conn.close()


def get_explanation(kind, order_item_id, question=None, use_cache=True):
    """Return {'text': ..., 'cached': True/False} for one order."""
    if kind not in VALID_KINDS:
        raise ValueError(f"kind must be one of {VALID_KINDS}")
    if kind.endswith("whatif") and not question:
        raise ValueError("A what-if explanation needs a question")

    version = load_config()["prompts"][f"active_{kind}_version"]
    key = str(order_item_id)

    # 1. Check the cache first
    if use_cache:
        saved = _cache_lookup(kind, key, version, question)
        if saved:
            return {"text": saved, "cached": True}

    # 2. Not saved yet: get facts, build prompt, call the LLM
    facts = _get_facts(kind, order_item_id)
    if facts is None:
        raise ValueError(f"No order found with order_item_id {order_item_id}")

    system, user = build_prompt(kind, facts, question)
    answer = format_lines(ask_llm(system, user))

    # A reasoning model can run out of tokens and return nothing
    if not answer.strip():
        raise ValueError("LLM returned an empty answer. Try a higher max_tokens in config.yaml")

    # 3. Save for next time
    _cache_save(kind, key, version, question, answer)
    return {"text": answer, "cached": False}