"""
streamlit_app.py — Professional Business Intelligence Dashboard
GenAI Retail Forecasting Engine · Rossmann Store Sales (1,115 stores)

Launch:  .venv/bin/streamlit run streamlit_app.py   (or: make ui)
"""

from __future__ import annotations

import io
import os
from datetime import datetime
from itertools import cycle

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
import psycopg2.extras
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv(override=False)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Rossmann Retail Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8080")
DB_URL_RAW = os.getenv("DATABASE_URL", "postgresql+asyncpg://retail:retail@localhost:5432/retail")

# ── Colour system ──────────────────────────────────────────────────────────────
C_BLUE = "#2563EB"
C_RED = "#DC2626"
C_GREEN = "#16A34A"
C_PURPLE = "#9333EA"
C_ORANGE = "#EA580C"
C_TEAL = "#0891B2"
C_AMBER = "#D97706"

PALETTE = [C_BLUE, C_RED, C_GREEN, C_PURPLE, C_ORANGE]
PALETTE_FILL = [
    "rgba(37,99,235,0.10)",
    "rgba(220,38,38,0.10)",
    "rgba(22,163,74,0.10)",
    "rgba(147,51,234,0.10)",
    "rgba(234,88,12,0.10)",
]

TIER_COLORS = {"High (>60K)": C_GREEN, "Mid (20-60K)": C_BLUE, "Low (<20K)": C_AMBER}

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

[data-testid="stAppViewContainer"] > .main { background: #F0F4F8; }
[data-testid="stSidebar"]          { background: #0D1B2A; border-right: 1px solid #1E3448; }
[data-testid="stSidebar"] *        { color: #C8D6E5 !important; }
[data-testid="stSidebar"] h3       { color: #E2EBF3 !important; font-size:1rem; }

/* ── Sidebar collapse button (inside sidebar, on hover) ── */
[data-testid="stSidebarCollapseButton"] {
    opacity: 1 !important;
    display: flex !important;
    visibility: visible !important;
}
[data-testid="stSidebarCollapseButton"] button {
    background: rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: white !important;
}
[data-testid="stSidebarCollapseButton"] button svg {
    fill: #C8D6E5 !important;
    stroke: #C8D6E5 !important;
}

/* ── Expand sidebar button in header (shown when sidebar is CLOSED) ── */
[data-testid="stExpandSidebarButton"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
}
[data-testid="stExpandSidebarButton"] button {
    background: #1A3A5C !important;
    border: 2px solid #2563EB !important;
    border-radius: 10px !important;
    padding: 8px 10px !important;
    box-shadow: 0 4px 16px rgba(37,99,235,.5) !important;
    color: white !important;
}
[data-testid="stExpandSidebarButton"] button svg {
    fill: white !important;
    stroke: white !important;
    width: 20px !important;
    height: 20px !important;
}
[data-testid="stExpandSidebarButton"] button:hover {
    background: #2563EB !important;
    box-shadow: 0 4px 20px rgba(37,99,235,.7) !important;
}

/* ── Hero ── */
.hero {
    background: linear-gradient(135deg, #0D1B2A 0%, #1A3A5C 55%, #2563EB 100%);
    padding: 1.6rem 2rem 1.4rem; border-radius: 14px; color: white;
    margin-bottom: 1.2rem; position: relative; overflow: hidden;
}
.hero::before {
    content: ""; position: absolute; right: -60px; top: -60px;
    width: 220px; height: 220px; border-radius: 50%;
    background: rgba(255,255,255,0.04);
}
.hero h1 { margin:0; font-size:1.6rem; font-weight:700; letter-spacing:-0.02em; }
.hero p  { margin:0.3rem 0 0; opacity:0.72; font-size:0.88rem; }
.pill {
    display:inline-block; background:rgba(255,255,255,0.14);
    border:1px solid rgba(255,255,255,0.22); border-radius:20px;
    padding:2px 12px; font-size:0.82rem; margin-top:0.5rem; font-weight:600;
}

/* ── Section card ── */
.card {
    background:white; border-radius:12px;
    padding:1.2rem 1.4rem; box-shadow:0 1px 8px rgba(0,0,0,.06);
    margin-bottom:0.8rem;
}
.card-title { font-size:0.78rem; text-transform:uppercase; letter-spacing:0.06em;
              color:#64748B; margin-bottom:0.7rem; font-weight:600; }

/* ── KPI cards ── */
.kpi { background:white; border-radius:12px; padding:1.1rem 1.3rem;
       box-shadow:0 1px 8px rgba(0,0,0,.06); border-top:3px solid #2563EB; }
.kpi.orange { border-color:#EA580C; }
.kpi.green  { border-color:#16A34A; }
.kpi.purple { border-color:#9333EA; }
.kpi.red    { border-color:#DC2626; }
.kpi.teal   { border-color:#0891B2; }
.kpi .val   { font-size:1.85rem; font-weight:700; color:#0F172A; line-height:1.1; }
.kpi .lbl   { font-size:0.70rem; color:#64748B; text-transform:uppercase;
              letter-spacing:0.06em; margin-top:0.25rem; }
.kpi .sub   { font-size:0.76rem; font-weight:600; margin-top:0.2rem; }
.up   { color:#16A34A; } .down { color:#DC2626; } .flat { color:#64748B; }

/* ── Insight box ── */
.insight {
    background:#EFF6FF; border-left:4px solid #2563EB; border-radius:0 8px 8px 0;
    padding:0.75rem 1.1rem; font-size:0.85rem; color:#1E3A5F;
    margin:0.6rem 0; line-height:1.6;
}

/* ── Narrative box ── */
.narrative-box {
    background:white; border-radius:12px; padding:1.6rem 2rem;
    box-shadow:0 1px 8px rgba(0,0,0,.06); font-size:0.93rem;
    line-height:1.9; color:#1E293B; white-space:pre-wrap;
    border-left:5px solid #2563EB;
}

/* ── Badges ── */
.badge-ok   { background:#DCFCE7;color:#15803D;padding:3px 12px;border-radius:20px;font-size:0.77rem;font-weight:600; }
.badge-err  { background:#FEE2E2;color:#B91C1C;padding:3px 12px;border-radius:20px;font-size:0.77rem;font-weight:600; }
.badge-warn { background:#FEF9C3;color:#A16207;padding:3px 12px;border-radius:20px;font-size:0.77rem;font-weight:600; }
.tier-high   { background:#DCFCE7;color:#15803D;padding:2px 10px;border-radius:12px;font-size:0.75rem;font-weight:600; }
.tier-mid    { background:#DBEAFE;color:#1D4ED8;padding:2px 10px;border-radius:12px;font-size:0.75rem;font-weight:600; }
.tier-low    { background:#FEF9C3;color:#A16207;padding:2px 10px;border-radius:12px;font-size:0.75rem;font-weight:600; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap:6px; }
.stTabs [data-baseweb="tab"] {
    background:white; border-radius:8px 8px 0 0;
    padding:8px 18px; font-weight:500; font-size:0.88rem;
}
.stTabs [aria-selected="true"] { background:#2563EB !important; color:white !important; }

#MainMenu, footer, header { visibility:hidden; }
</style>
""",
    unsafe_allow_html=True,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Database helpers (sync psycopg2 — analytics-only queries from dashboard)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _pg_dsn() -> str:
    """Convert SQLAlchemy URL to plain psycopg2 DSN (strips driver + query params)."""
    url = DB_URL_RAW.replace("postgresql+asyncpg://", "postgresql://")
    return url.split("?")[0]


def _pg_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    try:
        conn = psycopg2.connect(_pg_dsn())
        df = pd.read_sql(sql, conn, params=params)
        conn.close()
        return df
    except Exception as exc:
        st.warning(f"DB query failed: {exc}")
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def load_fleet_summary() -> pd.DataFrame:
    return _pg_query("""
        SELECT
            product_id,
            SUM(forecast_units)          AS total_30d,
            AVG(forecast_units)          AS avg_daily,
            MAX(forecast_units)          AS peak_day,
            AVG(ci_upper - ci_lower)     AS avg_ci_width
        FROM forecasts
        GROUP BY product_id
        ORDER BY total_30d DESC
    """)


@st.cache_data(ttl=300, show_spinner=False)
def load_dow_pattern() -> pd.DataFrame:
    return _pg_query("""
        SELECT
            EXTRACT(DOW FROM forecast_date)::int    AS dow,
            TO_CHAR(forecast_date, 'Dy')            AS day_abbr,
            ROUND(AVG(forecast_units)::numeric, 1)  AS avg_units,
            ROUND(SUM(forecast_units)::numeric, 0)  AS total_units
        FROM forecasts
        GROUP BY 1, 2
        ORDER BY 1
    """)


@st.cache_data(ttl=300, show_spinner=False)
def load_fleet_daily_trend() -> pd.DataFrame:
    return _pg_query("""
        SELECT
            forecast_date,
            SUM(forecast_units)          AS total_units,
            AVG(forecast_units)          AS avg_per_store,
            COUNT(DISTINCT product_id)   AS stores_active
        FROM forecasts
        WHERE forecast_date >= '2015-08-01'
        GROUP BY forecast_date
        ORDER BY forecast_date
    """)


@st.cache_data(ttl=300, show_spinner=False)
def load_weekly_fleet() -> pd.DataFrame:
    return _pg_query("""
        SELECT
            DATE_TRUNC('week', forecast_date)::date AS week_start,
            SUM(forecast_units)                     AS total_units,
            AVG(forecast_units)                     AS avg_per_store
        FROM forecasts
        WHERE forecast_date >= '2015-08-01'
        GROUP BY 1
        ORDER BY 1
    """)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API helpers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@st.cache_data(ttl=120, show_spinner=False)
def fetch_forecasts(product_id: str) -> dict | None:
    try:
        r = requests.get(f"{API_BASE}/v1/forecasts/{product_id}", timeout=10)
        return r.json() if r.status_code == 200 else None
    except requests.RequestException:
        return None


@st.cache_data(ttl=60, show_spinner=False)
def fetch_narrative(product_id: str) -> dict | None:
    try:
        r = requests.get(f"{API_BASE}/v1/narrative/{product_id}", timeout=10)
        return r.json() if r.status_code == 200 else None
    except requests.RequestException:
        return None


@st.cache_data(ttl=30, show_spinner=False)
def fetch_health() -> dict:
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        return r.json() if r.status_code == 200 else {"status": "error", "db": "error"}
    except requests.RequestException:
        return {"status": "unreachable", "db": "error"}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Chart helpers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _bg_fig(h: int = 360) -> dict:
    """Common Plotly layout dict: white bg, tight margins."""
    return dict(
        height=h,
        margin=dict(l=0, r=0, t=8, b=0),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )


def _tier(val: float) -> str:
    if val >= 60_000:
        return "High (>60K)"
    if val >= 20_000:
        return "Mid (20-60K)"
    return "Low (<20K)"


def _badge(status: str) -> str:
    cls = {"ok": "badge-ok", "unreachable": "badge-err"}.get(status, "badge-warn")
    icon = {"ok": "●", "unreachable": "✖"}.get(status, "⚠")
    label = {"ok": "Live", "unreachable": "Down"}.get(status, "Degraded")
    return f'<span class="{cls}">{icon} {label}</span>'


def _delta_html(pct: float, label: str) -> str:
    if pct > 2:
        return f'<span class="sub up">▲ {pct:+.1f}% {label}</span>'
    if pct < -2:
        return f'<span class="sub down">▼ {pct:+.1f}% {label}</span>'
    return f'<span class="sub flat">→ Stable {label}</span>'


def _risk_html(vol: float) -> str:
    if vol < 15:
        return '<span class="sub up">▼ Low risk</span>'
    if vol < 30:
        return '<span class="sub flat">◆ Medium risk</span>'
    return '<span class="sub down">▲ High risk</span>'


def _pct_rank(store_total: float, all_totals: pd.Series) -> float:
    return (all_totals <= store_total).mean() * 100


def _df_from_api(forecasts: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(forecasts)
    df["forecast_date"] = pd.to_datetime(df["forecast_date"])
    return df.sort_values("forecast_date").reset_index(drop=True)


def _weekly_agg(df: pd.DataFrame) -> pd.DataFrame:
    df2 = df.copy()
    df2["week"] = df2["forecast_date"].dt.to_period("W").apply(lambda p: str(p.start_time.date()))
    return (
        df2.groupby("week")
        .agg(
            forecast_units=("forecast_units", "sum"),
            ci_lower=("ci_lower", "sum"),
            ci_upper=("ci_upper", "sum"),
        )
        .reset_index()
        .rename(columns={"week": "forecast_date"})
    )


# Clear stale localStorage collapsed state so sidebar always starts open
st.iframe(
    """
<script>
  Object.keys(window.parent.localStorage)
    .filter(function(k){ return k.startsWith('stSidebarCollapsed'); })
    .forEach(function(k){ window.parent.localStorage.removeItem(k); });
</script>
""",
    height=0,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Sidebar
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with st.sidebar:
    st.markdown("### 📊 Retail Intelligence")
    st.markdown("<small style='color:#64748B'>Rossmann · 1,115 stores · ARIMA_PLUS</small>", unsafe_allow_html=True)
    st.markdown("---")

    health = fetch_health()
    c1, c2 = st.columns(2)
    c1.markdown("**API**")
    c1.markdown(_badge(health.get("status", "error")), unsafe_allow_html=True)
    c2.markdown("**DB**")
    c2.markdown(_badge(health.get("db", "error")), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("##### 🏪 Store Selector")
    store_search = st.text_input("Search", value="", placeholder="e.g. 0042 or 1114")
    all_stores = [f"STORE_{i:04d}" for i in range(1, 1116)]
    filtered = [s for s in all_stores if store_search.upper() in s] if store_search else all_stores
    primary_store = st.selectbox("Primary store", options=filtered, index=0, label_visibility="collapsed")

    st.markdown("---")
    st.markdown("##### Compare (optional)")
    compare_stores = st.multiselect(
        "Add stores to overlay",
        options=[s for s in all_stores if s != primary_store],
        max_selections=2,
        placeholder="Up to 2 more…",
    )

    st.markdown("---")
    view_mode = st.radio("Granularity", ["Daily", "Weekly"], horizontal=True)

    st.markdown("---")
    st.markdown(
        "<small style='color:#475569'>**Stack**<br>BigQuery ML · ARIMA_PLUS<br>"
        "LLaMA 3.3·70B via Groq<br>FAISS RAG · LangChain<br>"
        "FastAPI · PostgreSQL · Beam</small>",
        unsafe_allow_html=True,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Pre-load fleet data (all cached at module level for dashboard speed)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

fleet_df = load_fleet_summary()
dow_df = load_dow_pattern()
trend_df = load_fleet_daily_trend()
weekly_fleet = load_weekly_fleet()

# Per-store API data for selected stores
all_selected = [primary_store] + compare_stores
store_api: dict[str, list[dict]] = {}
for sid in all_selected:
    raw = fetch_forecasts(sid)
    if raw and raw.get("forecasts"):
        store_api[sid] = raw["forecasts"]

primary_fc = store_api.get(primary_store, [])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Hero header
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

compare_pill = f" + {', '.join(compare_stores)}" if compare_stores else ""
st.markdown(
    f"""
<div class="hero">
  <h1>Rossmann Retail Demand Intelligence</h1>
  <p>30-day ARIMA_PLUS forecasts · LLaMA 3.3·70B AI narratives · 1,115 stores across Germany</p>
  <span class="pill">📍 {primary_store}{compare_pill}</span>
  <span class="pill" style="margin-left:8px">🗓 Horizon: Aug–Sep 2015</span>
</div>
""",
    unsafe_allow_html=True,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Tabs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

tab_network, tab_store, tab_compare, tab_narrative, tab_about = st.tabs(
    [
        "🌐 Network Overview",
        "📊 Store Forecast",
        "🔀 Compare",
        "🤖 AI Narrative",
        "ℹ️ About",
    ]
)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — NETWORK OVERVIEW  (fleet-wide business intelligence)
# ══════════════════════════════════════════════════════════════════════════════

with tab_network:
    if fleet_df.empty:
        st.error("Cannot connect to database. Ensure `make up` is running.")
    else:
        # ── Fleet KPIs ──────────────────────────────────────────────────────
        fleet_total = fleet_df["total_30d"].sum()
        fleet_avg_store = fleet_df["total_30d"].mean()
        fleet_peak_store = fleet_df.loc[fleet_df["total_30d"].idxmax(), "product_id"]
        fleet_peak_val = fleet_df["total_30d"].max()
        pct_high = (fleet_df["total_30d"] >= 60_000).mean() * 100
        pct_low = (fleet_df["total_30d"] < 20_000).mean() * 100

        k1, k2, k3, k4, k5 = st.columns(5)
        k1.markdown(
            f'<div class="kpi"><div class="val">{fleet_total / 1e6:.2f}M</div>'
            f'<div class="lbl">Network 30-Day Units</div>'
            f'<span class="sub flat">1,115 stores combined</span></div>',
            unsafe_allow_html=True,
        )
        k2.markdown(
            f'<div class="kpi orange"><div class="val">{fleet_avg_store:,.0f}</div>'
            f'<div class="lbl">Avg Units / Store</div>'
            f'<span class="sub flat">30-day total</span></div>',
            unsafe_allow_html=True,
        )
        k3.markdown(
            f'<div class="kpi green"><div class="val">{fleet_peak_val / 1000:.0f}K</div>'
            f'<div class="lbl">Top Store 30-Day</div>'
            f'<span class="sub up">{fleet_peak_store}</span></div>',
            unsafe_allow_html=True,
        )
        k4.markdown(
            f'<div class="kpi teal"><div class="val">{pct_high:.0f}%</div>'
            f'<div class="lbl">High-Volume Stores</div>'
            f'<span class="sub up">&gt;60K units/30d</span></div>',
            unsafe_allow_html=True,
        )
        k5.markdown(
            f'<div class="kpi red"><div class="val">{pct_low:.0f}%</div>'
            f'<div class="lbl">Low-Volume Stores</div>'
            f'<span class="sub down">&lt;20K units/30d</span></div>',
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        # ── Row 1: Fleet demand trend + Day-of-week pattern ─────────────────
        col_trend, col_dow = st.columns([3, 2])

        with col_trend:
            st.markdown(
                '<div class="card"><div class="card-title">📈 Fleet-wide Daily Demand (Aug–Sep 2015)</div>',
                unsafe_allow_html=True,
            )
            if not trend_df.empty:
                fig_trend = go.Figure()
                fig_trend.add_trace(
                    go.Scatter(
                        x=trend_df["forecast_date"].astype(str),
                        y=trend_df["total_units"] / 1000,
                        mode="lines",
                        name="Total Units (K)",
                        line=dict(color=C_BLUE, width=2.5),
                        fill="tozeroy",
                        fillcolor="rgba(37,99,235,0.08)",
                        hovertemplate="<b>%{x}</b><br>Fleet total: %{y:.1f}K units<extra></extra>",
                    )
                )
                fig_trend.update_layout(
                    **_bg_fig(260),
                    xaxis=dict(showgrid=False, tickangle=-30),
                    yaxis=dict(gridcolor="#F1F5F9", title="Units (thousands)"),
                    hovermode="x unified",
                )
                st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        with col_dow:
            st.markdown(
                '<div class="card"><div class="card-title">📅 Avg Daily Units by Day of Week</div>',
                unsafe_allow_html=True,
            )
            if not dow_df.empty:
                dow_map = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}
                dow_sorted = dow_df.copy()
                dow_sorted["sort_key"] = dow_sorted["day_abbr"].map(dow_map)
                dow_sorted = dow_sorted.sort_values("sort_key")
                colors_dow = [
                    C_GREEN
                    if v == dow_sorted["avg_units"].max()
                    else C_RED
                    if v == dow_sorted["avg_units"].min()
                    else C_BLUE
                    for v in dow_sorted["avg_units"]
                ]
                fig_dow = go.Figure(
                    go.Bar(
                        x=dow_sorted["day_abbr"],
                        y=dow_sorted["avg_units"],
                        marker_color=colors_dow,
                        text=dow_sorted["avg_units"].apply(lambda v: f"{v:.0f}"),
                        textposition="outside",
                        textfont=dict(size=10),
                        hovertemplate="%{x}<br>Avg: %{y:.1f} units/store<extra></extra>",
                    )
                )
                fig_dow.update_layout(
                    **_bg_fig(260),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(gridcolor="#F1F5F9", title="Avg units/store"),
                    bargap=0.25,
                )
                st.plotly_chart(fig_dow, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Row 2: Top 15 stores + Store tier donut ──────────────────────────
        col_top, col_dist = st.columns([3, 2])

        with col_top:
            st.markdown(
                '<div class="card"><div class="card-title">🏆 Top 15 Stores — 30-Day Forecast Volume</div>',
                unsafe_allow_html=True,
            )
            top15 = fleet_df.head(15).copy()
            top15["tier"] = top15["total_30d"].apply(_tier)
            bar_colors = top15["tier"].map(TIER_COLORS).tolist()
            fig_top = go.Figure(
                go.Bar(
                    x=top15["total_30d"] / 1000,
                    y=top15["product_id"],
                    orientation="h",
                    marker_color=bar_colors,
                    text=top15["total_30d"].apply(lambda v: f"{v / 1000:.1f}K"),
                    textposition="outside",
                    textfont=dict(size=10),
                    hovertemplate="<b>%{y}</b><br>30-day total: %{x:.1f}K units<extra></extra>",
                )
            )
            fig_top.update_layout(
                **_bg_fig(340),
                xaxis=dict(showgrid=False, title="Units (thousands)"),
                yaxis=dict(autorange="reversed", showgrid=False),
            )
            st.plotly_chart(fig_top, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        with col_dist:
            st.markdown(
                '<div class="card"><div class="card-title">🥧 Store Performance Segmentation</div>',
                unsafe_allow_html=True,
            )
            fleet_df["tier"] = fleet_df["total_30d"].apply(_tier)
            tier_counts = (
                fleet_df.groupby("tier")
                .agg(stores=("product_id", "count"), avg_30d=("total_30d", "mean"))
                .reset_index()
            )
            fig_pie = go.Figure(
                go.Pie(
                    labels=tier_counts["tier"],
                    values=tier_counts["stores"],
                    hole=0.52,
                    marker_colors=[TIER_COLORS.get(t, C_BLUE) for t in tier_counts["tier"]],
                    textinfo="label+percent",
                    textfont_size=11,
                    hovertemplate="<b>%{label}</b><br>Stores: %{value}<br>Share: %{percent}<extra></extra>",
                )
            )
            fig_pie.update_layout(
                **_bg_fig(200),
                showlegend=False,
                annotations=[dict(text="<b>1,115</b><br>stores", x=0.5, y=0.5, font_size=13, showarrow=False)],
            )
            st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

            tier_summary = tier_counts.copy()
            tier_summary["avg_30d"] = tier_summary["avg_30d"].apply(lambda v: f"{v:,.0f}")
            tier_summary.columns = ["Segment", "# Stores", "Avg 30-Day Units"]
            st.dataframe(tier_summary, hide_index=True, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Row 3: Volume histogram + Weekly fleet bars ──────────────────────
        col_hist, col_wk = st.columns([3, 2])

        with col_hist:
            st.markdown(
                '<div class="card"><div class="card-title">📊 Store Volume Distribution (30-Day Forecast)</div>',
                unsafe_allow_html=True,
            )
            fig_hist = go.Figure(
                go.Histogram(
                    x=fleet_df["total_30d"] / 1000,
                    nbinsx=40,
                    marker_color=C_BLUE,
                    marker_line_color="white",
                    marker_line_width=0.5,
                    opacity=0.85,
                    hovertemplate="Range: %{x:.1f}K units<br>Stores: %{y}<extra></extra>",
                )
            )
            p25 = fleet_df["total_30d"].quantile(0.25) / 1000
            p50 = fleet_df["total_30d"].quantile(0.50) / 1000
            p75 = fleet_df["total_30d"].quantile(0.75) / 1000
            for val, label, col in [
                (p25, "P25", C_AMBER),
                (p50, "Median", C_GREEN),
                (p75, "P75", C_RED),
            ]:
                fig_hist.add_vline(
                    x=val,
                    line_dash="dash",
                    line_color=col,
                    line_width=1.5,
                    annotation_text=f"{label}: {val:.1f}K",
                    annotation_position="top right",
                    annotation_font_size=10,
                )
            fig_hist.update_layout(
                **_bg_fig(280),
                xaxis=dict(title="30-Day Units (thousands)", showgrid=False),
                yaxis=dict(title="# Stores", gridcolor="#F1F5F9"),
                bargap=0.05,
            )
            st.plotly_chart(fig_hist, use_container_width=True, config={"displayModeBar": False})
            st.markdown(
                """
<div class="insight">
💡 <b>Insight:</b> The distribution is right-skewed — 50% of stores forecast below
<b>19.9K units</b> in 30 days, while a small high-volume tier (17 stores) drives
disproportionate network revenue above 60K units.
</div>
""",
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with col_wk:
            st.markdown(
                '<div class="card"><div class="card-title">🗓 Weekly Fleet Demand (Aggregate)</div>',
                unsafe_allow_html=True,
            )
            if not weekly_fleet.empty:
                fig_wk = go.Figure(
                    go.Bar(
                        x=weekly_fleet["week_start"].astype(str),
                        y=weekly_fleet["total_units"] / 1e6,
                        marker_color=[
                            C_GREEN if i == weekly_fleet["total_units"].idxmax() else C_BLUE for i in weekly_fleet.index
                        ],
                        text=weekly_fleet["total_units"].apply(lambda v: f"{v / 1e6:.2f}M"),
                        textposition="outside",
                        textfont=dict(size=10),
                        hovertemplate="Week of %{x}<br>Total: %{y:.2f}M units<extra></extra>",
                    )
                )
                fig_wk.update_layout(
                    **_bg_fig(280),
                    xaxis=dict(showgrid=False, tickangle=-20),
                    yaxis=dict(gridcolor="#F1F5F9", title="Units (millions)"),
                    bargap=0.3,
                )
                st.plotly_chart(fig_wk, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Row 4: Risk vs Volume scatter ────────────────────────────────────
        st.markdown(
            '<div class="card"><div class="card-title">🎯 Forecast Confidence: Risk vs Volume (all 1,115 stores)</div>',
            unsafe_allow_html=True,
        )
        scatter_df = fleet_df.copy()
        scatter_df["tier"] = scatter_df["total_30d"].apply(_tier)
        scatter_df["vol_pct"] = scatter_df["avg_ci_width"] / scatter_df["avg_daily"] * 100
        fig_scatter = px.scatter(
            scatter_df,
            x="total_30d",
            y="vol_pct",
            color="tier",
            color_discrete_map=TIER_COLORS,
            opacity=0.65,
            labels={
                "total_30d": "30-Day Total Forecast (units)",
                "vol_pct": "Uncertainty % (CI width / avg)",
            },
            custom_data=["product_id"],
        )
        fig_scatter.update_traces(
            marker=dict(size=6),
            hovertemplate="<b>%{customdata[0]}</b><br>30d total: %{x:,.0f}<br>Uncertainty: %{y:.1f}%<extra></extra>",
        )
        fig_scatter.update_layout(
            **_bg_fig(300),
            xaxis=dict(showgrid=False),
            yaxis=dict(gridcolor="#F1F5F9"),
            legend=dict(orientation="h", y=1.08, x=0),
        )
        st.plotly_chart(fig_scatter, use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            """
<div class="insight">
💡 <b>Insight:</b> High-volume stores (green) tend to have <em>lower relative uncertainty</em> —
large established stores have more stable demand patterns. Low-volume stores show wider
confidence intervals relative to their forecast, indicating higher operational risk.
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — STORE FORECAST  (single store deep-dive)
# ══════════════════════════════════════════════════════════════════════════════

with tab_store:
    if not primary_fc:
        st.error(f"No forecast data for **{primary_store}**. Ensure API is running and forecasts are synced.")
    else:
        df = _df_from_api(primary_fc)
        plot_df = (
            _weekly_agg(df)
            if view_mode == "Weekly"
            else df.copy().assign(forecast_date=df["forecast_date"].dt.strftime("%Y-%m-%d"))
        )

        avg_daily = df["forecast_units"].mean()
        total_30d = df["forecast_units"].sum()
        peak_row = df.loc[df["forecast_units"].idxmax()]
        week1_avg = df.head(7)["forecast_units"].mean()
        week4_avg = df.tail(7)["forecast_units"].mean()
        trend_pct = (week4_avg - week1_avg) / week1_avg * 100
        ci_vol_pct = (df["ci_upper"] - df["ci_lower"]).mean() / avg_daily * 100 if df["ci_upper"].notna().any() else 0.0

        pct_rank = _pct_rank(total_30d, fleet_df["total_30d"]) if not fleet_df.empty else 0.0
        store_tier = _tier(total_30d)
        tier_class_map = {
            "High (>60K)": "tier-high",
            "Mid (20-60K)": "tier-mid",
            "Low (<20K)": "tier-low",
        }

        # ── 5 KPI cards ─────────────────────────────────────────────────────
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.markdown(
            f'<div class="kpi"><div class="val">{avg_daily:,.0f}</div>'
            f'<div class="lbl">Avg Daily Units</div>'
            f"{_delta_html(trend_pct, 'vs wk1')}</div>",
            unsafe_allow_html=True,
        )
        k2.markdown(
            f'<div class="kpi orange"><div class="val">{total_30d:,.0f}</div>'
            f'<div class="lbl">30-Day Total</div>'
            f'<span class="sub flat">30-day horizon</span></div>',
            unsafe_allow_html=True,
        )
        k3.markdown(
            f'<div class="kpi green"><div class="val">{peak_row["forecast_units"]:,.0f}</div>'
            f'<div class="lbl">Peak Day</div>'
            f'<span class="sub flat">{peak_row["forecast_date"].strftime("%b %d")}</span></div>',
            unsafe_allow_html=True,
        )
        k4.markdown(
            f'<div class="kpi purple"><div class="val">{ci_vol_pct:.0f}%</div>'
            f'<div class="lbl">Forecast Uncertainty</div>'
            f"{_risk_html(ci_vol_pct)}</div>",
            unsafe_allow_html=True,
        )
        k5.markdown(
            f'<div class="kpi teal"><div class="val">{pct_rank:.0f}'
            f'<sup style="font-size:1rem">th</sup></div>'
            f'<div class="lbl">Network Percentile</div>'
            f'<span class="{tier_class_map[store_tier]}">{store_tier}</span></div>',
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        # ── Row 1: Forecast line + Weekly bars ──────────────────────────────
        col_line, col_wbar = st.columns([3, 2])

        with col_line:
            st.markdown(
                '<div class="card"><div class="card-title">📈 30-Day Demand Forecast with 80% Confidence Interval</div>',
                unsafe_allow_html=True,
            )
            fig = go.Figure()
            if df["ci_upper"].notna().any():
                x_ci = list(plot_df["forecast_date"]) + list(plot_df["forecast_date"])[::-1]
                y_ci = list(plot_df["ci_upper"]) + list(plot_df["ci_lower"])[::-1]
                fig.add_trace(
                    go.Scatter(
                        x=x_ci,
                        y=y_ci,
                        fill="toself",
                        fillcolor=PALETTE_FILL[0],
                        line=dict(color="rgba(0,0,0,0)"),
                        hoverinfo="skip",
                        name="80% CI",
                    )
                )
            fig.add_trace(
                go.Scatter(
                    x=plot_df["forecast_date"],
                    y=plot_df["forecast_units"],
                    mode="lines+markers",
                    line=dict(color=C_BLUE, width=2.5),
                    marker=dict(size=5),
                    name=primary_store,
                    hovertemplate="<b>%{x}</b><br>Units: %{y:,.0f}<extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=[peak_row["forecast_date"].strftime("%Y-%m-%d")],
                    y=[peak_row["forecast_units"]],
                    mode="markers+text",
                    marker=dict(color=C_GREEN, size=12, symbol="star"),
                    text=["Peak"],
                    textposition="top center",
                    textfont=dict(size=10, color=C_GREEN),
                    name="Peak",
                    hoverinfo="skip",
                )
            )
            fig.add_hline(
                y=avg_daily,
                line_dash="dot",
                line_color=C_AMBER,
                line_width=1.5,
                annotation_text=f"Avg {avg_daily:,.0f}",
                annotation_position="right",
                annotation_font_size=10,
            )
            fig.update_layout(
                **_bg_fig(320),
                hovermode="x unified",
                legend=dict(orientation="h", y=1.08, x=0),
                xaxis=dict(showgrid=False, tickangle=-30),
                yaxis=dict(gridcolor="#F1F5F9", title="Units"),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        with col_wbar:
            st.markdown(
                '<div class="card"><div class="card-title">🗓 Weekly Demand Totals</div>', unsafe_allow_html=True
            )
            wk = _weekly_agg(df)
            fig_wk = go.Figure(
                go.Bar(
                    x=wk["forecast_date"],
                    y=wk["forecast_units"],
                    marker_color=[C_GREEN if v == wk["forecast_units"].max() else C_BLUE for v in wk["forecast_units"]],
                    marker_line_width=0,
                    text=wk["forecast_units"].apply(lambda v: f"{v:,.0f}"),
                    textposition="outside",
                    textfont=dict(size=10),
                    hovertemplate="Week of %{x}<br>Total: %{y:,.0f} units<extra></extra>",
                )
            )
            fig_wk.update_layout(
                **_bg_fig(320),
                xaxis=dict(showgrid=False, tickangle=-20),
                yaxis=dict(gridcolor="#F1F5F9", title="Units"),
                bargap=0.35,
            )
            st.plotly_chart(fig_wk, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Row 2: DOW pattern + Benchmark/WoW ──────────────────────────────
        col_sdow, col_bench = st.columns([2, 3])

        with col_sdow:
            st.markdown(
                '<div class="card"><div class="card-title">📅 Demand by Day of Week (this store)</div>',
                unsafe_allow_html=True,
            )
            store_dow = df.copy()
            store_dow["dow"] = store_dow["forecast_date"].dt.day_name().str[:3]
            dow_order_map = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}
            store_dow_agg = (
                store_dow.groupby("dow")["forecast_units"]
                .mean()
                .reset_index()
                .assign(sort_k=lambda x: x["dow"].map(dow_order_map))
                .sort_values("sort_k")
            )
            sdow_colors = [
                C_GREEN
                if v == store_dow_agg["forecast_units"].max()
                else C_RED
                if v == store_dow_agg["forecast_units"].min()
                else C_BLUE
                for v in store_dow_agg["forecast_units"]
            ]
            fig_sdow = go.Figure(
                go.Bar(
                    x=store_dow_agg["dow"],
                    y=store_dow_agg["forecast_units"],
                    marker_color=sdow_colors,
                    marker_line_width=0,
                    text=store_dow_agg["forecast_units"].apply(lambda v: f"{v:.0f}"),
                    textposition="outside",
                    textfont=dict(size=10),
                    hovertemplate="%{x}<br>Avg: %{y:.1f} units<extra></extra>",
                )
            )
            fig_sdow.update_layout(
                **_bg_fig(280),
                xaxis=dict(showgrid=False),
                bargap=0.3,
                yaxis=dict(gridcolor="#F1F5F9", title="Avg units"),
            )
            st.plotly_chart(fig_sdow, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        with col_bench:
            st.markdown(
                '<div class="card"><div class="card-title">📍 Network Benchmark + Week-over-Week Trend</div>',
                unsafe_allow_html=True,
            )
            if not fleet_df.empty:
                p25v = fleet_df["total_30d"].quantile(0.25)
                p50v = fleet_df["total_30d"].quantile(0.50)
                p75v = fleet_df["total_30d"].quantile(0.75)
                p90v = fleet_df["total_30d"].quantile(0.90)

                # Bullet chart
                fig_bullet = go.Figure()
                for end, zone_col in [
                    (p25v, "#FEF9C3"),
                    (p50v, "#DBEAFE"),
                    (p75v, "#DCFCE7"),
                    (p90v, "#BBF7D0"),
                ]:
                    fig_bullet.add_shape(
                        type="rect",
                        x0=0,
                        x1=end / 1000,
                        y0=-0.4,
                        y1=0.4,
                        fillcolor=zone_col,
                        line_width=0,
                    )
                fig_bullet.add_trace(
                    go.Bar(
                        x=[total_30d / 1000],
                        y=[""],
                        orientation="h",
                        marker_color=TIER_COLORS[store_tier],
                        width=0.35,
                        hovertemplate=f"{primary_store}: {total_30d:,.0f} units — {pct_rank:.0f}th pctile<extra></extra>",
                    )
                )
                for val, bl_label in [(p50v, "Median"), (p75v, "P75")]:
                    fig_bullet.add_vline(
                        x=val / 1000,
                        line_dash="dash",
                        line_color="#475569",
                        line_width=1.5,
                        annotation_text=f"{bl_label}: {val / 1000:.1f}K",
                        annotation_font_size=9,
                        annotation_position="top",
                    )
                fig_bullet.update_layout(
                    **_bg_fig(130),
                    xaxis=dict(title="30-Day Forecast Units (thousands)", showgrid=False),
                    yaxis=dict(showticklabels=False),
                    showlegend=False,
                )
                st.plotly_chart(fig_bullet, use_container_width=True, config={"displayModeBar": False})

                # Week-over-week bars
                st.markdown(
                    '<div class="card-title" style="margin-top:.8rem">📆 Week-over-Week Volume Trend</div>',
                    unsafe_allow_html=True,
                )
                n_weeks = min(4, len(df) // 7 + 1)
                wk_vals = [
                    df.iloc[i * 7 : (i + 1) * 7]["forecast_units"].sum()
                    for i in range(n_weeks)
                    if len(df.iloc[i * 7 : (i + 1) * 7]) > 0
                ]
                wk_labels = [f"Week {i + 1}" for i in range(len(wk_vals))]
                wow_colors = [
                    C_BLUE if i == 0 else (C_GREEN if wk_vals[i] >= wk_vals[i - 1] else C_RED)
                    for i in range(len(wk_vals))
                ]
                fig_wow = go.Figure(
                    go.Bar(
                        x=wk_labels,
                        y=wk_vals,
                        marker_color=wow_colors,
                        marker_line_width=0,
                        text=[f"{v:,.0f}" for v in wk_vals],
                        textposition="outside",
                        textfont=dict(size=11),
                        hovertemplate="%{x}<br>Total: %{y:,.0f} units<extra></extra>",
                    )
                )
                fig_wow.update_layout(
                    **_bg_fig(180),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(gridcolor="#F1F5F9", title="Units"),
                    bargap=0.4,
                )
                st.plotly_chart(fig_wow, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        # ── CSV export ───────────────────────────────────────────────────────
        with st.expander("📋 Raw forecast data + export", expanded=False):
            exp_df = df.copy()
            exp_df["forecast_date"] = exp_df["forecast_date"].dt.strftime("%Y-%m-%d")
            exp_df["dow"] = pd.to_datetime(exp_df["forecast_date"]).dt.day_name()
            st.dataframe(
                exp_df,
                column_config={
                    "forecast_date": st.column_config.TextColumn("Date"),
                    "forecast_units": st.column_config.NumberColumn("Units", format="%.0f"),
                    "ci_lower": st.column_config.NumberColumn("CI Lower", format="%.0f"),
                    "ci_upper": st.column_config.NumberColumn("CI Upper", format="%.0f"),
                    "dow": st.column_config.TextColumn("Day"),
                },
                hide_index=True,
                use_container_width=True,
            )
            csv_buf = io.StringIO()
            exp_df.to_csv(csv_buf, index=False)
            st.download_button(
                "⬇ Download CSV",
                data=csv_buf.getvalue(),
                file_name=f"{primary_store}_forecast.csv",
                mime="text/csv",
            )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — COMPARE
# ══════════════════════════════════════════════════════════════════════════════

with tab_compare:
    if len(store_api) < 2:
        st.info("Select at least one additional store in the sidebar **Compare** section.")
    else:
        st.markdown("#### Multi-Store Forecast Overlay")
        fig_cmp = go.Figure()
        clr_cycle = cycle(zip(PALETTE, PALETTE_FILL))

        for sid in all_selected:
            if sid not in store_api:
                continue
            col_c, fill_c = next(clr_cycle)
            sdf = _df_from_api(store_api[sid])
            pdf = (
                _weekly_agg(sdf)
                if view_mode == "Weekly"
                else sdf.copy().assign(forecast_date=sdf["forecast_date"].dt.strftime("%Y-%m-%d"))
            )
            if sdf["ci_upper"].notna().any():
                x_ci = list(pdf["forecast_date"]) + list(pdf["forecast_date"])[::-1]
                y_ci = list(pdf["ci_upper"]) + list(pdf["ci_lower"])[::-1]
                fig_cmp.add_trace(
                    go.Scatter(
                        x=x_ci,
                        y=y_ci,
                        fill="toself",
                        fillcolor=fill_c,
                        line=dict(color="rgba(0,0,0,0)"),
                        hoverinfo="skip",
                        showlegend=False,
                    )
                )
            fig_cmp.add_trace(
                go.Scatter(
                    x=pdf["forecast_date"],
                    y=pdf["forecast_units"],
                    mode="lines+markers",
                    line=dict(color=col_c, width=2.5),
                    marker=dict(size=5),
                    name=sid,
                    hovertemplate=f"<b>{sid}</b><br>%{{x}}<br>Units: %{{y:,.0f}}<extra></extra>",
                )
            )

        fig_cmp.update_layout(
            **_bg_fig(380),
            hovermode="x unified",
            legend=dict(orientation="h", y=1.06, x=0),
            xaxis=dict(showgrid=False, tickangle=-30),
            yaxis=dict(gridcolor="#F1F5F9", title="Units"),
        )
        st.plotly_chart(fig_cmp, use_container_width=True, config={"displayModeBar": False})

        st.markdown("#### Store Comparison Summary")
        rows = []
        for sid in all_selected:
            if sid not in store_api:
                continue
            sdf = _df_from_api(store_api[sid])
            w1 = sdf.head(7)["forecast_units"].mean()
            w4 = sdf.tail(7)["forecast_units"].mean()
            ci_w = (sdf["ci_upper"] - sdf["ci_lower"]).mean() if sdf["ci_upper"].notna().any() else 0
            pr = _pct_rank(sdf["forecast_units"].sum(), fleet_df["total_30d"]) if not fleet_df.empty else 0
            rows.append(
                {
                    "Store": sid,
                    "Tier": _tier(sdf["forecast_units"].sum()),
                    "Avg Daily": f"{sdf['forecast_units'].mean():,.0f}",
                    "30-Day Total": f"{sdf['forecast_units'].sum():,.0f}",
                    "Peak Units": f"{sdf['forecast_units'].max():,.0f}",
                    "Wk1→Wk4": f"{(w4 - w1) / w1 * 100:+.1f}%",
                    "Uncertainty": f"{ci_w / sdf['forecast_units'].mean() * 100:.0f}%",
                    "Pctile": f"{pr:.0f}th",
                }
            )
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — AI NARRATIVE
# ══════════════════════════════════════════════════════════════════════════════

with tab_narrative:
    hdr_col, ref_col = st.columns([4, 1])
    with hdr_col:
        st.markdown("### 🤖 AI Executive Summary")
        st.caption(f"**{primary_store}** · LLaMA 3.3·70B (Groq) + FAISS RAG on Rossmann business documents")
    with ref_col:
        if st.button("🔄 Refresh", use_container_width=True):
            fetch_narrative.clear()
            st.rerun()

    narrative_data = fetch_narrative(primary_store)
    if narrative_data:
        summary = narrative_data.get("summary", "")
        st.markdown(f'<div class="narrative-box">{summary}</div>', unsafe_allow_html=True)
        gen_at = narrative_data.get("generated_at", "")
        if gen_at:
            try:
                dt = datetime.fromisoformat(gen_at.replace("Z", "+00:00"))
                st.caption(f"Generated {dt.strftime('%Y-%m-%d %H:%M UTC')}")
            except ValueError:
                st.caption(f"Generated {gen_at}")
    else:
        st.info(f"No narrative for **{primary_store}** yet. Click below or run `make sync-narratives`.")

    st.markdown("---")
    st.markdown("#### ⚡ Generate live")
    st.caption("Calls Groq LLaMA 3.3·70B · ~5 seconds")
    if st.button(f"Generate narrative for {primary_store}", type="primary"):
        fc_data = fetch_forecasts(primary_store)
        if not fc_data or not fc_data.get("forecasts"):
            st.error("No forecast data — cannot generate narrative.")
        else:
            with st.spinner("Calling Groq API…"):
                try:
                    import sys
                    from pathlib import Path

                    sys.path.insert(0, str(Path(__file__).resolve().parent))
                    from rag.narrative_chain import NarrativeChain  # type: ignore[import]

                    chain = NarrativeChain()
                    text = chain.generate(primary_store, fc_data["forecasts"])
                    st.markdown(f'<div class="narrative-box">{text}</div>', unsafe_allow_html=True)
                    st.success("Done! Run `make sync-narratives` to persist.")
                except Exception as exc:
                    st.error(f"Generation failed: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — ABOUT
# ══════════════════════════════════════════════════════════════════════════════

with tab_about:
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown("#### System Architecture")
        st.code(
            """
Rossmann Sales CSV (844K rows, 1115 stores)
        │
        ▼
Apache Beam ETL ── clean · validate · dedup
DirectRunner (local)  /  Dataflow (cloud)
        │
        ▼
BigQuery ── retail_forecasting.sales_clean
        │
        ▼
BigQuery ML  ARIMA_PLUS
train → evaluate → 30-day forecast per store
        │
 ┌──────┴──────────────┐
 │                     │
 ▼                     ▼
PostgreSQL           FAISS Index
forecasts &          RAG corpus
narratives           HuggingFace
(Neon in prod)       all-MiniLM-L6
                          │
                          ▼
                  LangChain LCEL
                  + Groq LLaMA 3.3·70B
                          │
                          ▼
                  Executive Narrative
                          │
                  FastAPI backend (:8080)
                          │
                  Streamlit BI dashboard (:8501)
        """,
            language="text",
        )

    with c2:
        st.markdown("#### Technology Stack")
        st.markdown("""
| Layer | Tech |
|---|---|
| Ingestion | Apache Beam |
| Warehouse | BigQuery |
| Forecasting | BQML · ARIMA_PLUS |
| Embeddings | HuggingFace MiniLM-L6 |
| Vector store | FAISS |
| LLM | Groq · LLaMA 3.3·70B |
| Orchestration | LangChain LCEL |
| API | FastAPI · asyncpg |
| Database | PostgreSQL |
| CI/CD | GitHub Actions |
| Cloud | GCP (BQ · Dataflow · GCS) |
| UI | Streamlit · Plotly |
        """)
        st.markdown("#### Dataset")
        st.info(
            "**Rossmann Store Sales** (Kaggle)\n\n"
            "- 1,115 drug stores · Germany\n"
            "- 844,338 records (2013–2015)\n"
            "- 30-day forecast horizon\n"
            "- 33,450 total forecast rows"
        )

    st.markdown("---")
    st.markdown("#### Quick-start")
    st.code(
        """make up              # PostgreSQL
make build-index     # FAISS RAG index
make run             # FastAPI :8080
make sync-forecasts  # BQ → Postgres
make sync-narratives # AI narratives
make ui              # Streamlit :8501""",
        language="bash",
    )
