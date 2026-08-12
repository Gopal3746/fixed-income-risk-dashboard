from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
required = [
    "README.md",
    "dashboard/app.py",
    "data/sample_portfolio.csv",
    "data/benchmark_proxy.csv",
    "src/fixed_income_risk/math/bonds.py",
    "src/fixed_income_risk/analytics/dts.py",
    "src/fixed_income_risk/analytics/scenarios.py",
]
missing = [path for path in required if not (ROOT / path).exists()]
if missing:
    print("missing required files:", ", ".join(missing))
    sys.exit(1)
print("project validation passed")
