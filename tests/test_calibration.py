from pytest import approx

from sports_intelligence.models.calibration import brier_score, log_loss
from sports_intelligence.reporting.assessment import assess_value


def test_calibration_metrics():
    p = [0.9, 0.1]
    y = [1, 0]
    assert brier_score(p, y) == approx(0.01)
    assert log_loss(p, y) > 0


def test_value_gate():
    assert assess_value(0.60, 2.0) == "VALUE IDENTIFIED"
    assert assess_value(0.50, 2.0) == "FAIRLY PRICED"
