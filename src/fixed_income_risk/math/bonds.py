from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

import numpy as np


@dataclass(frozen=True)
class Bond:
    coupon_rate: float  # percent per year
    maturity_date: date
    face_value: float = 100.0
    frequency: int = 2


def _to_date(value: date | datetime | str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(value).date()


def year_fraction(start: date | str, end: date | str) -> float:
    s = _to_date(start)
    e = _to_date(end)
    return max((e - s).days / 365.25, 0.0)


def cashflow_schedule(
    bond: Bond, settlement_date: date | str
) -> tuple[np.ndarray, np.ndarray]:
    settlement = _to_date(settlement_date)
    years = year_fraction(settlement, bond.maturity_date)
    if years <= 0:
        return np.array([], dtype=float), np.array([], dtype=float)

    periods = max(int(np.ceil(years * bond.frequency)), 1)
    times = np.arange(1, periods + 1, dtype=float) / bond.frequency
    times[-1] = years
    coupon = bond.face_value * (bond.coupon_rate / 100.0) / bond.frequency
    cashflows = np.full(periods, coupon, dtype=float)
    cashflows[-1] += bond.face_value
    return times, cashflows


def price_from_ytm(
    bond: Bond, ytm_pct: float, settlement_date: date | str
) -> float:
    times, cashflows = cashflow_schedule(bond, settlement_date)
    if len(times) == 0:
        return 0.0
    m = bond.frequency
    y = ytm_pct / 100.0
    periods = times * m
    discounts = (1.0 + y / m) ** periods
    return float(np.sum(cashflows / discounts))


def yield_from_price(
    bond: Bond,
    target_price: float,
    settlement_date: date | str,
    low_pct: float = -0.95,
    high_pct: float = 30.0,
    tol: float = 1e-10,
    max_iter: int = 200,
) -> float:
    low, high = low_pct, high_pct
    f_low = price_from_ytm(bond, low, settlement_date) - target_price
    f_high = price_from_ytm(bond, high, settlement_date) - target_price
    if f_low * f_high > 0:
        raise ValueError("Price is outside the supported yield search range")
    for _ in range(max_iter):
        mid = (low + high) / 2.0
        f_mid = price_from_ytm(bond, mid, settlement_date) - target_price
        if abs(f_mid) < tol:
            return mid
        if f_low * f_mid <= 0:
            high, f_high = mid, f_mid
        else:
            low, f_low = mid, f_mid
    return (low + high) / 2.0


def macaulay_duration(
    bond: Bond, ytm_pct: float, settlement_date: date | str
) -> float:
    times, cashflows = cashflow_schedule(bond, settlement_date)
    if len(times) == 0:
        return 0.0
    m = bond.frequency
    y = ytm_pct / 100.0
    pv = cashflows / ((1 + y / m) ** (times * m))
    price = pv.sum()
    return float(np.sum(times * pv) / price)


def modified_duration(
    bond: Bond, ytm_pct: float, settlement_date: date | str
) -> float:
    mac = macaulay_duration(bond, ytm_pct, settlement_date)
    return float(mac / (1.0 + (ytm_pct / 100.0) / bond.frequency))


def effective_duration(
    bond: Bond,
    ytm_pct: float,
    settlement_date: date | str,
    bump_bps: float = 1.0,
) -> float:
    base = price_from_ytm(bond, ytm_pct, settlement_date)
    bump_pct = bump_bps / 100.0
    p_down = price_from_ytm(bond, ytm_pct - bump_pct, settlement_date)
    p_up = price_from_ytm(bond, ytm_pct + bump_pct, settlement_date)
    delta_y = bump_bps / 10000.0
    return float((p_down - p_up) / (2.0 * base * delta_y))


def convexity(
    bond: Bond,
    ytm_pct: float,
    settlement_date: date | str,
    bump_bps: float = 10.0,
) -> float:
    base = price_from_ytm(bond, ytm_pct, settlement_date)
    bump_pct = bump_bps / 100.0
    p_down = price_from_ytm(bond, ytm_pct - bump_pct, settlement_date)
    p_up = price_from_ytm(bond, ytm_pct + bump_pct, settlement_date)
    delta_y = bump_bps / 10000.0
    return float((p_down + p_up - 2.0 * base) / (base * delta_y**2))


def dv01_per_100(
    bond: Bond, ytm_pct: float, settlement_date: date | str
) -> float:
    duration = effective_duration(bond, ytm_pct, settlement_date, bump_bps=1.0)
    price = price_from_ytm(bond, ytm_pct, settlement_date)
    return float(duration * price * 1e-4)
