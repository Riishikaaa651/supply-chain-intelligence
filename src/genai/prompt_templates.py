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
