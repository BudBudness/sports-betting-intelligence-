from .market import edge, expected_value


def assess_value(model_probability: float, decimal_odds: float, *, min_edge: float = 0.02, min_ev: float = 0.03) -> str:
    e = edge(model_probability, 1 / decimal_odds)
    ev = expected_value(model_probability, decimal_odds)
    if e >= min_edge and ev >= min_ev:
        return "VALUE IDENTIFIED"
    if e > 0 or ev > 0:
        return "MARGINAL VALUE"
    if e == 0 and ev == 0:
        return "FAIRLY PRICED"
    return "NO CLEAR VALUE"
