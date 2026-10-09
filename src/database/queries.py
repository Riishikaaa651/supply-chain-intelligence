import pandas as pd
from src.database.db_connection import get_connection


def _run(sql, params=()):
    conn = get_connection()
    try:
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()


def mode_performance():
    """Reliability ranking by shipping mode."""
    return _run("""
        SELECT shipping_mode,
               COUNT(*) AS total_orders,
               ROUND(AVG(late_delivery_risk) * 100, 1) AS late_pct,
               ROUND(AVG(days_for_shipping_real), 2) AS avg_real_days,
               ROUND(AVG(days_for_shipment_scheduled), 2) AS avg_scheduled_days,
               RANK() OVER (ORDER BY AVG(late_delivery_risk) ASC) AS reliability_rank
        FROM orders
        GROUP BY shipping_mode
        ORDER BY reliability_rank
    """)


def region_mode_risk(min_orders=500):
    """Late % for each region and shipping mode, ignoring tiny groups."""
    return _run("""
        SELECT order_region, shipping_mode,
               COUNT(*) AS total_orders,
               ROUND(AVG(late_delivery_risk) * 100, 1) AS late_pct
        FROM orders
        GROUP BY order_region, shipping_mode
        HAVING COUNT(*) > ?
        ORDER BY late_pct DESC
    """, params=(min_orders,))


def filter_orders(shipping_mode=None, region=None, limit=100):
    """Orders for the dashboard table, with optional filters."""
    sql = """
        SELECT order_id, shipping_mode, order_region, category_name,
               shipping_gap, late_delivery_risk
        FROM orders
        WHERE 1 = 1
    """
    params = []
    if shipping_mode:
        sql += " AND shipping_mode = ?"
        params.append(shipping_mode)
    if region:
        sql += " AND order_region = ?"
        params.append(region)
    sql += " LIMIT ?"
    params.append(limit)
    return _run(sql, params=tuple(params))
if __name__ == "__main__":
    print(mode_performance())
    print(region_mode_risk().head())
    print(filter_orders(shipping_mode="Same Day", region="Western Europe", limit=5))