from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
load_dotenv(ROOT / ".env")

from fixed_income_risk.pipeline import run_analytics  # noqa: E402

st.set_page_config(page_title="Fixed Income Risk Dashboard", layout="wide")

st.title("Fixed Income Risk Dashboard")
st.caption(
    "Hypothetical positions • real public market inputs • self-implemented fixed-income analytics"
)

with st.sidebar:
    st.header("Methodology")
    st.write(
        "Positions are hypothetical. Treasury curve inputs come from U.S. Treasury daily par yields. "
        "Corporate OAS inputs come from FRED ICE BofA rating indices. Bond-level yields and prices are model-implied."
    )
    st.write(
        "Sector beta is a rating-mix spread beta proxy, estimated from daily changes in each sector's "
        "portfolio rating blend versus the broad investment-grade OAS series."
    )
    st.divider()
    st.write("FRED API key detected" if os.getenv("FRED_API_KEY") else "FRED API key not detected")

if not os.getenv("FRED_API_KEY"):
    st.error(
        "Set FRED_API_KEY in .env (local) or Streamlit secrets/environment variables (deployment) to run credit analytics."
    )
    st.code("cp .env.example .env\n# then edit .env and add FRED_API_KEY=...", language="bash")
    st.stop()

try:
    bundle = run_analytics()
except Exception as exc:
    st.exception(exc)
    st.stop()

s = bundle.portfolio_summary
cols = st.columns(6)
cols[0].metric("Market value", f"${s['market_value']/1_000_000:.2f}M")
cols[1].metric("Model yield", f"{s['yield_pct']:.2f}%")
cols[2].metric("Eff. duration", f"{s['duration']:.2f}y")
cols[3].metric("DV01", f"${s['dv01']:,.0f}")
cols[4].metric("DTS", f"{s['dts']:.1f}")
cols[5].metric("Convexity", f"{s['convexity']:.1f}")

st.caption(
    f"Settlement: {bundle.settlement_date} | Treasury source: {bundle.market.treasury_source} | "
    f"Credit source: {bundle.market.credit_source}"
)

tabs = st.tabs(["Positioning", "DTS & Beta", "Curve Risk", "Bond-Level Analytics", "Data & Assumptions"])

with tabs[0]:
    left, right = st.columns(2)
    with left:
        st.subheader("Sector weights")
        sector_fig = px.bar(
            bundle.sectors.sort_values("weight_pct"),
            x="weight_pct",
            y="sector",
            orientation="h",
            labels={"weight_pct": "Portfolio weight (%)", "sector": ""},
        )
        st.plotly_chart(sector_fig, use_container_width=True)
    with right:
        st.subheader("Active weights vs AGG proxy")
        active = bundle.benchmark.copy().sort_values("active_weight_pct")
        active_fig = px.bar(
            active,
            x="active_weight_pct",
            y="sector",
            orientation="h",
            labels={"active_weight_pct": "Portfolio - benchmark (pp)", "sector": ""},
        )
        st.plotly_chart(active_fig, use_container_width=True)
    st.subheader("Quality mix")
    st.dataframe(bundle.quality, use_container_width=True, hide_index=True)

with tabs[1]:
    beta = bundle.betas.copy()
    merged = bundle.sectors.merge(beta, on="sector", how="left")
    st.subheader("Sector risk budget")
    st.dataframe(
        merged[["sector", "weight_pct", "duration", "oas_bps", "dts_contribution", "sector_beta", "observations"]],
        use_container_width=True,
        hide_index=True,
    )
    fig = px.scatter(
        merged[merged["sector"] != "Treasury"],
        x="sector_beta",
        y="dts_contribution",
        size="weight_pct",
        hover_name="sector",
        labels={"sector_beta": "Rating-mix spread beta", "dts_contribution": "DTS contribution"},
    )
    st.plotly_chart(fig, use_container_width=True)
    st.info(
        "DTS = spread duration × OAS. Sector beta here is not a vendor sector beta; it is a transparent proxy based on the portfolio's rating mix and FRED rating-level OAS histories."
    )

with tabs[2]:
    st.subheader("Key-rate duration contribution")
    krd_cols = [c for c in bundle.positions.columns if c.endswith("_contribution") and c.startswith("krd_")]
    krd = pd.DataFrame(
        {
            "tenor": [c.replace("krd_", "").replace("_contribution", "").upper() for c in krd_cols],
            "duration_contribution": [bundle.positions[c].sum() for c in krd_cols],
        }
    )
    st.plotly_chart(
        px.bar(krd, x="tenor", y="duration_contribution", labels={"duration_contribution": "Duration contribution"}),
        use_container_width=True,
    )
    st.subheader("Curve shock P&L")
    st.dataframe(bundle.scenario_summary, use_container_width=True, hide_index=True)
    st.plotly_chart(
        px.bar(bundle.scenario_summary, x="scenario", y="estimated_pnl", labels={"estimated_pnl": "Estimated P&L ($)"}),
        use_container_width=True,
    )
    chosen = st.selectbox("Position detail for scenario", bundle.scenario_summary["scenario"].tolist())
    detail = bundle.scenario_positions[bundle.scenario_positions["scenario"] == chosen].sort_values("estimated_pnl")
    st.dataframe(detail, use_container_width=True, hide_index=True)

with tabs[3]:
    display_cols = [
        "position_id", "security_name", "sector", "rating", "maturity_years", "oas_bps",
        "model_ytm_pct", "model_price", "market_value", "macaulay_duration", "modified_duration",
        "effective_duration", "spread_duration", "dts", "dv01", "krd_2y", "krd_5y", "krd_10y", "krd_30y"
    ]
    st.dataframe(bundle.positions[display_cols], use_container_width=True, hide_index=True)

with tabs[4]:
    st.subheader("Treasury curve")
    st.plotly_chart(
        px.line(bundle.market.treasury_curve, x="tenor_years", y="yield_pct", markers=True),
        use_container_width=True,
    )
    st.dataframe(bundle.market.treasury_curve, use_container_width=True, hide_index=True)
    st.subheader("Assumptions")
    st.markdown(
        """
- The portfolio and face amounts are hypothetical and are not client or employer positions.
- Treasury curve observations are real public U.S. Treasury daily par yields.
- Rating OAS observations are pulled locally from FRED/ICE BofA series; raw ICE data is not bundled in this repo.
- Corporate bond yield is modeled as interpolated Treasury par yield at maturity plus rating-level OAS.
- Prices, durations, DV01 and KRD are therefore model analytics, not vendor marks.
- Bonds are treated as fixed-rate, non-callable bullet securities with simplified ACT/365.25 timing.
- Scenario P&L is first-order key-rate-duration attribution; it is not a full revaluation engine.
"""
    )
