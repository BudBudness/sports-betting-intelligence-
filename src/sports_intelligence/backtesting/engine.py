from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

@dataclass(frozen=True)
class HistoricalPrediction:
    prediction_id: str
    event_id: str
    prediction_timestamp: datetime
    probability: float
    market_odds: float | None
    outcome: int | None

@dataclass(frozen=True)
class BacktestSummary:
    sample_size: int
    accuracy: float | None
    brier_score: float | None
    log_loss: float | None
    baseline_brier_score: float | None = None


def evaluate_binary(predictions: Iterable[HistoricalPrediction]) -> BacktestSummary:
    rows = list(predictions)
    observed = [r for r in rows if r.outcome in (0, 1)]
    if not observed:
        return BacktestSummary(0, None, None, None)
    from .calibration import brier_score, log_loss
    probs = [r.probability for r in observed]
    outcomes = [r.outcome for r in observed]
    accuracy = sum((p >= 0.5) == bool(y) for p, y in zip(probs, outcomes)) / len(observed)
    return BacktestSummary(len(observed), accuracy, brier_score(probs, outcomes), log_loss(probs, outcomes))
