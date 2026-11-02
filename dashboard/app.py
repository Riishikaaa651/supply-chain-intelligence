import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))   # so "src" can be imported

import requests
import streamlit as st
from src.database.db_connection import load_config
from dashboard.components.risk_table import render_risk_table
from dashboard.components.charts import (
    delay_by_mode_chart, shortage_by_category_chart,
    risk_donut_chart, delay_heatmap_chart, monthly_trend_chart,
)

cfg = load_config()["api"]
API = f"http://{cfg['host']}:{cfg['port']}"

st.set_page_config(page_title="Supply Chain Intelligence", layout="wide")
css = (Path(__file__).parent / "assets" / "style.css").read_text(encoding="utf-8")
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def get(path, params=None):
    r = requests.get(f"{API}{path}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()


# ---------------- Sidebar ----------------
st.sidebar.markdown("<div class='brand'>Supply Chain<br>Intelligence</div>", unsafe_allow_html=True)

try:
    options = get("/filters")
except requests.exceptions.RequestException:
    st.error("Cannot reach the API. Start it first with: uvicorn src.api.main:app --reload")
    st.stop()

st.sidebar.markdown("<div class='side-label'>Filters</div>", unsafe_allow_html=True)
risk_type = st.sidebar.radio("Risk type", ["Both", "Delay", "Shortage"])
risk_type = risk_type.lower() # the API only accepts: both, delay, shortage
risk_level = st.sidebar.selectbox("Risk level", ["High", "Medium", "Low"])
shipping_mode = st.sidebar.selectbox("Shipping mode", ["All"] + options["shipping_modes"])
region = st.sidebar.selectbox("Order region", ["All"] + options["regions"])

st.sidebar.markdown("<div class='side-label'>Assistant</div>", unsafe_allow_html=True)
open_chat = st.sidebar.button("What-if assistant", icon=":material/chat:",
                              width="stretch", key="open_chat")
if open_chat:
    st.switch_page("pages/whatif_chat.py")

# ---------------- Main page ----------------
s = get("/summary")

st.markdown(
    f"<h1 class='app-title'>Supply Chain Decision Intelligence</h1>"
    f"<p class='app-subtitle'>Delivery delay and stock shortage risk across "
    f"{s['total_orders']:,} orders, with AI-generated explanations</p>",
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total orders", f"{s['total_orders']:,}")
c2.metric("High delay risk", f"{s['delay_high']:,}")
c3.metric("High shortage risk", f"{s['shortage_high']:,}")
c4.metric("High on both", f"{s['both_high']:,}")

chips = "".join(
    f"<span class='chip'>{c}</span>"
    for c in [risk_type.title() + " risk", f"{risk_level} level", shipping_mode, region]
)
st.markdown(f"<div class='chips'>{chips}</div>", unsafe_allow_html=True)

# ---------------- Charts ----------------
st.markdown("<div class='section'>Risk overview</div>", unsafe_allow_html=True)

region_f = {"region": region} if region != "All" else {}
both_f = {**region_f, **({"shipping_mode": shipping_mode} if shipping_mode != "All" else {})}
show_delay = risk_type in ("both", "delay")
show_shortage = risk_type in ("both", "shortage")


def two_up():
    """Two columns when showing both risk types, otherwise one full-width slot."""
    if risk_type == "both":
        return st.columns(2)
    box = st.container()
    return box, box


# row 1: bar charts
c1, c2 = two_up()
if show_delay:
    with c1:
        st.markdown("<div class='chart-title'>Delay risk by shipping mode</div>", unsafe_allow_html=True)
        rows = get("/charts/delay-by-mode", region_f)
        if rows:
            st.plotly_chart(delay_by_mode_chart(rows), width="stretch", config={"displayModeBar": False})
        else:
            st.info("No data for this selection.")
if show_shortage:
    with c2:
        st.markdown("<div class='chart-title'>Top categories by shortage risk</div>", unsafe_allow_html=True)
        rows = get("/charts/shortage-by-category", {"limit": 10, **both_f})
        if rows:
            st.plotly_chart(shortage_by_category_chart(rows), width="stretch", config={"displayModeBar": False})
        else:
            st.info("No data for this selection.")

# row 2: donuts
c3, c4 = two_up()
risk_rows = get("/charts/risk-distribution", both_f)
if show_delay:
    with c3:
        st.markdown("<div class='chart-title'>Delay risk levels</div>", unsafe_allow_html=True)
        st.plotly_chart(risk_donut_chart(risk_rows, "delay"), width="stretch", config={"displayModeBar": False})
if show_shortage:
    with c4:
        st.markdown("<div class='chart-title'>Shortage risk levels</div>", unsafe_allow_html=True)
        st.plotly_chart(risk_donut_chart(risk_rows, "shortage"), width="stretch", config={"displayModeBar": False})

# row 3: monthly trend (real data from the orders table)
trend = get("/charts/monthly-trend", both_f)
if trend:
    st.markdown("<div class='chart-title'>Monthly orders and late delivery rate</div>", unsafe_allow_html=True)
    st.plotly_chart(monthly_trend_chart(trend), width="stretch", config={"displayModeBar": False})

# row 4: heatmap (all orders, selected filter is outlined)
if show_delay:
    st.markdown("<div class='chart-title'>Average delay probability: shipping mode by region "
                "(all orders, your selection is outlined)</div>", unsafe_allow_html=True)
    st.plotly_chart(delay_heatmap_chart(get("/charts/delay-heatmap"), shipping_mode, region),
                    width="stretch", config={"displayModeBar": False})

# ---------------- Risk table ----------------
st.markdown("<div class='section'>Orders at risk</div>", unsafe_allow_html=True)
selected = render_risk_table(get, risk_type, risk_level, shipping_mode, region)

if selected:
    st.session_state["selected_order"] = selected

chosen = st.session_state.get("selected_order")
if chosen:
    st.markdown(
        f"<div class='glass' style='padding:14px 18px; margin-top:12px;'>"
        f"<b>Selected order:</b> #{chosen['order_item_id']} &nbsp;|&nbsp; {chosen['product_name']} "
        f"&nbsp;|&nbsp; {chosen['shipping_mode']} &nbsp;|&nbsp; {chosen['order_region']}"
        f"</div>",
        unsafe_allow_html=True,
    )