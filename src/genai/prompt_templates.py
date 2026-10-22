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