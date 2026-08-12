# Validation

Validated locally on the generated repository:

```text
.......                                                                  [100%]
7 passed
project validation passed
```

A deterministic smoke test using the included Treasury curve cache and the 2026-08-10 rating OAS levels produced:

- hypothetical market value: approximately $7.11 million
- model portfolio yield: approximately 4.85%
- effective duration: approximately 4.93 years
- DV01: approximately $3,502
- DTS: approximately 220.7 bp-years
- parallel +50 bp KRD scenario: approximately -$175k (-2.46%)

These values are validation outputs for the hypothetical portfolio, not performance claims and not actual portfolio risk numbers.

The live FRED path is intentionally not exercised in this packaged environment because no user API key is embedded. Add `FRED_API_KEY` locally and run `fixed-income-risk refresh` or `fixed-income-risk demo` to test live credit ingestion.
