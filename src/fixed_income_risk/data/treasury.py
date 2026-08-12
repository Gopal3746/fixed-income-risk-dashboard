from __future__ import annotations

from datetime import date
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

from fixed_income_risk.config import CACHED_DIR, TREASURY_TENORS

TREASURY_CSV_URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
    "daily-treasury-rates.csv/{year}/all"
)


def fetch_treasury_curve(year: int | None = None, timeout: int = 20) -> pd.DataFrame:
    """Fetch the latest official U.S. Treasury daily par yield curve observation."""
    year = year or date.today().year
    params = {
        "type": "daily_treasury_yield_curve",
        "field_tdr_date_value": str(year),
        "page": "",
        "_format": "csv",
    }
    response = requests.get(
        TREASURY_CSV_URL.format(year=year), params=params, timeout=timeout
    )
    response.raise_for_status()
    raw = pd.read_csv(StringIO(response.text))
    return normalize_treasury_curve(raw)


def normalize_treasury_curve(raw: pd.DataFrame) -> pd.DataFrame:
    if "Date" not in raw.columns:
        raise ValueError("Treasury response did not include a Date column")
    raw = raw.copy()
    raw["Date"] = pd.to_datetime(raw["Date"], errors="coerce")
    raw = raw.dropna(subset=["Date"]).sort_values("Date")
    if raw.empty:
        raise ValueError("Treasury response contained no valid observations")
    latest = raw.iloc[-1]
    rows = []
    for source_col, (years, label) in TREASURY_TENORS.items():
        if source_col not in raw.columns:
            continue
        value = pd.to_numeric(pd.Series([latest[source_col]]), errors="coerce").iloc[0]
        if pd.isna(value):
            continue
        rows.append(
            {
                "as_of": latest["Date"].date().isoformat(),
                "tenor_years": float(years),
                "tenor_label": label,
                "yield_pct": float(value),
            }
        )
    curve = pd.DataFrame(rows).sort_values("tenor_years").reset_index(drop=True)
    if curve.empty:
        raise ValueError("Treasury response did not contain recognized curve tenors")
    return curve


def load_cached_treasury_curve() -> pd.DataFrame:
    candidates = sorted(Path(CACHED_DIR).glob("treasury_curve_*.csv"))
    if not candidates:
        raise FileNotFoundError("No cached Treasury curve is available")
    return pd.read_csv(candidates[-1])


def get_treasury_curve(prefer_live: bool = True) -> tuple[pd.DataFrame, str]:
    if prefer_live:
        try:
            return fetch_treasury_curve(), "live"
        except Exception:
            pass
    return load_cached_treasury_curve(), "cached"
