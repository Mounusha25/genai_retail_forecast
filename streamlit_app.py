"""
streamlit_app.py
----------------
Demo UI for the GenAI Retail Forecasting Engine.

Launch:
    .venv/bin/streamlit run streamlit_app.py
    # or:  make ui

Requires the FastAPI backend to be running on localhost:8080.
"""
from __future__ import annotations

import os
import time
from datetime import datetime

import plotly.graph_objects as go
import requests
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Retail Forecasting Engine",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8080")

# ── Colour palette ────────────────────────────────────────────────────────────
BLUE   = "#1f77b4"
ORANGE = "#ff7f0e"
GREY   = "#adb5bd"

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Header gradient bar */
    [data-testid="stAppViewContainer"] > .main {
        background: #f8f9fa;
    }
    .hero-banner {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 100%);
        padding: 1.6rem 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
    .hero-banner h1 { margin: 0; font-size: 1.8rem; }
    .hero-banner p  { margin: 0.3rem 0 0; opacity: 0.85; font-size: 0.95rem; }

    /* Metric cards */
    .metric-card {
        background: white;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        box-shadow: 0 1px 4px rgba(0,0,0,.08);
        text-align: center;
    }
    .metric-card .value { font-size: 2rem; font-weight: 700; color: #1e3a5f; }
    .metric-card .label { font-size: 0.8rem; color: #6c757d; margin-top: 0.2rem; }

    /* Narrative box */
    .narrative-box {
        background: white;
        border-left: 4px solid #2d6a9f;
        border-radius: 0 8px 8px 0;
        padding: 1.2rem 1.5rem;
        box-shadow: 0 1px 4px rgba(0,0,0,.08);
        white-space: pre-wrap;
        font-size: 0.95rem;
        line-height: 1.7;
        color: #212529;
    }

    /* Status badge */
    .badge-ok      { background: #d4edda; color: #155724; padding: 2px 10px;
                     border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
    .badge-error   { background: #f8d7da; color: #721c24; padding: 2px 10px;
                     border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
    .badge-warning { background: #fff3cd; color: #856404; padding: 2px 10px;
                     border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── API helpers ───────────────────────────────────────────────────────────────

@st.cache_data(ttl=120, show_spinner=False)
def fetch_forecasts(product_id: str) -> dict | None:
    try:
        resp = requests.get(f"{API_BASE}/v1/forecasts/{product_id}", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except requests.RequestException:
        pass
    return None


@st.cache_data(ttl=60, show_spinner=False)
def fetch_narrative(product_id: str) -> dict | None:
    try:
        resp = requests.get(f"{API_BASE}/v1/narrative/{product_id}", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except requests.RequestException:
        pass
    return None


@st.cache_data(ttl=30, show_spinner=False)
def fetch_health() -> dict:
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except requests.RequestException:
        pass
    return {"status": "unreachable", "db": "error"}


@st.cache_data(ttl=300, show_spinner=False)
def fetch_store_list() -> list[str]:
    """Return a sorted list of store IDs by probing a known range."""
    return [f"STORE_{i:04d}" for i in range(1, 1116)]


# ── Layout helpers ────────────────────────────────────────────────────────────

def _health_badge(status: str) -> str:
    if status == "ok":
        return '<span class="badge-ok">● Healthy</span>'
    if status == "unreachable":
        return '<span class="badge-error">✖ Unreachable</span>'
    return '<span class="badge-warning">⚠ Degraded</span>'


def _build_forecast_chart(forecasts: list[dict]) -> go.Figure:
    dates  = [r["forecast_date"] for r in forecasts]
    units  = [r["forecast_units"] for r in forecasts]
    lowers = [r.get("ci_lower") for r in forecasts]
    uppers = [r.get("ci_upper") for r in forecasts]

    fig = go.Figure()

    # Confidence interval band
    if any(v is not None for v in uppers):
        fig.add_trace(go.Scatter(
            x=dates + dates[::-1],
            y=uppers + lowers[::-1],
            fill="toself",
            fillcolor="rgba(31,119,180,0.12)",
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            name="80% CI",
            showlegend=True,
        ))

    # Forecast line
    fig.add_trace(go.Scatter(
        x=dates,
        y=units,
        mode="lines+markers",
        line=dict(color=BLUE, width=2.5),
        marker=dict(size=5),
        name="Forecast Units",
        hovertemplate="<b>%{x}</b><br>Units: %{y:,.0f}<extra></extra>",
    ))

    fig.update_layout(
        title=None,
        xaxis_title="Date",
        yaxis_title="Forecasted Units Sold",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=380,
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="#e9ecef"),
    )
    return fig


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image(
        "https://img.icons8.com/color/96/combo-chart--v1.png",
        width=64,
    )
    st.title("Forecasting Engine")
    st.caption("GenAI · BigQuery ML · FastAPI")

    st.divider()

    # Health status
    health = fetch_health()
    st.markdown("**API Status**")
    st.markdown(_health_badge(health.get("status", "error")), unsafe_allow_html=True)
    st.markdown("**Database**")
    st.markdown(_health_badge(health.get("db", "error")), unsafe_allow_html=True)

    st.divider()

    store_list = fetch_store_list()
    selected_store = st.selectbox(
        "Select Store",
        options=store_list,
        index=0,
        help="1,115 Rossmann stores forecasted for the next 30 days.",
    )

    st.divider()
    st.caption(
        "**Stack**\n"
        "- BigQuery ML (ARIMA_PLUS)\n"
        "- LangChain + Groq LLaMA-3.3\n"
        "- FAISS RAG index\n"
        "- FastAPI + PostgreSQL\n"
        "- Apache Beam ETL"
    )

# ── Hero banner ───────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="hero-banner">
        <h1>📈 Retail Demand Forecasting &amp; AI Narrative Engine</h1>
        <p>30-day ARIMA_PLUS forecasts with GPT-powered executive summaries &mdash;
           currently viewing <strong>{selected_store}</strong></p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_forecast, tab_narrative, tab_about = st.tabs(
    ["📊 Demand Forecast", "🤖 AI Narrative", "ℹ️ About the Project"]
)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Forecast
# ═══════════════════════════════════════════════════════════════════════════════
with tab_forecast:
    with st.spinner(f"Loading forecasts for {selected_store}…"):
        data = fetch_forecasts(selected_store)

    if data is None:
        st.error(
            f"Could not load forecasts for **{selected_store}**. "
            "Make sure the API is running (`make run` or `docker compose up -d`) "
            "and forecasts have been synced (`make sync-forecasts`)."
        )
    else:
        forecasts = data.get("forecasts", [])

        if not forecasts:
            st.warning("No forecast rows found for this store.")
        else:
            # ── KPI row ────────────────────────────────────────────────────
            units_vals = [f["forecast_units"] for f in forecasts]
            avg_daily  = sum(units_vals) / len(units_vals)
            total_30d  = sum(units_vals)
            peak_day   = max(forecasts, key=lambda r: r["forecast_units"])
            low_day    = min(forecasts, key=lambda r: r["forecast_units"])

            k1, k2, k3, k4 = st.columns(4)
            with k1:
                st.markdown(
                    f'<div class="metric-card">'
                    f'<div class="value">{avg_daily:,.0f}</div>'
                    f'<div class="label">Avg Daily Units</div></div>',
                    unsafe_allow_html=True,
                )
            with k2:
                st.markdown(
                    f'<div class="metric-card">'
                    f'<div class="value">{total_30d:,.0f}</div>'
                    f'<div class="label">30-Day Total</div></div>',
                    unsafe_allow_html=True,
                )
            with k3:
                st.markdown(
                    f'<div class="metric-card">'
                    f'<div class="value">{peak_day["forecast_units"]:,.0f}</div>'
                    f'<div class="label">Peak Day ({peak_day["forecast_date"]})</div></div>',
                    unsafe_allow_html=True,
                )
            with k4:
                st.markdown(
                    f'<div class="metric-card">'
                    f'<div class="value">{low_day["forecast_units"]:,.0f}</div>'
                    f'<div class="label">Low Day ({low_day["forecast_date"]})</div></div>',
                    unsafe_allow_html=True,
                )

            st.divider()

            # ── Chart ──────────────────────────────────────────────────────
            st.plotly_chart(
                _build_forecast_chart(forecasts),
                use_container_width=True,
                config={"displayModeBar": False},
            )

            # ── Raw data table ─────────────────────────────────────────────
            with st.expander("View raw forecast data"):
                st.dataframe(
                    forecasts,
                    column_config={
                        "forecast_date":  st.column_config.DateColumn("Date"),
                        "forecast_units": st.column_config.NumberColumn("Units", format="%.0f"),
                        "ci_lower":       st.column_config.NumberColumn("CI Lower", format="%.0f"),
                        "ci_upper":       st.column_config.NumberColumn("CI Upper", format="%.0f"),
                    },
                    hide_index=True,
                    use_container_width=True,
                )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — AI Narrative
# ═══════════════════════════════════════════════════════════════════════════════
with tab_narrative:
    col_txt, col_meta = st.columns([3, 1])

    with col_txt:
        st.subheader("Executive Summary")
        st.caption(
            "Generated by **LLaMA 3.3·70B** (Groq) grounded with RAG context "
            "from Rossmann business documents and ARIMA_PLUS forecast data."
        )

    with col_meta:
        if st.button("🔄 Refresh narrative", use_container_width=True):
            fetch_narrative.clear()
            st.rerun()

    with st.spinner(f"Loading narrative for {selected_store}…"):
        narrative_data = fetch_narrative(selected_store)

    if narrative_data is None:
        st.info(
            f"No narrative found for **{selected_store}** yet.\n\n"
            "Run the following to generate narratives:\n"
            "```bash\n"
            f"make sync-narratives\n"
            "# or for a single store:\n"
            f".venv/bin/python scripts/sync_narratives.py --product {selected_store}\n"
            "```"
        )
    else:
        st.markdown(
            f'<div class="narrative-box">{narrative_data["summary"]}</div>',
            unsafe_allow_html=True,
        )
        generated_at = narrative_data.get("generated_at", "")
        if generated_at:
            try:
                dt = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
                st.caption(f"Generated at {dt.strftime('%Y-%m-%d %H:%M UTC')}")
            except ValueError:
                st.caption(f"Generated at {generated_at}")

    st.divider()

    # ── Live generation ────────────────────────────────────────────────────
    st.subheader("Generate narrative now")
    st.caption(
        "This calls the local Python chain directly (Groq API + FAISS). "
        "First call loads the embedding model (~3 s)."
    )

    if st.button(f"⚡ Generate narrative for {selected_store}", use_container_width=False):
        forecast_data = fetch_forecasts(selected_store)
        if forecast_data is None or not forecast_data.get("forecasts"):
            st.error("No forecast data found — cannot generate narrative.")
        else:
            with st.spinner("Calling Groq LLaMA 3.3·70B…"):
                try:
                    import sys
                    from pathlib import Path

                    sys.path.insert(0, str(Path(__file__).resolve().parent))
                    from dotenv import load_dotenv  # type: ignore[import]
                    load_dotenv(Path(__file__).resolve().parent / ".env", override=False)

                    from rag.narrative_chain import NarrativeChain  # type: ignore[import]

                    chain = NarrativeChain()
                    rows  = forecast_data["forecasts"]
                    text_out = chain.generate(selected_store, rows)
                    st.markdown(
                        f'<div class="narrative-box">{text_out}</div>',
                        unsafe_allow_html=True,
                    )
                    st.success("Narrative generated! Run `make sync-narratives` to persist all stores.")
                except Exception as exc:
                    st.error(f"Generation failed: {exc}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — About the Project
# ═══════════════════════════════════════════════════════════════════════════════
with tab_about:
    col_arch, col_stack = st.columns([3, 2])

    with col_arch:
        st.subheader("System Architecture")
        st.markdown(
            """
            ```
            Raw Sales CSV (Rossmann, 844 K rows)
                    │
                    ▼
            Apache Beam ETL (DirectRunner / Dataflow)
                    │  clean · validate · deduplicate
                    ▼
            BigQuery  ──  retail_forecasting.sales_clean
                    │
                    ▼
            BigQuery ML  ARIMA_PLUS
                    │  train → 30-day forecasts per store
                    ▼
            forecasts_30d  (BQ view)
                    │
            ┌───────┴────────┐
            │                │
            ▼                ▼
        PostgreSQL        FAISS Index
        forecasts &       RAG corpus
        narratives        (HuggingFace
        tables            all-MiniLM-L6)
                                │
                                ▼
                        LangChain + Groq LLaMA 3.3·70B
                                │
                                ▼
                        Executive narrative
                                │
                        FastAPI  (:8080)
                                │
                        Streamlit UI  (:8501)
            ```
            """
        )

    with col_stack:
        st.subheader("Technology Stack")
        st.markdown(
            """
            | Layer | Technology |
            |---|---|
            | Data ingestion | Apache Beam |
            | Data warehouse | BigQuery |
            | Forecasting | BigQuery ML (ARIMA_PLUS) |
            | Embeddings | HuggingFace `all-MiniLM-L6-v2` |
            | Vector store | FAISS |
            | LLM | Groq · LLaMA 3.3·70B |
            | Orchestration | LangChain LCEL |
            | Backend API | FastAPI + asyncpg |
            | Database | PostgreSQL (Docker) |
            | UI | Streamlit + Plotly |
            | Cloud | GCP (BigQuery, Dataflow, GCS) |
            """
        )

        st.subheader("Dataset")
        st.markdown(
            """
            **Rossmann Store Sales** (Kaggle)\n
            - 1,115 drug stores across Germany\n
            - 844,338 sales records (2013–2015)\n
            - 30-day horizon per store (33,450 forecast rows)\n
            """
        )

    st.divider()
    st.subheader("Quick-start commands")
    st.code(
        """# 1. Start infrastructure
make up              # PostgreSQL via Docker

# 2. Build FAISS index
make build-index

# 3. Start the API
make run             # FastAPI on :8080

# 4. Sync forecasts from BigQuery
make sync-forecasts

# 5. Generate and persist narratives
make sync-narratives  # first 20 stores

# 6. Launch this UI
make ui              # Streamlit on :8501
""",
        language="bash",
    )

    st.subheader("API endpoints")
    st.code(
        f"""curl {API_BASE}/health
curl {API_BASE}/v1/forecasts/STORE_0001
curl {API_BASE}/v1/narrative/STORE_0001""",
        language="bash",
    )
