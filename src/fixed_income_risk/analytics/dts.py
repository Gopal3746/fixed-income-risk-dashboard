from __future__ import annotations

import numpy as np
import pandas as pd


def rating_mix_sector_beta(
    enriched: pd.DataFrame,
    oas_history: pd.DataFrame,
    min_observations: int = 60,
) -> pd.DataFrame:
    """Estimate sector spread beta from each sector's portfolio rating mix.

    This is deliberately a proxy: each corporate sector is represented as the
    market-value-weighted blend of the rating-level ICE BofA OAS histories in
    that sector. Beta is the OLS slope of daily changes in that proxy against
    daily changes in the broad IG OAS series.
    """
    hist = oas_history.copy().sort_values("date")
    broad = hist[["date", "IG"]].dropna().copy()
    broad["broad_change"] = broad["IG"].diff()

    rows = []
    for sector, group in enriched.groupby("sector"):
        if (group["asset_class"] == "Treasury").all():
            rows.append(
                {
                    "sector": sector,
                    "sector_beta": 0.0,
                    "observations": 0,
                    "method": "Treasury beta fixed at 0",
                }
            )
            continue

        corp = group[group["asset_class"] == "Corporate"].copy()
        rating_weights = (
            corp.groupby("rating")["market_value"].sum() / corp["market_value"].sum()
        )
        proxy = hist[["date"]].copy()
        proxy["sector_proxy"] = 0.0
        available_weight = 0.0
        for rating, weight in rating_weights.items():
            if rating in hist.columns:
                proxy["sector_proxy"] += hist[rating] * float(weight)
                available_weight += float(weight)
        if available_weight <= 0:
            rows.append(
                {
                    "sector": sector,
                    "sector_beta": np.nan,
                    "observations": 0,
                    "method": "No matching rating history",
                }
            )
            continue
        proxy["sector_proxy"] /= available_weight
        proxy["sector_change"] = proxy["sector_proxy"].diff()
        joined = proxy.merge(broad[["date", "broad_change"]], on="date", how="inner").dropna()
        n = len(joined)
        if n < min_observations or joined["broad_change"].var() == 0:
            beta = np.nan
        else:
            beta = float(
                np.cov(joined["sector_change"], joined["broad_change"], ddof=1)[0, 1]
                / np.var(joined["broad_change"], ddof=1)
            )
        rows.append(
            {
                "sector": sector,
                "sector_beta": beta,
                "observations": n,
                "method": "rating-mix spread beta vs broad IG OAS changes",
            }
        )
    return pd.DataFrame(rows)
