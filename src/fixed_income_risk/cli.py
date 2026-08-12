from __future__ import annotations

import argparse
from datetime import date

from dotenv import load_dotenv

from fixed_income_risk.data.fred import fetch_oas_history, latest_oas
from fixed_income_risk.data.treasury import fetch_treasury_curve
from fixed_income_risk.pipeline import run_analytics


def _refresh() -> None:
    curve = fetch_treasury_curve()
    print("Treasury curve:")
    print(curve.to_string(index=False))
    history = fetch_oas_history()
    print("\nLatest OAS (bps):", latest_oas(history))


def _demo() -> None:
    bundle = run_analytics(settlement_date=date.today().isoformat())
    s = bundle.portfolio_summary
    print("Hypothetical Fixed Income Portfolio")
    print(f"Market value: ${s['market_value']:,.0f}")
    print(f"Model yield: {s['yield_pct']:.2f}%")
    print(f"Effective duration: {s['duration']:.2f} years")
    print(f"DV01: ${s['dv01']:,.0f}")
    print(f"DTS: {s['dts']:.1f} bp-years")
    print("\nScenario summary")
    print(bundle.scenario_summary.to_string(index=False))


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Fixed income risk dashboard utilities")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("refresh", help="Fetch current Treasury curve and FRED OAS data")
    sub.add_parser("demo", help="Run the sample portfolio analytics")
    args = parser.parse_args()
    if args.command == "refresh":
        _refresh()
    elif args.command == "demo":
        _demo()


if __name__ == "__main__":
    main()
