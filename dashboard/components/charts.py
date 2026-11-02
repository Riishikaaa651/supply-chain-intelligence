import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

GRID = "rgba(255, 255, 255, 0.08)"
TEXT = "#cbd5e1"
DELAY_COLOR = "#fbbf24"      # amber, same as the delay KPI card
SHORTAGE_COLOR = "#22d3ee"   # cyan, same as the shortage KPI card
RISK_COLORS = {"Low": "#34d399", "Medium": "#fbbf24", "High": "#f87171"}


def _style(fig, height=340):
    """Transparent background so the chart sits on top of the glass card."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=TEXT, size=13),
        margin=dict(l=10, r=10, t=10, b=10),
        height=height,
        showlegend=False,
        hoverlabel=dict(bgcolor="#0f172a", font_color="#f8fafc"),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


def delay_by_mode_chart(rows):
    """Bar chart: average delay probability for each shipping mode."""
    df = pd.DataFrame(rows).sort_values("avg_delay_prob", ascending=False)
    fig = px.bar(
        df, x="shipping_mode", y="avg_delay_prob",
        text="avg_delay_prob",
        custom_data=["orders", "high_risk_pct"],
        labels={"shipping_mode": "", "avg_delay_prob": "Average delay probability"},
    )
    fig.update_traces(
        marker_color=DELAY_COLOR,
        texttemplate="%{y:.2f}", textposition="outside",
        hovertemplate="<b>%{x}</b><br>Avg delay probability: %{y:.3f}"
                      "<br>Orders: %{customdata[0]:,}"
                      "<br>High risk: %{customdata[1]}%<extra></extra>",
    )
    fig.update_yaxes(range=[0, 1.1])
    return _style(fig)


def shortage_by_category_chart(rows):
    """Horizontal bar chart: share of orders at High shortage risk, per category."""
    df = pd.DataFrame(rows)
    df["category_name"] = df["category_name"].str.strip()
    df = df.sort_values("high_risk_pct", ascending=True)       # biggest ends up on top
    fig = px.bar(
        df, x="high_risk_pct", y="category_name", orientation="h",
        text="high_risk_pct",
        custom_data=["orders", "avg_shortage_prob"],
        labels={"high_risk_pct": "Orders at High risk (%)", "category_name": ""},
    )
    fig.update_traces(
        marker_color=SHORTAGE_COLOR,
        texttemplate="%{x:.0f}%", textposition="outside",
        hovertemplate="<b>%{y}</b><br>Orders at High risk: %{x}%"
                      "<br>Avg shortage score: %{customdata[1]:.3f}"
                      "<br>Orders: %{customdata[0]:,}<extra></extra>",
    )
    fig.update_xaxes(range=[0, 115])
    return _style(fig, height=380)


def risk_donut_chart(rows, risk_type):
    """Donut: how many orders are Low / Medium / High for one risk type."""
    df = pd.DataFrame(rows)
    df = df[df["risk_type"] == risk_type]
    order = ["Low", "Medium", "High"]
    df = df.set_index("risk_level").reindex(order).fillna(0).reset_index()
    total = int(df["orders"].sum())

    fig = go.Figure(go.Pie(
        labels=df["risk_level"], values=df["orders"], hole=0.62, sort=False,
        marker=dict(colors=[RISK_COLORS[l] for l in df["risk_level"]],
                    line=dict(color="#0b1220", width=2)),
        textinfo="percent", textfont=dict(color="#0b1220", size=13),
        hovertemplate="<b>%{label}</b><br>%{value:,} orders (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        annotations=[dict(text=f"<b>{total:,}</b><br><span style='font-size:11px'>orders</span>",
                          x=0.5, y=0.5, showarrow=False, font=dict(size=18, color="#f8fafc"))],
    )
    _style(fig, height=300)
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center"))
    return fig


def delay_heatmap_chart(rows, selected_mode="All", selected_region="All"):
    """Heatmap: average delay probability for every shipping mode x region pair.
    The cell (or row / column) matching the sidebar filters gets a cyan outline."""
    df = pd.DataFrame(rows)
    pivot = df.pivot(index="order_region", columns="shipping_mode", values="avg_delay_prob")
    pivot = pivot[["First Class", "Second Class", "Same Day", "Standard Class"]]   # worst to best
    pivot = pivot.loc[pivot.mean(axis=1).sort_values().index]

    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns, y=pivot.index,
        zmin=0, zmax=1,
        colorscale=[[0, "#1e293b"], [1, "#fbbf24"]],
        text=pivot.values, texttemplate="%{text:.2f}", textfont=dict(size=11),
        xgap=3, ygap=3, showscale=False,
        hovertemplate="<b>%{y}</b> · %{x}<br>Avg delay probability: %{z:.3f}<extra></extra>",
    ))

    # outline the selected mode / region
    cols, regs = list(pivot.columns), list(pivot.index)
    xi = cols.index(selected_mode) if selected_mode in cols else None
    yi = regs.index(selected_region) if selected_region in regs else None
    if xi is not None or yi is not None:
        x0, x1 = (xi - 0.5, xi + 0.5) if xi is not None else (-0.5, len(cols) - 0.5)
        y0, y1 = (yi - 0.5, yi + 0.5) if yi is not None else (-0.5, len(regs) - 0.5)
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                      line=dict(color=SHORTAGE_COLOR, width=3), fillcolor="rgba(0,0,0,0)")

    _style(fig, height=620)
    fig.update_xaxes(side="top", showgrid=False)
    fig.update_yaxes(showgrid=False)
    return fig


def monthly_trend_chart(rows):
    """Bars = orders per month, line = real late-delivery % (right axis)."""
    df = pd.DataFrame(rows)
    df["month"] = pd.to_datetime(df["month"])
    full = pd.date_range(df["month"].min(), df["month"].max(), freq="MS")
    df = df.set_index("month").reindex(full).rename_axis("month").reset_index()
    fig = go.Figure()
    fig.add_bar(
        x=df["month"], y=df["orders"], name="Orders",
        marker_color="rgba(96, 165, 250, 0.45)",
        hovertemplate="%{x|%b %Y}<br>Orders: %{y:,}<extra></extra>",
    )
    fig.add_scatter(
        x=df["month"], y=df["late_pct"], name="Late delivery %", yaxis="y2",
        mode="lines+markers", line=dict(color=DELAY_COLOR, width=2.5), marker=dict(size=5),
        hovertemplate="%{x|%b %Y}<br>Late deliveries: %{y}%<extra></extra>",
    )
    _style(fig, height=340)
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", y=1.12, x=0),
        margin=dict(l=10, r=10, t=30, b=10),
        yaxis2=dict(overlaying="y", side="right", range=[0, 100], showgrid=False,
                    ticksuffix="%", zeroline=False),
    )
    return fig