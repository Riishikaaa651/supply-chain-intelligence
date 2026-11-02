import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]      # project root
sys.path.append(str(ROOT))

import streamlit as st

from dashboard.components.chat_interface import post_api, preset_questions


def fmt(text):
    """Put every sentence on its own line (decimals like 0.60 are not split)."""
    return re.sub(r"(?<=[.!?])\s+(?=[A-Z0-9])", "\n\n", text.strip())


st.set_page_config(page_title="What-if assistant", layout="wide")
css = (ROOT / "dashboard" / "assets" / "style.css").read_text(encoding="utf-8")
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

order = st.session_state.get("selected_order")

# ---------------- Sidebar ----------------
st.sidebar.markdown("<div class='brand'>Supply Chain<br>Intelligence</div>", unsafe_allow_html=True)
if st.sidebar.button("Back to dashboard", icon=":material/arrow_back:", width="stretch"):
    st.switch_page("app.py")

st.markdown("<div class='app-title'>What-if assistant</div>", unsafe_allow_html=True)

if not order:
    st.info("No order selected. Click a row in the dashboard table first, then open the assistant.")
    st.stop()

oid = int(order["order_item_id"])

st.sidebar.markdown("<div class='side-label'>About product</div>", unsafe_allow_html=True)
st.sidebar.markdown(
    f"<div class='glass' style='padding:14px 16px; line-height:1.6; font-size:0.85rem; "
    f"overflow-wrap:anywhere;'>"
    f"<b>{escape(str(order['product_name']).strip())}</b><br>"
    f"{escape(str(order['category_name']).strip())}<br>"
    f"{escape(str(order['shipping_mode']))} · {escape(str(order['order_region']))}<br><br>"
    f"Delay probability: <b>{order['delay_prob']:.2f}</b> ({order['delay_risk']})<br>"
    f"Shortage score: <b>{order['shortage_score']:.2f}</b> ({order['shortage_risk']})</div>",
    unsafe_allow_html=True,
)

kind = st.sidebar.radio("Risk type", ["Delay", "Shortage"], horizontal=True,
                        label_visibility="collapsed").lower()

history = st.session_state.setdefault("chat_history", {})
msgs = history.setdefault((oid, kind), [])

pending_q, want_brief = None, False

st.sidebar.markdown("<div class='side-label'>Briefing</div>", unsafe_allow_html=True)
if st.sidebar.button("Generate briefing", icon=":material/description:", width="stretch"):
    want_brief = True

st.sidebar.markdown("<div class='side-label'>Quick questions</div>", unsafe_allow_html=True)
for i, q in enumerate(preset_questions(kind)):
    if st.sidebar.button(q, key=f"q_{kind}_{i}", width="stretch"):
        pending_q = q

if msgs and st.sidebar.button("Clear chat", icon=":material/delete:", width="stretch"):
    msgs.clear()
    st.rerun()

typed = st.chat_input("Ask anything about this order...")
if typed:
    pending_q = typed.strip()

# ---------------- Chat ----------------
for m in msgs:
    with st.chat_message(m["role"]):
        st.markdown(fmt(m["content"]))


def turn(user_text, path, payload, field):
    """Show the user message, call the API, show and store the answer."""
    msgs.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            data, err = post_api(path, payload)
        text = data[field] if data else f"⚠️ {err}"
        st.markdown(fmt(text))
    msgs.append({"role": "assistant", "content": text})


if want_brief:
    turn("Give me a briefing for this order.", "/briefing",
         {"order_item_id": oid, "risk_type": kind}, "briefing")
elif pending_q:
    turn(pending_q, "/whatif",
         {"order_item_id": oid, "risk_type": kind, "question": pending_q}, "answer")