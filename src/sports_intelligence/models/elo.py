from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EloState:
    ratings: dict[str, float]
    home_advantage: float = 60.0
    k_factor: float = 20.0
    initial_rating: float = 1500.0

    def rating(self, team: str) -> float:
        return self.ratings.get(team, self.initial_rating)

    def probabilities(self, home: str, away: str) -> tuple[float, float]:
        diff = self.rating(home) + self.home_advantage - self.rating(away)
        home_win = 1.0 / (1.0 + 10.0 ** (-diff / 400.0))
        return home_win, 1.0 - home_win

    def update(self, home: str, away: str, home_win: bool, draw: bool) -> None:
        rh = self.rating(home)
        ra = self.rating(away)
        expected_home = 1.0 / (1.0 + 10.0 ** (-(rh + self.home_advantage - ra) / 400.0))
        actual_home = 0.5 if draw else (1.0 if home_win else 0.0)
        delta = self.k_factor * (actual_home - expected_home)
        self.ratings[home] = rh + delta
        self.ratings[away] = ra - delta


def outcome_probabilities(state: EloState, home: str, away: str) -> tuple[float, float, float]:
    """Return H/D/A probabilities from the pre-match Elo state."""
    home_win, away_win = state.probabilities(home, away)
    draw = min(0.30, max(0.12, 0.26 - 0.10 * abs(home_win - away_win)))
    scale = 1.0 - draw
    return home_win * scale, draw, away_win * scale
