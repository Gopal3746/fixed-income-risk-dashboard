from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from fixed_income_risk.math.bonds import Bond, cashflow_schedule


def interpolate_curve_yield(curve: pd.DataFrame, tenor_years: float) -> float:
    x = curve["tenor_years"].astype(float).to_numpy()
    y = curve["yield_pct"].astype(float).to_numpy()
    return float(np.interp(tenor_years, x, y, left=y[0], right=y[-1]))


def curve_price(
    bond: Bond,
    settlement_date: date | str,
    curve: pd.DataFrame,
    spread_bps: float = 0.0,
    curve_shocks_bps: dict[float, float] | None = None,
) -> float:
    times, cashflows = cashflow_schedule(bond, settlement_date)
    if len(times) == 0:
        return 0.0
    shocks = curve_shocks_bps or {}
    rates = []
    for t in times:
        base_pct = interpolate_curve_yield(curve, float(t))
        shock_bps = interpolate_key_shock(float(t), shocks) if shocks else 0.0
        annual_rate = (base_pct / 100.0) + (spread_bps + shock_bps) / 10000.0
        rates.append(annual_rate)
    rates = np.asarray(rates)
    discount = (1.0 + rates / bond.frequency) ** (times * bond.frequency)
    return float(np.sum(cashflows / discount))


def interpolate_key_shock(tenor: float, shocks_bps: dict[float, float]) -> float:
    if not shocks_bps:
        return 0.0
    keys = np.array(sorted(float(k) for k in shocks_bps), dtype=float)
    vals = np.array([float(shocks_bps[k]) for k in keys], dtype=float)
    return float(np.interp(tenor, keys, vals, left=vals[0], right=vals[-1]))


def key_rate_durations(
    bond: Bond,
    settlement_date: date | str,
    curve: pd.DataFrame,
    spread_bps: float,
    key_tenors: list[float],
    bump_bps: float = 1.0,
) -> dict[float, float]:
    base = curve_price(bond, settlement_date, curve, spread_bps)
    if base == 0:
        return {float(k): 0.0 for k in key_tenors}
    out: dict[float, float] = {}
    delta_y = bump_bps / 10000.0
    for key in key_tenors:
        up = triangular_key_shocks(key_tenors, key, bump_bps)
        down = triangular_key_shocks(key_tenors, key, -bump_bps)
        p_up = curve_price(bond, settlement_date, curve, spread_bps, up)
        p_down = curve_price(bond, settlement_date, curve, spread_bps, down)
        out[float(key)] = float((p_down - p_up) / (2.0 * base * delta_y))
    return out


def triangular_key_shocks(
    key_tenors: list[float], target_key: float, bump_bps: float
) -> dict[float, float]:
    # Key-rate bump is localized at the selected node; linear interpolation between
    # nodes creates the standard triangular sensitivity profile.
    return {
        float(k): (float(bump_bps) if float(k) == float(target_key) else 0.0)
        for k in key_tenors
    }
