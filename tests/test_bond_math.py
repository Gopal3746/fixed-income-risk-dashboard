from datetime import date

import pytest

from fixed_income_risk.math.bonds import Bond, modified_duration, price_from_ytm, yield_from_price


def test_par_bond_prices_near_100_when_coupon_equals_yield():
    bond = Bond(coupon_rate=5.0, maturity_date=date(2031, 1, 1), face_value=100.0, frequency=2)
    price = price_from_ytm(bond, 5.0, date(2026, 1, 1))
    assert price == pytest.approx(100.0, abs=0.25)


def test_yield_price_round_trip():
    bond = Bond(coupon_rate=4.0, maturity_date=date(2034, 1, 1), face_value=100.0, frequency=2)
    price = price_from_ytm(bond, 5.25, date(2026, 1, 1))
    solved = yield_from_price(bond, price, date(2026, 1, 1))
    assert solved == pytest.approx(5.25, abs=1e-7)


def test_modified_duration_is_positive_and_less_than_macaulay_factor():
    bond = Bond(coupon_rate=4.5, maturity_date=date(2032, 1, 1), face_value=100.0, frequency=2)
    mod = modified_duration(bond, 5.0, date(2026, 1, 1))
    assert 0 < mod < 6.5
