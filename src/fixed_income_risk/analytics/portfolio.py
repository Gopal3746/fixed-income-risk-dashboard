from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from fixed_income_risk.config import KEY_RATE_TENORS
from fixed_income_risk.math.bonds import (
    Bond,
    convexity,
    dv01_per_100,
    effective_duration,
    macaulay_duration,
    modified_duration,
    year_fraction,
)
from fixed_income_risk.math.curve import curve_price, interpolate_curve_yield, key_rate_durations


def enrich_positions(
    portfolio: pd.DataFrame,
    curve: pd.DataFrame,
    latest_oas_bps: dict[str, float],
    settlement_date: date | str,
) -> pd.DataFrame:
    rows = []
    for _, p in portfolio.iterrows():
        maturity_years = year_fraction(settlement_date, p["maturity_date"])
        spread_bps = 0.0 if p["asset_class"] == "Treasury" else latest_oas_bps[p["rating"]]
        treasury_yield_pct = interpolate_curve_yield(curve, maturity_years)
        model_ytm_pct = treasury_yield_pct + spread_bps / 100.0
        bond = Bond(
            coupon_rate=float(p["coupon_rate"]),
            maturity_date=pd.to_datetime(p["maturity_date"]).date(),
            face_value=100.0,
            frequency=int(p.get("frequency", 2)),
        )
        price = curve_price(bond, settlement_date, curve, spread_bps=spread_bps)
        market_value = price / 100.0 * float(p["face_value"])
        mac = macaulay_duration(bond, model_ytm_pct, settlement_date)
        mod = modified_duration(bond, model_ytm_pct, settlement_date)
        eff = effective_duration(bond, model_ytm_pct, settlement_date)
        conv = convexity(bond, model_ytm_pct, settlement_date)
        dv01 = dv01_per_100(bond, model_ytm_pct, settlement_date) / 100.0 * float(p["face_value"])
        krd = key_rate_durations(
            bond,
            settlement_date,
            curve,
            spread_bps,
            KEY_RATE_TENORS,
            bump_bps=1.0,
        )
        spread_duration = 0.0 if p["asset_class"] == "Treasury" else eff
        dts = spread_duration * spread_bps
        row = p.to_dict()
        row.update(
            {
                "maturity_years": maturity_years,
                "treasury_yield_pct": treasury_yield_pct,
                "oas_bps": spread_bps,
                "model_ytm_pct": model_ytm_pct,
                "model_price": price,
                "market_value": market_value,
                "macaulay_duration": mac,
                "modified_duration": mod,
                "effective_duration": eff,
                "convexity": conv,
                "dv01": dv01,
                "spread_duration": spread_duration,
                "dts": dts,
            }
        )
        for key, value in krd.items():
            row[f"krd_{int(key)}y"] = value
        rows.append(row)
    enriched = pd.DataFrame(rows)
    total_mv = enriched["market_value"].sum()
    enriched["portfolio_weight"] = enriched["market_value"] / total_mv
    enriched["dts_contribution"] = enriched["portfolio_weight"] * enriched["dts"]
    for key in KEY_RATE_TENORS:
        col = f"krd_{int(key)}y"
        enriched[f"{col}_contribution"] = enriched["portfolio_weight"] * enriched[col]
    return enriched


def portfolio_summary(enriched: pd.DataFrame) -> dict[str, float]:
    w = enriched["portfolio_weight"].to_numpy()
    return {
        "market_value": float(enriched["market_value"].sum()),
        "yield_pct": float(np.sum(w * enriched["model_ytm_pct"])),
        "duration": float(np.sum(w * enriched["effective_duration"])),
        "modified_duration": float(np.sum(w * enriched["modified_duration"])),
        "convexity": float(np.sum(w * enriched["convexity"])),
        "dv01": float(enriched["dv01"].sum()),
        "dts": float(np.sum(w * enriched["dts"])),
    }


def sector_summary(enriched: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        enriched.groupby("sector", dropna=False)
        .apply(
            lambda g: pd.Series(
                {
                    "market_value": g["market_value"].sum(),
                    "weight_pct": g["portfolio_weight"].sum() * 100.0,
                    "duration": np.average(g["effective_duration"], weights=g["market_value"]),
                    "oas_bps": np.average(g["oas_bps"], weights=g["market_value"]),
                    "dts_contribution": g["dts_contribution"].sum(),
                    "dv01": g["dv01"].sum(),
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )
    return grouped.sort_values("weight_pct", ascending=False).reset_index(drop=True)


def quality_summary(enriched: pd.DataFrame) -> pd.DataFrame:
    out = (
        enriched.groupby("rating", as_index=False)["market_value"].sum()
        .sort_values("market_value", ascending=False)
    )
    out["weight_pct"] = out["market_value"] / out["market_value"].sum() * 100.0
    return out


def benchmark_comparison(enriched: pd.DataFrame, benchmark: pd.DataFrame) -> pd.DataFrame:
    portfolio = sector_summary(enriched)[["sector", "weight_pct"]].rename(
        columns={"weight_pct": "portfolio_weight_pct"}
    )
    comparison = benchmark[["sector", "benchmark_weight_pct"]].merge(
        portfolio, on="sector", how="outer"
    )
    comparison[["benchmark_weight_pct", "portfolio_weight_pct"]] = comparison[
        ["benchmark_weight_pct", "portfolio_weight_pct"]
    ].fillna(0.0)
    comparison["active_weight_pct"] = (
        comparison["portfolio_weight_pct"] - comparison["benchmark_weight_pct"]
    )
    return comparison.sort_values("active_weight_pct", ascending=False).reset_index(drop=True)
