import json
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.database import queries

CHECKS = {
    "summary": queries.summary,
    "filter_options": queries.filter_options,
    "delay_by_mode": queries.delay_by_mode,
    "shortage_by_category": lambda: queries.shortage_by_category(10),
    "risk_distribution": queries.risk_distribution,
    "delay_heatmap": queries.delay_heatmap,
    "monthly_trend": queries.monthly_trend,
    "delay_context": queries.get_delay_context,
    "risky_orders": lambda: queries.risky_orders("both", "High", None, None, 20, 0),
    "delay_facts": lambda: queries.get_delay_facts(173124),
    "shortage_facts": lambda: queries.get_shortage_facts(173124),
}


def normalise(x):
    return x.to_dict("records") if hasattr(x, "to_dict") else x


def run(db_file):
    os.environ["DB_PATH"] = db_file
    return {name: json.dumps(normalise(fn()), default=str, sort_keys=True)
            for name, fn in CHECKS.items()}


big = run("data/supply_chain.db")
slim = run("data/supply_chain_deploy.db")

bad = 0
for name in CHECKS:
    same = big[name] == slim[name]
    bad += not same
    print("OK  " if same else "DIFF", name)
print("\nAll checks passed." if bad == 0 else f"\n{bad} check(s) differ.")