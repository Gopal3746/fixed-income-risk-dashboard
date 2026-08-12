from __future__ import annotations

import pandas as pd

from fixed_income_risk.config import KEY_RATE_TENORS

SCENARIOS_BPS = {
    "Parallel +50bp": {2.0: 50.0, 5.0: 50.0, 10.0: 50.0, 30.0: 50.0},
    "Bear steepener": {2.0: 20.0, 5.0: 35.0, 10.0: 50.0, 30.0: 65.0},
    "Bear flattener": {2.0: 65.0, 5.0: 50.0, 10.0: 35.0, 30.0: 20.0},
    "Bull steepener": {2.0: -65.0, 5.0: -50.0, 10.0: -35.0, 30.0: -20.0},
}


def scenario_pnl(
    enriched: pd.DataFrame,
    scenarios: dict[str, dict[float, float]] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    scenarios = scenarios or SCENARIOS_BPS
    position_rows = []
    portfolio_rows = []
    for name, shocks in scenarios.items():
        total_pnl = 0.0
        for _, row in enriched.iterrows():
            rate_move = 0.0
            for key in KEY_RATE_TENORS:
                krd = float(row[f"krd_{int(key)}y"])
                rate_move += krd * float(shocks[key]) / 10000.0
            pnl = -float(row["market_value"]) * rate_move
            total_pnl += pnl
            position_rows.append(
                {
                    "scenario": name,
                    "position_id": row["position_id"],
                    "security_name": row["security_name"],
                    "sector": row["sector"],
                    "estimated_pnl": pnl,
                }
            )
        mv = float(enriched["market_value"].sum())
        portfolio_rows.append(
            {
                "scenario": name,
                "estimated_pnl": total_pnl,
                "return_impact_pct": total_pnl / mv * 100.0,
            }
        )
    return pd.DataFrame(portfolio_rows), pd.DataFrame(position_rows)
