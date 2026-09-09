from dataclasses import dataclass

@dataclass(frozen=True)
class Confidence:
    score: int
    level: str
    rationale: tuple[str, ...]


def score_confidence(*, data_quality: str, model_agreement: float | None, sample_size: int, edge: float | None) -> Confidence:
    if data_quality == "INVALID" or sample_size <= 0:
        return Confidence(0, "INSUFFICIENT", ("insufficient or invalid evidence",))
    score = 35
    rationale = []
    if data_quality == "VALID":
        score += 20
        rationale.append("data quality is valid")
    elif data_quality == "VALID WITH WARNINGS":
        score += 10
        rationale.append("data quality has warnings")
    if model_agreement is not None:
        score += round(max(0.0, min(1.0, model_agreement)) * 20)
        rationale.append("model agreement contributes to confidence")
    if sample_size >= 100:
        score += 15
    elif sample_size >= 30:
        score += 8
    if edge is not None and edge > 0:
        score += min(10, round(edge * 100))
    score = min(100, score)
    level = "HIGH" if score >= 75 else "MEDIUM" if score >= 50 else "LOW"
    return Confidence(score, level, tuple(rationale))
