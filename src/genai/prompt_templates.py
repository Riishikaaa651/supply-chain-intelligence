import re

from src.database.db_connection import load_config

SYSTEM_PROMPT = (
    "You are a supply chain analyst assistant writing for a logistics manager. "
    "Use ONLY the numbers given to you. Never invent numbers. Keep answers short and plain."
)

PROMPTS = {
    # ---------------- DELAY ----------------
    "delay_briefing": {
        "v1": """Order details:
- Shipping mode: {shipping_mode}
- Region: {order_region}
- Category: {category_name}
- Predicted delay probability: {delay_prob:.0%}
- Risk level: {risk_level}

Historical numbers (from orders before this one):
- Shipping mode average delay: {mode_avg_delay:.2f} days (std {mode_delay_std:.2f}), reliability score {mode_reliability_score:.2f}
- Region average delay: {region_avg_delay:.2f} days (std {region_delay_std:.2f}), reliability score {region_reliability_score:.2f}

Write a briefing in exactly 3 short sentences:
1. State the risk level and the delay probability.
2. Explain the main reason, using the numbers above.
3. Suggest one practical action.""",

        "v2": """Order details:
- Shipping mode: {shipping_mode}, Region: {order_region}, Category: {category_name}
- Predicted delay probability: {delay_prob:.0%}
- Risk level: {risk_level} (Low = below 45%, Medium = 45% to 75%, High = above 75%)

Context from history:
- Across all past orders, {overall_late_pct}% were delivered late.
- Late rate by shipping mode: {mode_table}.
- This order's shipping mode had an average delay of {mode_avg_delay:.2f} days (std {mode_delay_std:.2f}).
- This order's region had an average delay of {region_avg_delay:.2f} days (std {region_delay_std:.2f}).

Write exactly 3 short sentences:
1. State the risk level and delay probability, and say whether it is below or above the overall late rate.
2. Explain the main reason using the shipping mode and region numbers. Your explanation must match the risk level (never say something raises the risk if the level is Low).
3. Suggest one practical action.""",

        "v3": """Order details:
- Shipping mode: {shipping_mode}, Region: {order_region}, Category: {category_name}
- Predicted delay probability: {delay_prob:.0%}
- Risk level: {risk_level} (Low = below 45%, Medium = 45% to 75%, High = above 75%)

Context from history:
- Across all past orders, {overall_late_pct}% were delivered late.
- Late rate by shipping mode: {mode_table}.
- This order's shipping mode had an average delay of {mode_avg_delay:.2f} days (std {mode_delay_std:.2f}).
- This order's region had an average delay of {region_avg_delay:.2f} days (std {region_delay_std:.2f}).

Write exactly 3 lines. Each line is one short sentence. No bullets, no numbering, no blank lines.
Line 1: State the risk level and delay probability, and say whether it is below or above the overall late rate.
Line 2: Explain the main reason using the shipping mode and region numbers. It must match the risk level (never say something raises the risk if the level is Low).
Line 3: Suggest one practical action.""",
    },

    "delay_whatif": {
        "v1": """Order details:
- Shipping mode: {shipping_mode}, Region: {order_region}, Category: {category_name}
- Predicted delay probability: {delay_prob:.0%} (risk level: {risk_level})
- Shipping mode average delay: {mode_avg_delay:.2f} days, region average delay: {region_avg_delay:.2f} days

Manager's what-if question: {question}

Answer in at most 4 sentences. Explain in simple words how the change would likely affect the delay risk, based on the numbers above.
Do NOT give a new probability number. Say the model must be re-run for an exact value.""",

        "v2": """Order details:
- Shipping mode: {shipping_mode}, Region: {order_region}
- Predicted delay probability: {delay_prob:.0%} (risk level: {risk_level})
- Overall late rate across all past orders: {overall_late_pct}%
- Late rate by shipping mode: {mode_table}

Manager's what-if question: {question}

Answer in at most 4 sentences. Compare using the late rates by shipping mode above.
Do NOT give a new probability for this order. Say the model must be re-run for an exact value.""",

        "v3": """Order details:
- Shipping mode: {shipping_mode}, Region: {order_region}
- Predicted delay probability: {delay_prob:.0%} (risk level: {risk_level})
- Overall late rate across all past orders: {overall_late_pct}%
- Late rate by shipping mode: {mode_table}

Manager's what-if question: {question}

Write at most 4 lines. Each line is one short sentence. No bullets, no numbering, no blank lines.
Use the late rates by shipping mode above to compare the current mode with the new one, and compare both with the overall late rate.
Do NOT give a new probability for this order. In the last line say the model must be re-run for an exact value.""",

        "v4": """Order details:
- Shipping mode: {shipping_mode}, Region: {order_region}
- Predicted delay probability: {delay_prob:.0%} (risk level: {risk_level})
- Overall late rate across all past orders: {overall_late_pct}%
- Late rate by shipping mode: {mode_table}
- Late rate by region: {region_table}
- This order's shipping mode average delay: {mode_avg_delay:.2f} days (std {mode_delay_std:.2f})

Manager's what-if question: {question}

Write at most 4 lines. Each line is one short sentence. No bullets, no numbering, no blank lines.
Rules:
- If the question is about another shipping mode or region, compare the late rates from the lists above (current vs new, and vs the overall rate). If the new one is the same as the current one, say the order already uses it.
- If the question is about extra days of delay, compare the extra days with the delay std above. Do not link days to another shipping mode.
- If the question cannot be answered from the numbers above, say so in one line instead of guessing.
- Do NOT give a new probability for this order. In the last line say the model must be re-run for an exact value.""",
    },

    # ---------------- SHORTAGE ----------------
    "shortage_briefing": {
        "v1": """Product details:
- Product: {product_name} (category: {category_name})
- Shortage risk score: {shortage_prob:.2f} (higher = riskier). This is a ranking score, NOT a probability.
- Risk level: {risk_level}

Demand numbers (history before this order):
- Average demand: {product_demand_mean:.1f} units, std {product_demand_std:.1f}
- This order's quantity deviation: {qty_deviation:.2f}
- Past orders of this product: {product_order_history_count}

Write a briefing in exactly 3 short sentences:
1. State the risk level. Do NOT call the score a percentage or a probability.
2. Explain the main reason, using the demand numbers above.
3. Suggest one practical action (for example about stock or reordering).""",

        "v2": """Product details:
- Product: {product_name} (category: {category_name})
- Shortage risk score: {shortage_prob:.2f}. This is a ranking score, NOT a probability.
- Risk level: {risk_level} (High = top 10% of all orders by score, Medium = next 20%, Low = rest)

Demand numbers (history before this order):
- Average demand: {product_demand_mean:.1f} units, std {product_demand_std:.1f}
- This order's quantity deviation: {qty_deviation:.2f}
- Past orders of this product in the data: {product_order_history_count}

Write exactly 3 short sentences:
1. State the risk level. Do NOT call the score a percentage or a probability.
2. Explain the main reason using the demand numbers. If past orders are fewer than 5, say the history is limited so the score is less reliable.
3. Suggest one practical action about stock or reordering.""",

        "v3": """Product details:
- Product: {product_name} (category: {category_name})
- Shortage risk score: {shortage_prob:.2f}. This is a ranking score, NOT a probability.
- Risk level: {risk_level} (High = top 10% of all orders by score, Medium = next 20%, Low = rest)

Demand numbers (history before this order):
- Average demand: {product_demand_mean:.1f} units, std {product_demand_std:.1f}
- This order's quantity deviation: {qty_deviation:.2f}
- Past orders of this product in the data: {product_order_history_count}

Write exactly 3 lines. Each line is one short sentence. No bullets, no numbering, no blank lines.
Line 1: State the risk level. Do NOT call the score a percentage or a probability.
Line 2: Explain the main reason using the demand numbers. If past orders are fewer than 5, say the history is limited so the score is less reliable.
Line 3: Suggest one practical action about stock or reordering. Do not invent quantities or time periods (like days or months). You may use the standard deviation as a buffer.""",
    },

    "shortage_whatif": {
        "v1": """Product details:
- Product: {product_name} (category: {category_name})
- Shortage risk score: {shortage_prob:.2f} (ranking score, NOT a probability), risk level: {risk_level}
- Average demand: {product_demand_mean:.1f} units, std {product_demand_std:.1f}

Manager's what-if question: {question}

Answer in at most 4 sentences. Explain in simple words how the change would likely affect shortage risk, based on the numbers above.
Do NOT give a new score or percentage. Say the model must be re-run for an exact value.""",

        "v2": """Product details:
- Product: {product_name} (category: {category_name})
- Shortage risk score: {shortage_prob:.2f} (ranking score, NOT a probability), risk level: {risk_level}
- Average demand: {product_demand_mean:.1f} units, std {product_demand_std:.1f}

Manager's what-if question: {question}

Answer in at most 4 sentences using only the demand numbers above.
We have NO data about supply, lead time or capacity, so do not mention them.
Do NOT give a new score or percentage. Say the model must be re-run for an exact value.""",

        "v3": """Product details:
- Product: {product_name} (category: {category_name})
- Shortage risk score: {shortage_prob:.2f} (ranking score, NOT a probability), risk level: {risk_level}
- Average demand: {product_demand_mean:.1f} units, std {product_demand_std:.1f}

Manager's what-if question: {question}

Write at most 4 lines. Each line is one short sentence. No bullets, no numbering, no blank lines.
You may do simple arithmetic on the average demand (for example the new demand after the change) and compare the change with the standard deviation.
We have NO data about supply, lead time or capacity, so do not mention them.
Do NOT give a new score or percentage. In the last line say the model must be re-run for an exact value.""",

        "v4": """Product details:
- Product: {product_name} (category: {category_name})
- Shortage risk score: {shortage_prob:.2f} (ranking score, NOT a probability), risk level: {risk_level}
- Average demand: {product_demand_mean:.1f} units, std {product_demand_std:.1f}

Manager's what-if question: {question}

Write at most 4 lines. Each line is one short sentence. No bullets, no numbering, no blank lines.
Rules:
- You may do simple arithmetic on the average demand and compare the change with the standard deviation.
- In one line, say whether the change would likely raise or lower the shortage risk (more demand means more risk, less demand means less risk). Use the word "likely".
- We have NO data about supply, lead time or capacity, so do not mention them.
- Do NOT give a new score or percentage. In the last line say the model must be re-run for an exact value.""",
    },
}


def build_prompt(kind, facts, question=None, version=None):
    """Version comes from config.yaml unless you pass one (useful for testing)."""
    version = version or load_config()["prompts"][f"active_{kind}_version"]
    template = PROMPTS[kind][version]
    user_prompt = template.format(**facts, question=question or "")
    return SYSTEM_PROMPT, user_prompt


def format_lines(text):
    """Put every sentence on its own line, so the answer is easy to read.

    If the LLM already wrote one sentence per line we keep that.
    If it wrote everything in one paragraph, we split it at sentence ends.
    """
    text = (text or "").strip()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if len(lines) <= 1:
        lines = re.split(r"(?<=[.!?])\s+", text)
    # remove leading bullets or numbers like "1." or "-" if the LLM added them
    lines = [re.sub(r"^(\d+[.)]\s*|[-*•]\s*)", "", ln).strip() for ln in lines]
    return "\n".join(ln for ln in lines if ln)