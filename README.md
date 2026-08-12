# Fixed Income Risk Dashboard

A small fixed-income portfolio risk system built around **real public market inputs** and a **clearly labeled hypothetical bond portfolio**. It pulls the U.S. Treasury daily par yield curve and ICE BofA corporate OAS series from FRED, then computes bond math, portfolio positioning, DTS, a transparent sector-beta proxy, key-rate duration, and curve-shock P&L.

> **Scope boundary:** the positions and notionals in `data/sample_portfolio.csv` are hypothetical. Treasury and FRED inputs are real market data. Bond-level yields and prices are model-implied from those inputs, not vendor marks or actual trade quotes.

## What this demonstrates

- Fixed-income cash-flow modeling: price/yield conversion, Macaulay duration, modified duration, effective duration, convexity and DV01.
- Portfolio positioning: market-value weights, duration, quality mix, sector weights, and active weights versus a public U.S. Aggregate proxy.
- Credit risk budgeting: spread duration, DTS and a sector spread-beta proxy built from rating-level OAS history.
- Curve risk: 2Y/5Y/10Y/30Y key-rate durations and scenario P&L for parallel, steepening and flattening shocks.
- Data engineering: thin API clients, normalization, a repeatable analytics pipeline, tests and a Streamlit dashboard.

## Data sources

### U.S. Treasury daily par yield curve

Source: U.S. Department of the Treasury, Daily Treasury Par Yield Curve Rates.

The pipeline requests the official Treasury CSV endpoint for the current year and normalizes the latest available observation. A Treasury-only cache is included so the curve portion remains inspectable if Treasury is temporarily unavailable.

### Corporate OAS from FRED

The credit module uses these ICE BofA daily OAS series from FRED:

| Rating / universe | FRED series |
|---|---|
| AAA | `BAMLC0A1CAAA` |
| AA | `BAMLC0A2CAA` |
| A | `BAMLC0A3CA` |
| BBB | `BAMLC0A4CBBB` |
| Broad investment grade | `BAMLC0A0CM` |

FRED requires a free API key. ICE index data carries licensing restrictions, so this repository **does not redistribute raw FRED/ICE history**. The app fetches the series at runtime using your own key.

### Benchmark proxy

`data/benchmark_proxy.csv` uses the iShares Core U.S. Aggregate Bond ETF (`AGG`) sector exposure as of **2026-08-10**. AGG's stated benchmark is the Bloomberg U.S. Aggregate Bond Index, making the fund exposure a practical public proxy for sector positioning. The file is a small hand-entered benchmark configuration, not a vendor index data feed.

## Methodology

### 1. Bond math engine

Each position is treated as a fixed-rate, non-callable bullet bond. The engine builds a coupon/principal cash-flow schedule and supports:

- price from yield
- yield from price via bisection
- Macaulay duration
- modified duration
- effective duration from bumped yields
- convexity from symmetric yield shocks
- DV01

The schedule uses a simplified ACT/365.25 year fraction and assumes the configured coupon frequency.

### 2. Model pricing from live market inputs

For the hypothetical portfolio:

1. Interpolate the Treasury par yield at the bond's remaining maturity.
2. For corporates, add the latest rating-level OAS from FRED.
3. Use that model yield for traditional duration metrics.
4. Use curve-by-cash-flow discounting for key-rate sensitivity.

This produces a transparent analytical mark. It is **not** intended to reproduce Bloomberg, ICE, TRACE, or dealer pricing.

### 3. DTS

For corporate positions:

`DTS = spread duration × OAS (bps)`

Portfolio and sector DTS contributions are market-value weighted. Treasuries have zero credit spread and zero DTS.

### 4. Sector beta proxy

The project does not claim access to proprietary bond-level sector spread histories. Instead, it estimates a **rating-mix sector spread beta**:

1. Compute each hypothetical sector's market-value mix across AAA/AA/A/BBB positions.
2. Blend the corresponding FRED rating OAS histories using those weights.
3. Take daily changes in the resulting sector spread proxy.
4. Regress those changes on daily changes in the broad investment-grade OAS series.
5. The OLS slope is shown as `sector_beta`.

This metric is useful for a portfolio-risk demo because the methodology is fully inspectable, but it should not be described as an official vendor sector beta.

### 5. Key-rate duration and curve shocks

The engine calculates 2Y, 5Y, 10Y and 30Y key-rate durations by bumping one curve node at a time and linearly interpolating the bump between nodes. Scenario P&L uses first-order KRD attribution:

`estimated P&L ≈ - market value × Σ(KRD_k × shock_k)`

Included scenarios:

- Parallel +50 bp
- Bear steepener
- Bear flattener
- Bull steepener

## Project structure

```text
fixed-income-risk-dashboard/
├── dashboard/app.py
├── data/
│   ├── benchmark_proxy.csv
│   ├── sample_portfolio.csv
│   └── cached/treasury_curve_2026-08-11.csv
├── scripts/verify_project.py
├── src/fixed_income_risk/
│   ├── analytics/
│   │   ├── dts.py
│   │   ├── portfolio.py
│   │   └── scenarios.py
│   ├── data/
│   │   ├── fred.py
│   │   ├── market.py
│   │   └── treasury.py
│   ├── math/
│   │   ├── bonds.py
│   │   └── curve.py
│   ├── cli.py
│   ├── config.py
│   └── pipeline.py
└── tests/
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

Add your FRED key to `.env`:

```text
FRED_API_KEY=your_key_here
```

Run the tests:

```bash
python -m pytest -q
```

Run a terminal demo:

```bash
PYTHONPATH=src python -m fixed_income_risk.cli demo
```

Launch Streamlit:

```bash
streamlit run dashboard/app.py
```

## Dashboard pages

- **Positioning** — sector and quality mix plus active weights versus the AGG proxy.
- **DTS & Beta** — sector DTS contribution and rating-mix spread beta.
- **Curve Risk** — key-rate duration contribution and scenario P&L.
- **Bond-Level Analytics** — price, yield, duration, spread duration, DTS, DV01 and KRD by position.
- **Data & Assumptions** — Treasury curve plus the project's modeling boundary.

## Validation notes

The included tests check:

- a par bond prices close to 100 when coupon equals yield
- price/yield round-trip accuracy
- price falls when spread widens
- key-rate durations are positive
- a rate-rise scenario generates negative P&L
- the sector-beta proxy recovers a known synthetic regression slope

## Known limitations

- No actual client positions or security identifiers are used.
- No security-level corporate bond quote/OAS feed is used.
- Treasury CMT rates are par yields, not a fully bootstrapped Treasury spot curve.
- The cash-flow schedule uses simplified timing rather than full street day-count/business-day conventions.
- Callable, putable, floating-rate, MBS and amortizing securities are outside scope.
- Scenario P&L is duration-based rather than a full nonlinear revaluation.

Those limits are intentional: the project is small enough to explain end-to-end while still demonstrating the core risk concepts in the role description.

## Potential stretch goals

- bootstrap a zero curve from Treasury par yields
- add historical VaR / expected shortfall
- support callable bonds with option-adjusted effective duration
- add a Power BI export layer for the aggregated tables
- store daily snapshots in DuckDB and build a risk-history page

## Source links

- U.S. Treasury daily rates: `https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve`
- Treasury CSV pattern: `https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{YEAR}/all?type=daily_treasury_yield_curve&field_tdr_date_value={YEAR}&_format=csv`
- FRED API documentation: `https://fred.stlouisfed.org/docs/api/fred/series_observations.html`
- iShares AGG: `https://www.ishares.com/us/products/239458/ishares-core-total-us-bond-market-etf`
