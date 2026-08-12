from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from fixed_income_risk.analytics.dts import rating_mix_sector_beta
from fixed_income_risk.analytics.portfolio import (
    benchmark_comparison,
    enrich_positions,
    portfolio_summary,
    quality_summary,
    sector_summary,
)
from fixed_income_risk.analytics.scenarios import scenario_pnl
from fixed_income_risk.config import DATA_DIR
from fixed_income_risk.data.market import MarketData, load_market_data


@dataclass
class AnalyticsBundle:
    market: MarketData
    positions: pd.DataFrame
    portfolio_summary: dict[str, float]
    sectors: pd.DataFrame
    quality: pd.DataFrame
    benchmark: pd.DataFrame
    betas: pd.DataFrame
    scenario_summary: pd.DataFrame
    scenario_positions: pd.DataFrame
    settlement_date: str


def load_portfolio(path: str | Path | None = None) -> pd.DataFrame:
    target = Path(path) if path else DATA_DIR / "sample_portfolio.csv"
    return pd.read_csv(target)


def run_analytics(
    settlement_date: str | None = None,
    prefer_live_treasury: bool = True,
) -> AnalyticsBundle:
    settlement_date = settlement_date or date.today().isoformat()
    market = load_market_data(prefer_live_treasury=prefer_live_treasury)
    if not market.latest_oas_bps:
        raise RuntimeError(
            "Credit analytics require FRED_API_KEY. Add the key to .env or your environment."
        )
    portfolio = load_portfolio()
    positions = enrich_positions(
        portfolio,
        market.treasury_curve,
        market.latest_oas_bps,
        settlement_date,
    )
    benchmark_cfg = pd.read_csv(DATA_DIR / "benchmark_proxy.csv")
    sectors = sector_summary(positions)
    quality = quality_summary(positions)
    benchmark = benchmark_comparison(positions, benchmark_cfg)
    betas = (
        rating_mix_sector_beta(positions, market.oas_history)
        if market.oas_history is not None
        else pd.DataFrame()
    )
    scen_summary, scen_positions = scenario_pnl(positions)
    return AnalyticsBundle(
        market=market,
        positions=positions,
        portfolio_summary=portfolio_summary(positions),
        sectors=sectors,
        quality=quality,
        benchmark=benchmark,
        betas=betas,
        scenario_summary=scen_summary,
        scenario_positions=scen_positions,
        settlement_date=settlement_date,
    )
