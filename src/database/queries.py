import pandas as pd
from .db_connection import get_connection


def run_query(sql, params=()):
    """Run any SQL query and return the result as a DataFrame."""
    conn = get_connection()
    try:
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()   # always close, even if the query fails


def delay_by_mode():
    return run_query("""
        SELECT o.shipping_mode,
               COUNT(*)                            AS orders,
               ROUND(AVG(d.delay_prob), 3)         AS avg_delay_prob,
               ROUND(100.0 * AVG(d.risk_level = 'High'), 1) AS high_risk_pct
        FROM delay_predictions d
        JOIN orders o ON o.order_item_id = d.order_item_id
        GROUP BY o.shipping_mode
        ORDER BY avg_delay_prob DESC
    """)


def delay_by_region():
    return run_query("""
        SELECT order_region,
               COUNT(*)                                   AS orders,
               ROUND(AVG(delay_prob), 3)                  AS avg_delay_prob,
               ROUND(100.0 * AVG(risk_level = 'High'), 1) AS high_risk_pct
        FROM delay_predictions
        GROUP BY order_region
        ORDER BY avg_delay_prob DESC
    """)


def shortage_by_category(limit=10):
    return run_query("""
        SELECT category_name,
               COUNT(*)                                    AS orders,
               ROUND(AVG(shortage_prob), 3)                AS avg_shortage_prob,
               ROUND(100.0 * AVG(risk_level = 'High'), 1)  AS high_risk_pct
        FROM shortage_predictions
        GROUP BY category_name
        ORDER BY avg_shortage_prob DESC
        LIMIT ?
    """, params=(limit,))


def top_risky_orders(limit=10):
    return run_query("""
        SELECT d.order_id, d.order_item_id, o.shipping_mode, o.order_region, o.category_name,
               ROUND(d.delay_prob, 3)    AS delay_prob,
               ROUND(s.shortage_prob, 3) AS shortage_prob
        FROM delay_predictions d
        JOIN shortage_predictions s ON s.order_item_id = d.order_item_id
        JOIN orders o               ON o.order_item_id = d.order_item_id
        WHERE d.risk_level = 'High' AND s.risk_level = 'High'
        ORDER BY d.delay_prob + s.shortage_prob DESC
        LIMIT ?
    """, params=(limit,))


#For llm client, we need to get the facts for a specific order item to explain its delay or shortage risk. The following functions retrieve those facts from the database.
def get_delay_facts(order_item_id):
    """All facts the LLM needs about one order's delay risk."""
    df = run_query("""
        SELECT d.order_item_id, d.order_id, o.shipping_mode, d.order_region, o.category_name,
               d.mode_avg_delay, d.mode_delay_std, d.mode_reliability_score,
               d.region_avg_delay, d.region_delay_std, d.region_reliability_score,
               d.delay_prob, d.risk_level
        FROM delay_predictions d
        JOIN orders o ON o.order_item_id = d.order_item_id
        WHERE d.order_item_id = ?
    """, params=(order_item_id,))
    return df.iloc[0].to_dict() if len(df) else None


def get_shortage_facts(order_item_id):
    """All facts the LLM needs about one order's shortage risk."""
    df = run_query("""
        SELECT s.order_item_id, s.order_id, s.category_name, o.product_name,
               s.product_demand_mean, s.product_demand_std, s.qty_deviation,
               s.product_order_history_count, s.shortage_prob, s.risk_level
        FROM shortage_predictions s
        JOIN orders o ON o.order_item_id = s.order_item_id
        WHERE s.order_item_id = ?
    """, params=(order_item_id,))
    return df.iloc[0].to_dict() if len(df) else None

def get_delay_context():
    """Extra context for the LLM: late rates overall, per shipping mode, and per region."""
    overall = run_query("SELECT ROUND(100.0 * AVG(late_delivery_risk), 1) AS pct FROM orders").iloc[0]["pct"]
    modes = run_query("""
        SELECT shipping_mode, ROUND(100.0 * AVG(late_delivery_risk), 1) AS pct
        FROM orders GROUP BY shipping_mode ORDER BY pct DESC
    """)
    regions = run_query("""
        SELECT order_region, ROUND(100.0 * AVG(late_delivery_risk), 1) AS pct
        FROM orders GROUP BY order_region ORDER BY pct DESC
    """)
    mode_table = "; ".join(f"{r.shipping_mode}: {r.pct}% late" for r in modes.itertuples())
    region_table = "; ".join(f"{r.order_region}: {r.pct}% late" for r in regions.itertuples())
    return {"overall_late_pct": overall, "mode_table": mode_table, "region_table": region_table}