SYSTEM_PROMPT=(
    "You are a supply chain risk analyst writing for an operations manager."
    "Use ONLY the numbers given to you. Never invent figures or causes."
)
BRIEFING_V1="""Write a short risk briefing from this data.
Shipping mode performance:
{mode_table}
highest-risk region and shipping mode combinations:
{region_table}
Write the briefing now."""

def build_briefing_prompt(mode_df, region_df, version="v1"):
    templates={"v1": BRIEFING_V1}
    return templates[version].format(
        mode_table=mode_df.to_string(index=False),
        region_table=region_df.head(5).to_string(index=False),
    )

SYSTEM_PROMPT = (
    "You are a supply chain risk analyst writing for an operations manager. "
    "Use ONLY the numbers given to you. Never invent figures or causes."
)

BRIEFING_V1 = """Write a short risk briefing from this data.

Shipping mode performance:
{mode_table}

Highest-risk region and shipping mode combinations:
{region_table}

Write the briefing now."""

BRIEFING_V2 = """Write a risk briefing for an operations manager.

DATA
Shipping mode performance:
{mode_table}

PRE-CALCULATED FACTS (use these exactly; do not calculate anything yourself):
{facts}

RULES
- Use only numbers that appear above. Do no arithmetic.
- 'Late' means delivered after the scheduled date.
- Do not repeat the tables.
- Under 150 words.

FORMAT
Headline: one sentence.
Key risks: exactly 3 bullets, each containing a number.
Recommended actions: exactly 2 bullets.
"""


def build_facts(mode_df, region_df):
    worst = mode_df.sort_values("late_pct", ascending=False).iloc[0]
    best = mode_df.sort_values("late_pct").iloc[0]
    gap = worst.avg_real_days - worst.avg_scheduled_days
    total = int(mode_df.total_orders.sum())
    overall_late = (mode_df.total_orders * mode_df.late_pct).sum() / total
    n_100 = int((region_df.late_pct == 100).sum())

    return "\n".join([
        f"- Worst mode: {worst.shipping_mode} ({worst.late_pct}% late; "
        f"promised {worst.avg_scheduled_days} days, actual {worst.avg_real_days} days, "
        f"gap {gap:.2f} days)",
        f"- Best mode: {best.shipping_mode} ({best.late_pct}% late)",
        f"- Overall late rate across {total:,} order items: {overall_late:.1f}%",
        f"- {n_100} region/mode combinations are 100% late, so the problem is "
        f"not specific to one region",
    ])


def build_briefing_prompt(mode_df, region_df, version="v1"):
    if version == "v1":
        return BRIEFING_V1.format(
            mode_table=mode_df.to_string(index=False),
            region_table=region_df.head(5).to_string(index=False),
        )
    if version == "v2":
        return BRIEFING_V2.format(
            mode_table=mode_df.to_string(index=False),
            facts=build_facts(mode_df, region_df),
        )
    raise ValueError(f"Unknown version: {version}")

SYSTEM_PROMPT = (
    "You are a supply chain risk analyst writing for an operations manager. "
    "Use ONLY the numbers given to you. Never invent figures or causes."
)

BRIEFING_V1 = """Write a short risk briefing from this data.

Shipping mode performance:
{mode_table}

Highest-risk region and shipping mode combinations:
{region_table}

Write the briefing now."""

BRIEFING_V2 = """Write a risk briefing for an operations manager.

DATA
Shipping mode performance:
{mode_table}

PRE-CALCULATED FACTS (use these exactly; do not calculate anything yourself):
{facts}

RULES
- Use only numbers that appear above. Do no arithmetic.
- 'Late' means delivered after the scheduled date.
- Do not repeat the tables.
- Under 150 words.

FORMAT
Headline: one sentence.
Key risks: exactly 3 bullets, each containing a number.
Recommended actions: exactly 2 bullets.
"""

BRIEFING_V3 = """Write a risk briefing for an operations manager.

DATA
Shipping mode performance:
{mode_table}

PRE-CALCULATED FACTS (use these exactly; do not calculate anything yourself):
{facts}

RULES
- Use only numbers that appear above. Do no arithmetic.
- 'Late' means delivered after the scheduled date.
- Do not repeat the tables.
- List risks from worst to best and cover the two worst modes. Never list the best mode as a risk.
- Explain the cause using promised days vs actual days. Do not guess any other cause.
- Every recommended action must follow directly from a number above.
- Write percentages like 39.8% (no space before %).
- Under 150 words.

STYLE EXAMPLE (fictional numbers, for format only; never reuse them)
Headline: Mode A misses its promise on nearly every order, lifting overall lateness to 61.0%.
Key risks:
- Mode A: 95.0% late; promised 1.0 days, actual 2.1 days.
- Mode B: 70.2% late; promised 2.0 days, actual 3.5 days.
- Overall late rate is 61.0% across 50,000 order items.
Recommended actions:
- Extend Mode A's promised delivery window to match its 2.1-day actual time.
- Review Mode B's 2.0-day promise against its 3.5-day actual time.

NOW WRITE THE BRIEFING FOR THE REAL DATA ABOVE.
"""


def build_facts(mode_df, region_df):
    worst = mode_df.sort_values("late_pct", ascending=False).iloc[0]
    best = mode_df.sort_values("late_pct").iloc[0]
    gap = worst.avg_real_days - worst.avg_scheduled_days
    total = int(mode_df.total_orders.sum())
    overall_late = (mode_df.total_orders * mode_df.late_pct).sum() / total
    n_100 = int((region_df.late_pct == 100).sum())

    return "\n".join([
        f"- Worst mode: {worst.shipping_mode} ({worst.late_pct}% late; "
        f"promised {worst.avg_scheduled_days} days, actual {worst.avg_real_days} days, "
        f"gap {gap:.2f} days)",
        f"- Best mode: {best.shipping_mode} ({best.late_pct}% late)",
        f"- Overall late rate across {total:,} order items: {overall_late:.1f}%",
        f"- {n_100} region/mode combinations are 100% late, so the problem is "
        f"not specific to one region",
    ])


def build_briefing_prompt(mode_df, region_df, version="v1"):
    mode_table = mode_df.to_string(index=False)

    if version == "v1":
        return BRIEFING_V1.format(
            mode_table=mode_table,
            region_table=region_df.head(5).to_string(index=False),
        )

    templates = {"v2": BRIEFING_V2, "v3": BRIEFING_V3}
    if version in templates:
        return templates[version].format(
            mode_table=mode_table,
            facts=build_facts(mode_df, region_df),
        )

    raise ValueError(f"Unknown version: {version}")

WHATIF_V1 = """A manager asks: {question}
Facts:
{facts}
Answer the question."""
WHATIF_V2 = """You are answering a what-if question from an operations manager.
QUESTION
{question}
SCENARIO FACTS (pre-calculated; use exactly, do no arithmetic)
{facts}
RULES
- Use only numbers that appear above.
- State that the result assumes moved orders would perform like the target mode's historical average in this region.
- Cover both sides of the trade-off: lateness AND delivery time.
- Do not claim anything about cost, customer satisfaction or any effect not in the facts.
- Under 120 words.

FORMAT
Answer: one sentence with a clear verdict (better / worse / mixed).
Impact: exactly 2 bullets, each with a number.
Caveat: one sentence.
"""


def build_whatif_facts(region, from_mode, to_mode, a, b, share=1.0):
    n = int(a["total_orders"])
    moved = round(n * share)
    late_before = round(moved * a["late_pct"] / 100)
    late_after = round(moved * b["late_pct"] / 100)
    days_change = b["avg_real_days"] - a["avg_real_days"]
    where = region or "all regions"

    return "\n".join([
        f"- Scenario: move {moved:,} of {n:,} {from_mode} order items in {where} to {to_mode}",
        f"- {from_mode}: {a['late_pct']}% late; promised {a['avg_scheduled_days']} days, "
        f"actual {a['avg_real_days']} days",
        f"- {to_mode}: {b['late_pct']}% late; promised {b['avg_scheduled_days']} days, "
        f"actual {b['avg_real_days']} days",
        f"- Late order items among the moved orders: before {late_before:,.0f}, "
        f"after {late_after:,.0f} (change {late_after - late_before:+,.0f})",
        f"- Average delivery time changes by {days_change:+.2f} days "
        f"({a['avg_real_days']} to {b['avg_real_days']})",
    ])


def build_whatif_prompt(question, region, from_mode, to_mode, a, b, share=1.0, version="v2"):
    templates = {"v1": WHATIF_V1, "v2": WHATIF_V2, "v3": WHATIF_V3}
    if version not in templates:
        raise ValueError(f"Unknown version: {version}")
    facts = build_whatif_facts(region, from_mode, to_mode, a, b, share)
    return templates[version].format(question=question, facts=facts)

WHATIF_V3 = """You are answering a what-if question from an operations manager.

QUESTION
{question}

SCENARIO FACTS (pre-calculated; use exactly, do no arithmetic)
{facts}

RULES
- Use only numbers that appear above.
- The Answer must be one full sentence that names the trade-off.
- Each Impact bullet must show a before -> after number.
- Lateness is measured against each mode's own promise. State how the promised days change (from X to Y), because that is part of why lateness changes.
- State that the result assumes moved orders would perform like the target mode's historical average in this region.
- Do not claim anything about cost, customer satisfaction or any effect not in the facts.
- Under 120 words.

FORMAT
Answer: one sentence.
Impact: exactly 2 bullets.
Caveat: one sentence.
"""