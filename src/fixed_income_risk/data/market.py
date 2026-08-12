from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from fixed_income_risk.data.fred import FredKeyMissing, fetch_oas_history, latest_oas
from fixed_income_risk.data.treasury import get_treasury_curve


@dataclass
class MarketData:
    treasury_curve: pd.DataFrame
    oas_history: pd.DataFrame | None
    latest_oas_bps: dict[str, float]
    treasury_source: str
    credit_source: str


def load_market_data(prefer_live_treasury: bool = True) -> MarketData:
    curve, curve_source = get_treasury_curve(prefer_live=prefer_live_treasury)
    try:
        history = fetch_oas_history()
        oas = latest_oas(history)
        credit_source = "live FRED"
    except FredKeyMissing:
        history = None
        oas = {}
        credit_source = "missing FRED key"
    return MarketData(
        treasury_curve=curve,
        oas_history=history,
        latest_oas_bps=oas,
        treasury_source=curve_source,
        credit_source=credit_source,
    )
