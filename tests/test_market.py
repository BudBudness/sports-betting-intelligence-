import pytest
from sports_intelligence.market import edge, expected_value, fair_decimal_odds, implied_probability, overround

def test_implied_probability():
    assert implied_probability(2.0) == pytest.approx(0.5)

def test_fair_price():
    assert fair_decimal_odds(0.5) == pytest.approx(2.0)

def test_ev():
    assert expected_value(0.5, 2.2) == pytest.approx(0.1)

def test_edge():
    assert edge(0.60, 0.50) == pytest.approx(0.10)

def test_overround():
    assert overround([2.0, 2.0]) == pytest.approx(0.0)

def test_invalid_odds():
    with pytest.raises(ValueError):
        implied_probability(1.0)
