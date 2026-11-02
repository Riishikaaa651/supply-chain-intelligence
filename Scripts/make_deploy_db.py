import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "supply_chain.db"
DST = ROOT / "data" / "supply_chain_deploy.db"

# the only columns of the orders table that the API and dashboard use
ORDER_COLS = ["order_item_id", "order_id", "shipping_mode", "order_region",
              "category_name", "product_name", "late_delivery_risk",
              "order_date_dateorders"]

if DST.exists():
    DST.unlink()

conn = sqlite3.connect(DST)
conn.execute("ATTACH DATABASE ? AS src", (str(SRC),))

tables = [r[0] for r in conn.execute(
    "SELECT name FROM src.sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
print("Tables found:", tables)

for t in tables:
    if t == "orders":
        conn.execute(f"CREATE TABLE orders AS SELECT {', '.join(ORDER_COLS)} FROM src.orders")
    else:
        ddl = conn.execute("SELECT sql FROM src.sqlite_master WHERE type='table' AND name=?",
                           (t,)).fetchone()[0]
        conn.execute(ddl)                                    # same structure as the original
        conn.execute(f"INSERT INTO {t} SELECT * FROM src.{t}")

# indexes make the JOINs on order_item_id fast
for t in ("orders", "delay_predictions", "shortage_predictions"):
    if t in tables:
        conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{t}_item ON {t}(order_item_id)")

conn.commit()
conn.execute("DETACH DATABASE src")
conn.execute("VACUUM")          # shrink the file

for t in tables:
    n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"{t}: {n:,} rows")
conn.close()
print(f"Done. {DST.name} is {DST.stat().st_size / 1e6:.1f} MB")
