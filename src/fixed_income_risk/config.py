from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CACHED_DIR = DATA_DIR / "cached"

FRED_SERIES = {
    "AAA": "BAMLC0A1CAAA",
    "AA": "BAMLC0A2CAA",
    "A": "BAMLC0A3CA",
    "BBB": "BAMLC0A4CBBB",
    "IG": "BAMLC0A0CM",
}

TREASURY_TENORS = {
    "1 Mo": (1 / 12, "1M"),
    "1.5 Mo": (1.5 / 12, "1.5M"),
    "2 Mo": (2 / 12, "2M"),
    "3 Mo": (3 / 12, "3M"),
    "4 Mo": (4 / 12, "4M"),
    "6 Mo": (0.5, "6M"),
    "1 Yr": (1.0, "1Y"),
    "2 Yr": (2.0, "2Y"),
    "3 Yr": (3.0, "3Y"),
    "5 Yr": (5.0, "5Y"),
    "7 Yr": (7.0, "7Y"),
    "10 Yr": (10.0, "10Y"),
    "20 Yr": (20.0, "20Y"),
    "30 Yr": (30.0, "30Y"),
}

KEY_RATE_TENORS = [2.0, 5.0, 10.0, 30.0]
