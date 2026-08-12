import pandas as pd

from fixed_income_risk.analytics.scenarios import scenario_pnl
from fixed_income_risk.analytics.dts import rating_mix_sector_beta


def test_parallel_rate_rise_produces_negative_pnl():
    positions = pd.DataFrame(
        [
            {
                "position_id": "x",
                "security_name": "x",
                "sector": "Industrial",
                "market_value": 1_000_000.0,
                "krd_2y": 1.0,
                "krd_5y": 2.0,
                "krd_10y": 2.0,
                "krd_30y": 0.5,
            }
        ]
    )
    summary, _ = scenario_pnl(positions, {"up": {2.0: 50, 5.0: 50, 10.0: 50, 30.0: 50}})
    assert summary.loc[0, "estimated_pnl"] < 0


def test_rating_mix_beta_recovers_simple_slope():
    dates = pd.date_range("2026-01-01", periods=100, freq="D")
    moves = pd.Series(([1.0, 2.0, -1.0, 0.5, 3.0] * 20), dtype=float)
    ig = moves.cumsum()
    hist = pd.DataFrame({"date": dates, "IG": ig, "A": ig * 1.5, "BBB": ig * 2.0})
    enriched = pd.DataFrame(
        [
            {"sector": "Industrial", "asset_class": "Corporate", "rating": "A", "market_value": 60.0},
            {"sector": "Industrial", "asset_class": "Corporate", "rating": "BBB", "market_value": 40.0},
        ]
    )
    beta = rating_mix_sector_beta(enriched, hist, min_observations=10)
    # 60% * 1.5 + 40% * 2.0 = 1.7
    assert abs(beta.loc[0, "sector_beta"] - 1.7) < 1e-10
