from dataclasses import dataclass

@dataclass(frozen=True)
class CalibrationReport:
    method: str
    brier_score: float | None
    log_loss: float | None
    calibration_error: float | None
    sample_size: int


def brier_score(probabilities: list[float], outcomes: list[int]) -> float:
    if len(probabilities) != len(outcomes) or not probabilities:
        raise ValueError("probabilities and outcomes must be non-empty and equal length")
    return sum((p - y) ** 2 for p, y in zip(probabilities, outcomes)) / len(probabilities)


def log_loss(probabilities: list[float], outcomes: list[int], eps: float = 1e-15) -> float:
    import math
    if len(probabilities) != len(outcomes) or not probabilities:
        raise ValueError("probabilities and outcomes must be non-empty and equal length")
    total = 0.0
    for p, y in zip(probabilities, outcomes):
        p = min(max(p, eps), 1 - eps)
        total -= y * math.log(p) + (1 - y) * math.log(1 - p)
    return total / len(probabilities)
