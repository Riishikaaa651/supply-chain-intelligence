import pandas as pd
import streamlit as st

PAGE_SIZES = [10, 20, 50]


def render_risk_table(get, risk_type, risk_level, shipping_mode, region):
    """Show the risk table. Returns the row the user clicked, or None."""
    left, right = st.columns([3, 1])
    page_size = right.selectbox("Rows per page", PAGE_SIZES, index=1)

    params = {"risk_type": risk_type, "risk_level": risk_level, "limit": page_size, "offset": 0}
    if shipping_mode != "All":
        params["shipping_mode"] = shipping_mode
    if region != "All":
        params["region"] = region

    # first call only to learn how many orders match the filters
    total = get("/orders/risky", {**params, "limit": 1})["total"]
    pages = max(1, -(-total // page_size))          # round up
    page = left.number_input(f"Page (1 to {pages})", min_value=1, max_value=pages, value=1)

    params["offset"] = (page - 1) * page_size
    data = get("/orders/risky", params)
    rows = data["rows"]

    st.caption(f"{total:,} orders match these filters. Click a row to select it.")
    if not rows:
        st.info("No orders match these filters. Try a different risk level, shipping mode or region.")
        return None

    df = pd.DataFrame(rows)
    event = st.dataframe(
        df,
        hide_index=True,
        width="stretch",
        on_select="rerun",
        selection_mode="single-row",
        column_order=["order_item_id", "product_name", "category_name", "shipping_mode",
                      "order_region", "delay_prob", "delay_risk", "shortage_score", "shortage_risk"],
        column_config={
            "order_item_id": st.column_config.NumberColumn("Order item", format="%d"),
            "product_name": "Product",
            "category_name": "Category",
            "shipping_mode": "Shipping mode",
            "order_region": "Region",
            "delay_prob": st.column_config.ProgressColumn(
                "Delay probability", min_value=0, max_value=1, format="%.2f",
                help="Chance the order is delivered late. Low below 0.45, Medium 0.45 to 0.75, High above 0.75."),
            "delay_risk": "Delay risk",
            "shortage_score": st.column_config.ProgressColumn(
                "Shortage score", min_value=0, max_value=1, format="%.2f",
                help="Ranking score, NOT a probability. High = top 10% of all orders by score."),
            "shortage_risk": "Shortage risk",
        },
    )

    picked = event.selection.rows
    return rows[picked[0]] if picked else None