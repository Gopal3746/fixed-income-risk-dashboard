from __future__ import annotations

import os
from datetime import date, timedelta

import pandas as pd
import requests

from fixed_income_risk.config import FRED_SERIES

FRED_OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"


class FredKeyMissing(RuntimeError):
    pass


def _api_key(explicit: str | None = None) -> str:
    key = explicit or os.getenv("FRED_API_KEY")
    if not key:
        raise FredKeyMissing(
            "FRED_API_KEY is not set. Copy .env.example to .env and add a free FRED API key."
        )
    return key


def fetch_series(
    series_id: str,
    start: str | None = None,
    api_key: str | None = None,
    timeout: int = 20,
) -> pd.DataFrame:
    params = {
        "series_id": series_id,
        "api_key": _api_key(api_key),
        "file_type": "json",
        "sort_order": "asc",
    }
    if start:
        params["observation_start"] = start
    response = requests.get(FRED_OBSERVATIONS_URL, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    observations = payload.get("observations", [])
    frame = pd.DataFrame(observations)
    if frame.empty:
        raise ValueError(f"FRED returned no observations for {series_id}")
    frame = frame[["date", "value"]].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    return frame.dropna().reset_index(drop=True)


def fetch_oas_history(
    lookback_days: int = 550,
    api_key: str | None = None,
) -> pd.DataFrame:
    start = (date.today() - timedelta(days=lookback_days)).isoformat()
    merged = None
    for label, series_id in FRED_SERIES.items():
        one = fetch_series(series_id, start=start, api_key=api_key).rename(
            columns={"value": label}
        )
        merged = one if merged is None else merged.merge(one, on="date", how="outer")
    assert merged is not None
    return merged.sort_values("date").reset_index(drop=True)


def latest_oas(oas_history: pd.DataFrame) -> dict[str, float]:
    values: dict[str, float] = {}
    for label in FRED_SERIES:
        series = oas_history[label].dropna()
        if series.empty:
            raise ValueError(f"No usable OAS observations for {label}")
        values[label] = float(series.iloc[-1]) * 100.0  # FRED percent -> basis points
    return values
