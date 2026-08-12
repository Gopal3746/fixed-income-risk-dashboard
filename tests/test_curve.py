from datetime import date

import pandas as pd

from fixed_income_risk.math.bonds import Bond
from fixed_income_risk.math.curve import curve_price, key_rate_durations


def curve():
    return pd.DataFrame(
        {
            "tenor_years": [0.5, 1, 2, 5, 10, 30],
            "yield_pct": [4.0, 4.1, 4.2, 4.3, 4.5, 4.8],
        }
    )


def test_curve_price_falls_when_spread_widens():
    bond = Bond(4.5, date(2031, 1, 1), 100, 2)
    p1 = curve_price(bond, date(2026, 1, 1), curve(), spread_bps=50)
    p2 = curve_price(bond, date(2026, 1, 1), curve(), spread_bps=100)
    assert p2 < p1


def test_key_rate_durations_are_non_negative():
    bond = Bond(4.5, date(2034, 1, 1), 100, 2)
    krd = key_rate_durations(bond, date(2026, 1, 1), curve(), 75, [2, 5, 10, 30])
    assert set(krd) == {2.0, 5.0, 10.0, 30.0}
    assert all(v >= 0 for v in krd.values())
    assert sum(krd.values()) > 0
