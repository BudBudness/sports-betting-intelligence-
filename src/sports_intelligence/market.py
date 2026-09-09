from decimal import Decimal

def implied_probability(decimal_odds: float | Decimal) -> float:
    odds = float(decimal_odds)
    if odds <= 1:
        raise ValueError("Decimal odds must be greater than 1")
    return 1.0 / odds

def overround(decimal_odds: list[float | Decimal]) -> float:
    if not decimal_odds:
        raise ValueError("At least one price is required")
    return sum(implied_probability(o) for o in decimal_odds) - 1.0

def fair_decimal_odds(probability: float) -> float:
    if not 0 < probability <= 1:
        raise ValueError("Probability must be in (0, 1]")
    return 1.0 / probability

def expected_value(probability: float, decimal_odds: float) -> float:
    if not 0 <= probability <= 1:
        raise ValueError("Probability must be between 0 and 1")
    if decimal_odds <= 1:
        raise ValueError("Decimal odds must be greater than 1")
    return probability * decimal_odds - 1.0

def edge(model_probability: float, market_probability: float) -> float:
    if not 0 <= model_probability <= 1 or not 0 <= market_probability <= 1:
        raise ValueError("Probabilities must be between 0 and 1")
    return model_probability - market_probability
