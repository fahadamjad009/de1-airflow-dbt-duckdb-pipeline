"""
DE1 — ASX Financial Data Pipeline Dashboard
Full interactive dashboard — candlestick, correlation, Sharpe, drawdown,
sector rotation, treemap, radar, waterfall, macro overlay.
"""

import streamlit as st
import duckdb
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
import random

st.set_page_config(page_title="ASX Financial Pipeline", page_icon="📊", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0A0F1E !important; }
    .main { background-color: #0A0F1E !important; }
    .block-container {
        padding-top: 1.5rem;
        padding-left: 2rem;
        padding-right: 2rem;
        background-color: #0A0F1E !important;
    }
    .stMarkdown, .stMarkdown p, label, .stSelectbox label,
    .stMultiSelect label, .stCheckbox label, p, span {
        color: #F1F5F9 !important;
    }
    [data-testid="stMetricValue"] {
        color: #60A5FA !important;
        font-size: 2rem !important;
    }
    [data-testid="stMetricLabel"] { color: #94A3B8 !important; }
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #111827, #1E3A5F) !important;
        border: 1px solid #1E40AF !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        background-color: #111827 !important;
        border-radius: 10px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #94A3B8 !important;
        background-color: transparent !important;
        border-radius: 8px !important;
    }
    .stTabs [aria-selected="true"] {
        color: #F1F5F9 !important;
        background-color: #1E40AF !important;
    }
    .stSelectbox > div > div {
        background-color: #111827 !important;
        border: 1px solid #1E40AF !important;
        color: #F1F5F9 !important;
        border-radius: 8px !important;
    }
    .stMultiSelect > div > div {
        background-color: #111827 !important;
        border: 1px solid #1E40AF !important;
        color: #F1F5F9 !important;
        border-radius: 8px !important;
    }
    .stCheckbox span { color: #F1F5F9 !important; }
    .stDataFrame {
        background-color: #111827 !important;
        border: 1px solid #1E3A5F !important;
        border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] { background-color: #111827 !important; }
    .stButton > button {
        background: linear-gradient(90deg, #1D4ED8, #3B82F6) !important;
        color: white !important; border: none !important;
        border-radius: 10px !important;
        padding: 0.5rem 2rem !important;
        font-size: 1rem !important; font-weight: 600 !important;
    }
    h1 {
        background: linear-gradient(90deg, #3B82F6, #60A5FA) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        font-size: 2.2rem !important;
    }
    h2, h3 { color: #F1F5F9 !important; }
    hr { border-color: #1E3A5F !important; }
    .footer { color: #475569; font-size: 0.78rem; text-align: center; margin-top: 2rem; }
    .js-plotly-plot { border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)

PLOT_BG  = "#0D1117"
PAPER_BG = "#111827"
GRID_COL = "#1E3A5F"
TEXT_COL = "#94A3B8"
BLUE="#3B82F6"; GREEN="#10B981"; RED="#F87171"
YELLOW="#FBBF24"; ORANGE="#F97316"; PURPLE="#8B5CF6"

SECTOR_COLORS = {
    "Financials": BLUE, "Materials": GREEN, "Healthcare": PURPLE,
    "Consumer Disc": ORANGE, "Consumer Stap": YELLOW, "Communication": RED,
}


def dark_layout(fig, title="", height=350):
    fig.update_layout(
        title=dict(text=title, font=dict(color="#F1F5F9", size=14)),
        plot_bgcolor=PLOT_BG,
        paper_bgcolor=PAPER_BG,
        font=dict(color="#F1F5F9", size=12),
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(
            bgcolor="rgba(17,24,39,0.8)",
            bordercolor="#1E3A5F",
            borderwidth=1,
            font=dict(color="#F1F5F9"),
        ),
    )
    fig.update_xaxes(
        gridcolor="#1E3A5F",
        zerolinecolor="#1E3A5F",
        tickfont=dict(color="#94A3B8"),
        title_font=dict(color="#F1F5F9"),
    )
    fig.update_yaxes(
        gridcolor="#1E3A5F",
        zerolinecolor="#1E3A5F",
        tickfont=dict(color="#94A3B8"),
        title_font=dict(color="#F1F5F9"),
    )
    return fig


def make_gauge(value, title, max_val, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title, "font": {"color": "#F1F5F9", "size": 13}},
        number={"font": {"color": color, "size": 32}, "suffix": "%"},
        gauge={
            "axis": {"range": [0, max_val], "tickcolor": "#94A3B8",
                     "tickfont": {"color": "#94A3B8"}},
            "bar":  {"color": color},
            "bgcolor": "#0D1117",
            "bordercolor": "#1E3A5F",
            "steps": [
                {"range": [0, max_val*0.33], "color": "#064E3B"},
                {"range": [max_val*0.33, max_val*0.66], "color": "#78350F"},
                {"range": [max_val*0.66, max_val], "color": "#7F1D1D"},
            ],
        },
    ))
    fig.update_layout(
        paper_bgcolor="#111827",
        font=dict(color="#F1F5F9"),
        height=220,
        margin=dict(l=20, r=20, t=50, b=10),
    )
    return fig


def _bootstrap_db(db_path):
    """Generate sample data and run dbt-equivalent transforms for cloud deploy."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))
    from ingest_financial_data import generate_asx_data, generate_macro_data

    con = duckdb.connect(db_path)

    asx_df   = generate_asx_data(90)
    macro_df = generate_macro_data()

    con.execute("DROP TABLE IF EXISTS raw_asx_prices")
    con.execute("DROP TABLE IF EXISTS raw_macro_indicators")
    con.execute("CREATE TABLE raw_asx_prices AS SELECT * FROM asx_df")
    con.execute("CREATE TABLE raw_macro_indicators AS SELECT * FROM macro_df")

    con.execute("DROP TABLE IF EXISTS main.stg_macro_indicators")
    con.execute("""
        CREATE TABLE main.stg_macro_indicators AS
        SELECT indicator,
               ROUND(CAST(value AS DOUBLE), 4) AS value,
               unit,
               CAST(date AS DATE) AS date,
               source
        FROM raw_macro_indicators
    """)

    con.execute("DROP TABLE IF EXISTS main.mart_asx_daily_metrics")
    con.execute("""
        CREATE TABLE main.mart_asx_daily_metrics AS
        WITH base AS (
            SELECT
                CAST(date AS DATE) AS date,
                ticker, company, sector,
                ROUND(CAST(open   AS DOUBLE), 3) AS open,
                ROUND(CAST(high   AS DOUBLE), 3) AS high,
                ROUND(CAST(low    AS DOUBLE), 3) AS low,
                ROUND(CAST(close  AS DOUBLE), 3) AS close,
                CAST(volume AS BIGINT)            AS volume,
                ROUND(CAST(daily_return AS DOUBLE), 4) AS daily_return
            FROM raw_asx_prices
            WHERE close > 0 AND volume > 0
        )
        SELECT *,
            ROUND(AVG(close) OVER (
                PARTITION BY ticker ORDER BY date
                ROWS BETWEEN 4 PRECEDING AND CURRENT ROW), 3) AS ma_5_rounded,
            ROUND(AVG(close) OVER (
                PARTITION BY ticker ORDER BY date
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW), 3) AS ma_20_rounded,
            ROUND(STDDEV(daily_return) OVER (
                PARTITION BY ticker ORDER BY date
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) * SQRT(252), 4) AS volatility_20d_rounded,
            ROUND((close / FIRST_VALUE(close) OVER (
                PARTITION BY ticker ORDER BY date) - 1) * 100, 2) AS cum_return_pct,
            ROUND(close - low, 3) AS daily_range,
            ROUND(volume / NULLIF(AVG(volume) OVER (
                PARTITION BY ticker ORDER BY date
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW), 0), 2) AS rel_volume
        FROM base
        ORDER BY ticker, date
    """)

    con.execute("DROP TABLE IF EXISTS main.mart_sector_summary")
    con.execute("""
        CREATE TABLE main.mart_sector_summary AS
        WITH latest AS (
            SELECT * FROM main.mart_asx_daily_metrics
            WHERE date = (SELECT MAX(date) FROM main.mart_asx_daily_metrics)
        )
        SELECT
            sector,
            COUNT(DISTINCT ticker)                  AS ticker_count,
            ROUND(AVG(cum_return_pct), 2)           AS avg_cumulative_return_pct,
            ROUND(AVG(volatility_20d_rounded), 4)   AS avg_volatility,
            ROUND(AVG(rel_volume), 2)               AS avg_relative_volume,
            ROUND(SUM(volume), 0)                   AS total_volume,
            ROUND(AVG(close), 2)                    AS avg_close_price,
            MIN(cum_return_pct)                     AS min_return,
            MAX(cum_return_pct)                     AS max_return,
            CASE
                WHEN AVG(cum_return_pct) > 5  THEN 'Strong Buy'
                WHEN AVG(cum_return_pct) > 0  THEN 'Hold'
                WHEN AVG(cum_return_pct) > -5 THEN 'Weak'
                ELSE 'Underperform'
            END AS sector_signal
        FROM latest
        GROUP BY sector
        ORDER BY avg_cumulative_return_pct DESC
    """)

    con.close()


@st.cache_resource
def get_con():
    db = "data/financial.duckdb"
    if not os.path.exists(db):
        os.makedirs("data", exist_ok=True)
        with st.spinner("Bootstrapping data pipeline..."):
            _bootstrap_db(db)
    return duckdb.connect(db, read_only=True)


@st.cache_data(ttl=300)
def load_daily():
    return get_con().execute("SELECT * FROM main.mart_asx_daily_metrics ORDER BY date").fetchdf()


@st.cache_data(ttl=300)
def load_sector():
    return get_con().execute("SELECT * FROM main.mart_sector_summary ORDER BY avg_cumulative_return_pct DESC").fetchdf()


@st.cache_data(ttl=300)
def load_macro():
    return get_con().execute("SELECT * FROM main.stg_macro_indicators ORDER BY indicator").fetchdf()


@st.cache_data(ttl=300)
def load_raw():
    return get_con().execute("SELECT * FROM raw_asx_prices ORDER BY date").fetchdf()


@st.cache_data(ttl=300)
def load_counts():
    c = get_con()
    return (
        c.execute("SELECT COUNT(*) FROM raw_asx_prices").fetchone()[0],
        c.execute("SELECT COUNT(DISTINCT ticker) FROM raw_asx_prices").fetchone()[0],
        c.execute("SELECT COUNT(DISTINCT date) FROM raw_asx_prices").fetchone()[0],
    )


# ── Load ──────────────────────────────────────────────────────────────────────
daily_df  = load_daily()
sector_df = load_sector()
macro_df  = load_macro()
raw_df    = load_raw()
rows, tickers, days = load_counts()

daily_df["date"] = pd.to_datetime(daily_df["date"])
raw_df["date"]   = pd.to_datetime(raw_df["date"])

# ── Header ────────────────────────────────────────────────────────────────────
st.title("📊 ASX Financial Data Pipeline Dashboard")
st.markdown(
    "End-to-end pipeline: **Apache Airflow** → **dbt** → **DuckDB** → **Streamlit**. "
    "10 ASX tickers · 90 days · Candlestick · Correlation · Sharpe · Drawdown · Sector Rotation"
)
st.markdown("---")

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Total Rows", f"{rows:,}")
c2.metric("ASX Tickers", tickers)
c3.metric("Trading Days", days)
c4.metric("dbt Models", "4")
c5.metric("Pipeline", "✅ Live")
st.markdown("---")

tab1,tab2,tab3,tab4,tab5 = st.tabs([
    "📈 Price & Technical",
    "🏭 Sector Analysis",
    "🔬 Deep Analytics",
    "🌍 Macro & Context",
    "🔧 Pipeline Architecture",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — PRICE & TECHNICAL
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Price & Technical Analysis")
    col_ctrl, _ = st.columns([1, 3])
    with col_ctrl:
        sel = st.selectbox("Ticker:", sorted(daily_df["ticker"].unique()))
        show_ma5  = st.checkbox("MA5",  True)
        show_ma20 = st.checkbox("MA20", True)
        show_vol  = st.checkbox("Volume", True)

    tdf = daily_df[daily_df["ticker"] == sel].copy()
    rdf = raw_df[raw_df["ticker"] == sel].copy()
    company = tdf["company"].iloc[0]
    sector  = tdf["sector"].iloc[0]
    st.markdown(f"**{company}** · {sector}")

    if show_vol:
        fig_candle = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            row_heights=[0.75, 0.25], vertical_spacing=0.03,
        )
    else:
        fig_candle = make_subplots(rows=1, cols=1)

    fig_candle.add_trace(go.Candlestick(
        x=rdf["date"], open=rdf["open"], high=rdf["high"],
        low=rdf["low"], close=rdf["close"],
        name="OHLC",
        increasing_line_color=GREEN, decreasing_line_color=RED,
    ), row=1, col=1)

    if show_ma5:
        fig_candle.add_trace(go.Scatter(
            x=tdf["date"], y=tdf["ma_5_rounded"],
            name="MA5", line=dict(color=YELLOW, width=1.5, dash="dash"),
        ), row=1, col=1)

    if show_ma20:
        fig_candle.add_trace(go.Scatter(
            x=tdf["date"], y=tdf["ma_20_rounded"],
            name="MA20", line=dict(color=ORANGE, width=1.5, dash="dot"),
        ), row=1, col=1)

    cross_up   = tdf[(tdf["ma_5_rounded"] > tdf["ma_20_rounded"]) & (tdf["ma_5_rounded"].shift(1) <= tdf["ma_20_rounded"].shift(1))]
    cross_down = tdf[(tdf["ma_5_rounded"] < tdf["ma_20_rounded"]) & (tdf["ma_5_rounded"].shift(1) >= tdf["ma_20_rounded"].shift(1))]

    if not cross_up.empty:
        fig_candle.add_trace(go.Scatter(
            x=cross_up["date"], y=cross_up["close"],
            mode="markers", name="Buy Signal",
            marker=dict(symbol="triangle-up", size=14, color=GREEN),
        ), row=1, col=1)

    if not cross_down.empty:
        fig_candle.add_trace(go.Scatter(
            x=cross_down["date"], y=cross_down["close"],
            mode="markers", name="Sell Signal",
            marker=dict(symbol="triangle-down", size=14, color=RED),
        ), row=1, col=1)

    if show_vol:
        fig_candle.add_trace(go.Bar(
            x=rdf["date"], y=rdf["volume"],
            name="Volume",
            marker_color=[GREEN if c >= o else RED for c, o in zip(rdf["close"], rdf["open"])],
            opacity=0.7,
        ), row=2, col=1)

    fig_candle.update_layout(
        plot_bgcolor=PLOT_BG, paper_bgcolor=PAPER_BG,
        font=dict(color="#F1F5F9", size=12), height=520,
        margin=dict(l=20, r=20, t=40, b=20),
        title=dict(text=f"{sel} — Candlestick with MA Crossover Signals", font=dict(color="#F1F5F9", size=14)),
        xaxis_rangeslider_visible=False,
        legend=dict(bgcolor="rgba(17,24,39,0.8)", bordercolor="#1E3A5F", borderwidth=1, font=dict(color="#F1F5F9")),
    )
    fig_candle.update_xaxes(gridcolor=GRID_COL, tickfont=dict(color="#94A3B8"), zerolinecolor=GRID_COL)
    fig_candle.update_yaxes(gridcolor=GRID_COL, tickfont=dict(color="#94A3B8"), zerolinecolor=GRID_COL)
    st.plotly_chart(fig_candle, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        fig_cum = go.Figure(go.Scatter(
            x=tdf["date"], y=tdf["cum_return_pct"],
            fill="tozeroy", fillcolor="rgba(59,130,246,0.15)",
            line=dict(color=BLUE, width=2),
        ))
        fig_cum = dark_layout(fig_cum, f"{sel} — Cumulative Return %", 280)
        fig_cum.update_yaxes(ticksuffix="%")
        st.plotly_chart(fig_cum, use_container_width=True)

    with col_b:
        fig_hist = go.Figure(go.Histogram(
            x=tdf["daily_return"], nbinsx=30,
            marker_color=BLUE, opacity=0.8, name="Daily Return",
        ))
        fig_hist.add_vline(x=0, line_dash="dash", line_color="#475569")
        fig_hist.add_vline(
            x=tdf["daily_return"].mean(), line_dash="dot", line_color=GREEN,
            annotation_text="Mean", annotation_font_color="#F1F5F9",
        )
        fig_hist = dark_layout(fig_hist, f"{sel} — Daily Return Distribution", 280)
        fig_hist.update_xaxes(ticksuffix="%")
        st.plotly_chart(fig_hist, use_container_width=True)

    col_c, col_d = st.columns(2)
    with col_c:
        fig_vola = go.Figure(go.Scatter(
            x=tdf["date"], y=tdf["volatility_20d_rounded"],
            fill="tozeroy", fillcolor="rgba(248,113,113,0.15)",
            line=dict(color=RED, width=2),
        ))
        fig_vola = dark_layout(fig_vola, f"{sel} — 20d Annualised Volatility", 280)
        st.plotly_chart(fig_vola, use_container_width=True)

    with col_d:
        fig_rvol = go.Figure(go.Bar(
            x=tdf["date"], y=tdf["rel_volume"],
            marker_color=[GREEN if v >= 1 else RED for v in tdf["rel_volume"]],
        ))
        fig_rvol.add_hline(y=1, line_dash="dash", line_color="#475569",
                           annotation_text="Avg", annotation_font_color="#F1F5F9")
        fig_rvol = dark_layout(fig_rvol, f"{sel} — Relative Volume vs 20d Avg", 280)
        st.plotly_chart(fig_rvol, use_container_width=True)

    st.markdown("---")
    st.subheader("📊 Cross-Ticker Return Correlation")
    pivot = daily_df.pivot_table(index="date", columns="ticker", values="daily_return")
    corr  = pivot.corr().round(3)
    fig_corr = go.Figure(go.Heatmap(
        z=corr.values,
        x=corr.columns.tolist(),
        y=corr.index.tolist(),
        colorscale="RdBu",
        zmid=0, zmin=-1, zmax=1,
        hovertemplate="%{x} vs %{y}: %{z:.3f}<extra></extra>",
        colorbar=dict(title="Corr", tickfont=dict(color="#F1F5F9"), title_font=dict(color="#F1F5F9")),
        texttemplate="%{z:.2f}",
        textfont=dict(color="#F1F5F9", size=10),
    ))
    fig_corr = dark_layout(fig_corr, "Daily Return Correlation Matrix — All Tickers", 420)
    fig_corr.update_xaxes(showgrid=False, tickfont=dict(color="#F1F5F9"))
    fig_corr.update_yaxes(showgrid=False, tickfont=dict(color="#F1F5F9"))
    st.plotly_chart(fig_corr, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SECTOR ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Sector Performance Analysis")
    colors = [SECTOR_COLORS.get(s, BLUE) for s in sector_df["sector"]]

    col_a, col_b = st.columns(2)
    with col_a:
        fig_sec = go.Figure(go.Bar(
            x=sector_df["avg_cumulative_return_pct"],
            y=sector_df["sector"], orientation="h",
            marker_color=colors,
            text=[f"{v:.1f}%" for v in sector_df["avg_cumulative_return_pct"]],
            textposition="outside",
            textfont=dict(color="#F1F5F9"),
        ))
        fig_sec = dark_layout(fig_sec, "Avg Cumulative Return by Sector", 320)
        fig_sec.update_xaxes(ticksuffix="%")
        fig_sec.update_yaxes(showgrid=False, tickfont=dict(color="#F1F5F9"))
        st.plotly_chart(fig_sec, use_container_width=True)

    with col_b:
        latest = daily_df.groupby(["sector","ticker"]).last().reset_index()
        fig_tree = px.treemap(
            latest,
            path=["sector","ticker"],
            values=latest["close"].abs(),
            color="cum_return_pct",
            color_continuous_scale="RdYlGn",
            color_continuous_midpoint=0,
        )
        fig_tree.update_layout(
            paper_bgcolor=PAPER_BG, font=dict(color="#F1F5F9"),
            height=320, margin=dict(l=10,r=10,t=40,b=10),
            title=dict(text="Sector to Ticker Treemap (colour = cumulative return)", font=dict(color="#F1F5F9")),
        )
        fig_tree.update_traces(textfont=dict(color="#F1F5F9"))
        st.plotly_chart(fig_tree, use_container_width=True)

    st.markdown("---")
    sector_daily = daily_df.groupby(["date","sector"])["cum_return_pct"].mean().reset_index()
    fig_rot = go.Figure()
    for s, color in SECTOR_COLORS.items():
        sdf = sector_daily[sector_daily["sector"] == s]
        if not sdf.empty:
            fig_rot.add_trace(go.Scatter(
                x=sdf["date"], y=sdf["cum_return_pct"],
                name=s, line=dict(color=color, width=2),
            ))
    fig_rot = dark_layout(fig_rot, "Sector Rotation — Cumulative Return Over Time", 380)
    fig_rot.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig_rot, use_container_width=True)

    col_c, col_d = st.columns(2)
    with col_c:
        fig_rr = go.Figure(go.Scatter(
            x=sector_df["avg_volatility"],
            y=sector_df["avg_cumulative_return_pct"],
            mode="markers+text",
            text=sector_df["sector"],
            textposition="top center",
            textfont=dict(color="#F1F5F9", size=11),
            marker=dict(size=20, color=colors, line=dict(color="#0A0F1E", width=2)),
        ))
        fig_rr = dark_layout(fig_rr, "Risk vs Return by Sector", 350)
        fig_rr.update_xaxes(title="Avg Volatility")
        fig_rr.update_yaxes(title="Avg Return %", ticksuffix="%")
        st.plotly_chart(fig_rr, use_container_width=True)

    with col_d:
        metrics = ["avg_cumulative_return_pct","avg_volatility","avg_relative_volume"]
        norm_df = sector_df.copy()
        for m in metrics:
            mn, mx = norm_df[m].min(), norm_df[m].max()
            norm_df[m] = (norm_df[m] - mn) / (mx - mn + 1e-9)

        fig_radar = go.Figure()
        for _, row in norm_df.iterrows():
            vals = [row[m] for m in metrics] + [row[metrics[0]]]
            fig_radar.add_trace(go.Scatterpolar(
                r=vals,
                theta=["Return","Volatility","Rel Volume","Return"],
                fill="toself", opacity=0.5,
                name=row["sector"],
                line=dict(color=SECTOR_COLORS.get(row["sector"], BLUE)),
            ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0,1], gridcolor=GRID_COL,
                                tickfont=dict(color="#94A3B8")),
                angularaxis=dict(gridcolor=GRID_COL, tickfont=dict(color="#F1F5F9")),
                bgcolor=PLOT_BG,
            ),
            paper_bgcolor=PAPER_BG, font=dict(color="#F1F5F9"),
            height=350,
            title=dict(text="Sector Multi-Metric Radar", font=dict(color="#F1F5F9")),
            legend=dict(bgcolor="rgba(17,24,39,0.8)", bordercolor="#1E3A5F",
                        borderwidth=1, font=dict(color="#F1F5F9")),
            margin=dict(l=60,r=60,t=60,b=40),
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    sorted_df = sector_df.sort_values("avg_cumulative_return_pct")
    fig_wf = go.Figure(go.Waterfall(
        x=sorted_df["sector"],
        y=sorted_df["avg_cumulative_return_pct"],
        measure=["relative"]*len(sorted_df),
        connector=dict(line=dict(color=GRID_COL)),
        increasing=dict(marker=dict(color=GREEN)),
        decreasing=dict(marker=dict(color=RED)),
        text=[f"{v:.1f}%" for v in sorted_df["avg_cumulative_return_pct"]],
        textposition="outside",
        textfont=dict(color="#F1F5F9"),
    ))
    fig_wf = dark_layout(fig_wf, "Sector Return Waterfall", 320)
    fig_wf.update_xaxes(showgrid=False, tickfont=dict(color="#F1F5F9"))
    fig_wf.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig_wf, use_container_width=True)

    st.markdown("**dbt Sector Signals**")
    sig_map = {"Strong Buy":"🟢","Hold":"🟡","Weak":"🟠","Underperform":"🔴"}
    disp = sector_df[["sector","avg_cumulative_return_pct","avg_volatility","sector_signal"]].copy()
    disp["sector_signal"] = disp["sector_signal"].apply(lambda x: f"{sig_map.get(x,'')} {x}")
    disp.columns = ["Sector","Avg Return %","Avg Volatility","Signal"]
    st.dataframe(disp, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — DEEP ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("🔬 Deep Analytics")

    sel2 = st.selectbox("Select ticker for deep analysis:", sorted(daily_df["ticker"].unique()), key="deep")
    tdf2 = daily_df[daily_df["ticker"] == sel2].copy().sort_values("date")

    tdf2["rolling_sharpe"] = (
        tdf2["daily_return"].rolling(20).mean() /
        (tdf2["daily_return"].rolling(20).std() + 1e-9)
    ) * np.sqrt(252)

    tdf2["cumulative_max"] = tdf2["close"].cummax()
    tdf2["drawdown"]       = (tdf2["close"] - tdf2["cumulative_max"]) / tdf2["cumulative_max"] * 100

    col_a, col_b = st.columns(2)
    with col_a:
        fig_sharpe = go.Figure(go.Scatter(
            x=tdf2["date"], y=tdf2["rolling_sharpe"],
            fill="tozeroy", fillcolor="rgba(139,92,246,0.15)",
            line=dict(color=PURPLE, width=2),
        ))
        fig_sharpe.add_hline(y=0, line_dash="dash", line_color="#475569",
                             annotation_text="0", annotation_font_color="#F1F5F9")
        fig_sharpe.add_hline(y=1, line_dash="dot", line_color=GREEN,
                             annotation_text="Sharpe=1", annotation_font_color="#F1F5F9")
        fig_sharpe = dark_layout(fig_sharpe, f"{sel2} — Rolling 20d Sharpe Ratio (Annualised)", 300)
        st.plotly_chart(fig_sharpe, use_container_width=True)

    with col_b:
        fig_dd = go.Figure(go.Scatter(
            x=tdf2["date"], y=tdf2["drawdown"],
            fill="tozeroy", fillcolor="rgba(248,113,113,0.25)",
            line=dict(color=RED, width=2),
        ))
        fig_dd = dark_layout(fig_dd, f"{sel2} — Drawdown from Peak %", 300)
        fig_dd.update_yaxes(ticksuffix="%")
        st.plotly_chart(fig_dd, use_container_width=True)

    st.markdown("---")
    sharpe_rows = []
    for t in daily_df["ticker"].unique():
        td = daily_df[daily_df["ticker"]==t].copy()
        mean_r = td["daily_return"].mean()
        std_r  = td["daily_return"].std() + 1e-9
        sharpe = (mean_r / std_r) * np.sqrt(252)
        max_dd = ((td["close"] - td["close"].cummax()) / td["close"].cummax() * 100).min()
        sharpe_rows.append({"ticker": t, "sharpe": round(sharpe, 3), "max_drawdown": round(max_dd, 2)})
    sharpe_df = pd.DataFrame(sharpe_rows).sort_values("sharpe", ascending=False)

    col_c, col_d = st.columns(2)
    with col_c:
        fig_sh = go.Figure(go.Bar(
            x=sharpe_df["ticker"],
            y=sharpe_df["sharpe"],
            marker_color=[GREEN if v > 0 else RED for v in sharpe_df["sharpe"]],
            text=[f"{v:.2f}" for v in sharpe_df["sharpe"]],
            textposition="outside",
            textfont=dict(color="#F1F5F9"),
        ))
        fig_sh.add_hline(y=0, line_dash="dash", line_color="#475569")
        fig_sh = dark_layout(fig_sh, "Annualised Sharpe Ratio — All Tickers", 320)
        fig_sh.update_xaxes(showgrid=False, tickfont=dict(color="#F1F5F9"))
        st.plotly_chart(fig_sh, use_container_width=True)

    with col_d:
        fig_mdd = go.Figure(go.Bar(
            x=sharpe_df["ticker"],
            y=sharpe_df["max_drawdown"],
            marker_color=RED,
            text=[f"{v:.1f}%" for v in sharpe_df["max_drawdown"]],
            textposition="outside",
            textfont=dict(color="#F1F5F9"),
        ))
        fig_mdd = dark_layout(fig_mdd, "Max Drawdown % — All Tickers", 320)
        fig_mdd.update_xaxes(showgrid=False, tickfont=dict(color="#F1F5F9"))
        fig_mdd.update_yaxes(ticksuffix="%")
        st.plotly_chart(fig_mdd, use_container_width=True)

    st.markdown("---")
    sel_tickers = st.multiselect(
        "Compare tickers:",
        sorted(daily_df["ticker"].unique()),
        default=sorted(daily_df["ticker"].unique())[:5],
    )
    fig_multi = go.Figure()
    palette = [BLUE, GREEN, RED, YELLOW, ORANGE, PURPLE, "#06B6D4", "#EC4899", "#84CC16", "#A78BFA"]
    for i, t in enumerate(sel_tickers):
        td = daily_df[daily_df["ticker"]==t]
        fig_multi.add_trace(go.Scatter(
            x=td["date"], y=td["cum_return_pct"],
            name=t, line=dict(color=palette[i % len(palette)], width=2),
        ))
    fig_multi.add_hline(y=0, line_dash="dash", line_color="#475569")
    fig_multi = dark_layout(fig_multi, "Multi-Ticker Cumulative Return Comparison", 380)
    fig_multi.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig_multi, use_container_width=True)

    st.markdown("**Analytics Summary**")
    summary_rows = []
    for t in daily_df["ticker"].unique():
        td = daily_df[daily_df["ticker"]==t]
        summary_rows.append({
            "Ticker": t,
            "Company": td["company"].iloc[0],
            "Sector": td["sector"].iloc[0],
            "Cum Return %": round(td["cum_return_pct"].iloc[-1], 2),
            "Avg Volatility": round(td["volatility_20d_rounded"].mean(), 4),
            "Sharpe": sharpe_df[sharpe_df["ticker"]==t]["sharpe"].values[0],
            "Max DD %": sharpe_df[sharpe_df["ticker"]==t]["max_drawdown"].values[0],
        })
    st.dataframe(
        pd.DataFrame(summary_rows).sort_values("Cum Return %", ascending=False),
        use_container_width=True, hide_index=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — MACRO
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Australian Macro Indicators")

    rate_row  = macro_df[macro_df["indicator"].str.contains("Cash Rate")]
    cpi_row   = macro_df[macro_df["indicator"].str.contains("CPI")]
    unemp_row = macro_df[macro_df["indicator"].str.contains("Unemployment")]
    gdp_row   = macro_df[macro_df["indicator"].str.contains("GDP")]

    g1, g2, g3, g4 = st.columns(4)
    if not rate_row.empty:
        g1.plotly_chart(make_gauge(rate_row["value"].iloc[0], "RBA Cash Rate", 10, ORANGE), use_container_width=True)
    if not cpi_row.empty:
        g2.plotly_chart(make_gauge(cpi_row["value"].iloc[0], "CPI Inflation", 10, RED), use_container_width=True)
    if not unemp_row.empty:
        g3.plotly_chart(make_gauge(unemp_row["value"].iloc[0], "Unemployment", 10, YELLOW), use_container_width=True)
    if not gdp_row.empty:
        g4.plotly_chart(make_gauge(gdp_row["value"].iloc[0], "GDP Growth", 10, GREEN), use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        fig_mac = go.Figure(go.Bar(
            x=macro_df["value"], y=macro_df["indicator"],
            orientation="h", marker_color=BLUE,
            text=[f"{v} {u}" for v,u in zip(macro_df["value"], macro_df["unit"])],
            textposition="outside",
            textfont=dict(color="#F1F5F9"),
        ))
        fig_mac = dark_layout(fig_mac, "All Macro Indicators", 380)
        fig_mac.update_yaxes(showgrid=False, tickfont=dict(color="#F1F5F9"))
        st.plotly_chart(fig_mac, use_container_width=True)

    with col_b:
        fig_mp = go.Figure(go.Pie(
            labels=macro_df["indicator"],
            values=macro_df["value"].abs(),
            hole=0.4,
            marker_colors=px.colors.qualitative.Bold,
            textfont=dict(color="#F1F5F9"),
        ))
        fig_mp = dark_layout(fig_mp, "Macro Indicator Relative Values", 380)
        st.plotly_chart(fig_mp, use_container_width=True)

    fig_ctx = make_subplots(specs=[[{"secondary_y": True}]])
    avg_ret = daily_df.groupby("date")["daily_return"].mean().reset_index()
    avg_ret["cum"] = (1 + avg_ret["daily_return"]/100).cumprod() * 100 - 100
    fig_ctx.add_trace(go.Scatter(
        x=avg_ret["date"], y=avg_ret["cum"],
        name="ASX 10 Avg Cumulative Return", line=dict(color=BLUE, width=2),
    ), secondary_y=False)
    if not rate_row.empty:
        fig_ctx.add_hline(
            y=rate_row["value"].iloc[0],
            line_dash="dash", line_color=ORANGE,
            annotation_text=f"RBA Rate {rate_row['value'].iloc[0]}%",
            annotation_font_color="#F1F5F9",
        )
    fig_ctx.update_layout(
        plot_bgcolor=PLOT_BG, paper_bgcolor=PAPER_BG,
        font=dict(color="#F1F5F9", size=12), height=320,
        title=dict(text="ASX Portfolio Return vs RBA Cash Rate Context", font=dict(color="#F1F5F9")),
        legend=dict(bgcolor="rgba(17,24,39,0.8)", bordercolor="#1E3A5F",
                    borderwidth=1, font=dict(color="#F1F5F9")),
        margin=dict(l=20,r=20,t=40,b=20),
    )
    fig_ctx.update_xaxes(gridcolor=GRID_COL, tickfont=dict(color="#94A3B8"))
    fig_ctx.update_yaxes(gridcolor=GRID_COL, tickfont=dict(color="#94A3B8"))
    st.plotly_chart(fig_ctx, use_container_width=True)

    st.markdown("**Macro Data Table**")
    st.dataframe(
        macro_df[["indicator","value","unit","date","source"]].rename(columns={
            "indicator":"Indicator","value":"Value","unit":"Unit","date":"Date","source":"Source"
        }),
        use_container_width=True, hide_index=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — PIPELINE ARCHITECTURE
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("Pipeline Architecture & dbt Lineage")

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown("**🚀 Ingestion**\n\nPython script → 650 ASX OHLCV rows + 8 macro indicators → DuckDB raw tables")
    c2.markdown("**⚙️ Airflow**\n\nDAG: `financial_pipeline` · Schedule: 0 6 * * * · 3 tasks · LocalExecutor · Docker")
    c3.markdown("**🔄 dbt**\n\n4 models · 2 staging views · 2 mart tables · Window functions · Sector signals")
    c4.markdown("**✅ Validation**\n\n4 quality checks · Row counts · Null prices · Ticker completeness · Sector coverage")

    st.markdown("---")
    st.markdown("**dbt Model Lineage**")
    lineage = pd.DataFrame({
        "Model":       ["raw_asx_prices","raw_macro_indicators","stg_asx_prices","stg_macro_indicators","mart_asx_daily_metrics","mart_sector_summary"],
        "Type":        ["Source","Source","View","View","Table","Table"],
        "Layer":       ["Raw","Raw","Staging","Staging","Mart","Mart"],
        "Rows":        ["650","8","650","8","650","6"],
        "Key Columns": [
            "date, ticker, open, high, low, close, volume",
            "indicator, value, unit, date, source",
            "Cleaned + typed OHLCV",
            "Cleaned macro data",
            "MA5, MA20, volatility_20d, cum_return_pct, rel_volume",
            "avg_return, avg_volatility, sector_signal",
        ],
    })
    st.dataframe(lineage, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("**Simulated DAG Run History**")
    random.seed(42)
    run_dates = pd.date_range("2026-01-01", periods=30, freq="D")
    run_data  = pd.DataFrame({
        "date":       run_dates,
        "ingest_s":   [random.uniform(2, 5)    for _ in range(30)],
        "dbt_s":      [random.uniform(0.3, 0.8) for _ in range(30)],
        "validate_s": [random.uniform(0.1, 0.3) for _ in range(30)],
    })
    fig_runs = go.Figure()
    fig_runs.add_trace(go.Bar(x=run_data["date"], y=run_data["ingest_s"],   name="Ingest",   marker_color=BLUE))
    fig_runs.add_trace(go.Bar(x=run_data["date"], y=run_data["dbt_s"],      name="dbt Run",  marker_color=GREEN))
    fig_runs.add_trace(go.Bar(x=run_data["date"], y=run_data["validate_s"], name="Validate", marker_color=PURPLE))
    fig_runs = dark_layout(fig_runs, "Simulated Pipeline Run Duration per Task (seconds)", 320)
    fig_runs.update_layout(barmode="stack")
    fig_runs.update_yaxes(ticksuffix="s")
    st.plotly_chart(fig_runs, use_container_width=True)

    st.markdown("**Tech Stack**")
    cols = st.columns(6)
    stack = [
        ("Apache Airflow","2.9.1","Orchestration"),
        ("dbt-core","1.8.7","Transformation"),
        ("DuckDB","1.5.3","Analytics DB"),
        ("Docker","29.4.0","Containerisation"),
        ("Streamlit","1.58","Dashboard"),
        ("Plotly","6.8","Visualisation"),
    ]
    for col,(tool,ver,role) in zip(cols,stack):
        col.markdown(f"**{tool}**\n\n`v{ver}`\n\n{role}")

st.markdown("---")
st.markdown("""
<div class="footer">
    Pipeline: Apache Airflow · dbt · DuckDB · Docker &nbsp;·&nbsp;
    Dashboard: Streamlit · Plotly &nbsp;·&nbsp;
    <a href="https://github.com/fahadamjad009/de1-airflow-dbt-duckdb-pipeline" style="color:#3B82F6">GitHub ↗</a>
</div>
""", unsafe_allow_html=True)