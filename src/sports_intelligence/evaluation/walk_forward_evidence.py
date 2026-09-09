from __future__ import annotations

from dataclasses import dataclass
from math import log

from sports_intelligence.data.football_data import MatchRow
from sports_intelligence.models.elo import EloState, outcome_probabilities


@dataclass(frozen=True)
class EvidenceSummary:
    sample_size: int
    model_brier: float
    market_brier: float
    model_log_loss: float
    market_log_loss: float
    model_accuracy: float
    market_accuracy: float
    positive_ev_observations: int
    positive_ev_hit_rate: float | None
    closing_line_observations: int
    mean_closing_odds_delta: float | None


def _metrics(rows: list[tuple[tuple[float, float, float], str]]) -> tuple[float, float, float]:
    index = {"H": 0, "D": 1, "A": 2}
    brier = 0.0
    logloss = 0.0
    accuracy = 0
    for probs, result in rows:
        i = index[result]
        brier += sum((p - (1.0 if j == i else 0.0)) ** 2 for j, p in enumerate(probs))
        logloss -= log(max(1e-15, probs[i]))
        accuracy += int(max(range(3), key=lambda j: probs[j]) == i)
    n = len(rows)
    return brier / n, logloss / n, accuracy / n


def run_walk_forward(rows: list[MatchRow]) -> EvidenceSummary:
    state = EloState(ratings={})
    model_rows: list[tuple[tuple[float, float, float], str]] = []
    market_rows: list[tuple[tuple[float, float, float], str]] = []
    positive_ev = positive_ev_hits = 0
    closing_deltas: list[float] = []

    for row in sorted(rows, key=lambda r: (r.date, r.home, r.away)):
        if row.avg_home_odds and row.avg_draw_odds and row.avg_away_odds:
            model = outcome_probabilities(state, row.home, row.away)
            raw = tuple(1.0 / x for x in (row.avg_home_odds, row.avg_draw_odds, row.avg_away_odds))
            total = sum(raw)
            market = tuple(x / total for x in raw)
            model_rows.append((model, row.result))
            market_rows.append((market, row.result))
            candidates = ((model[0], row.avg_home_odds, row.result == "H"), (model[1], row.avg_draw_odds, row.result == "D"), (model[2], row.avg_away_odds, row.result == "A"))
            best = max(candidates, key=lambda x: x[0] * x[1] - 1.0)
            if best[0] * best[1] - 1.0 > 0:
                positive_ev += 1
                positive_ev_hits += int(best[2])
            opening = (row.avg_home_odds, row.avg_draw_odds, row.avg_away_odds)
            closing = (row.closing_home_odds, row.closing_draw_odds, row.closing_away_odds)
            if all(x is not None for x in closing):
                closing_deltas.append(sum(c - o for o, c in zip(opening, closing) if o and c) / 3)
        state.update(row.home, row.away, row.result == "H", row.result == "D")

    if not model_rows:
        raise ValueError("No complete market observations available")
    mb, ml, ma = _metrics(model_rows)
    kb, kl, ka = _metrics(market_rows)
    return EvidenceSummary(len(model_rows), mb, kb, ml, kl, ma, ka, positive_ev, positive_ev_hits / positive_ev if positive_ev else None, len(closing_deltas), sum(closing_deltas) / len(closing_deltas) if closing_deltas else None)
