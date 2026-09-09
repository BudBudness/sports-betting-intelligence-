from dataclasses import dataclass
from datetime import datetime
from .contracts import MarketObservation

@dataclass(frozen=True)
class Movement:
    opening_odds: float
    latest_odds: float
    change: float
    velocity_per_hour: float | None
    acceleration_per_hour2: float | None


def movement(observations: list[MarketObservation]) -> Movement:
    if not observations:
        raise ValueError("at least one observation is required")
    rows = sorted(observations, key=lambda x: x.source_timestamp)
    opening = float(rows[0].decimal_odds)
    latest = float(rows[-1].decimal_odds)
    velocity = None
    acceleration = None
    if len(rows) >= 2:
        hours = (rows[-1].source_timestamp - rows[0].source_timestamp).total_seconds() / 3600
        if hours > 0:
            velocity = (latest - opening) / hours
    if len(rows) >= 3:
        t1 = (rows[-2].source_timestamp - rows[-3].source_timestamp).total_seconds() / 3600
        t2 = (rows[-1].source_timestamp - rows[-2].source_timestamp).total_seconds() / 3600
        if t1 > 0 and t2 > 0:
            v1 = (float(rows[-2].decimal_odds) - float(rows[-3].decimal_odds)) / t1
            v2 = (latest - float(rows[-2].decimal_odds)) / t2
            acceleration = (v2 - v1) / ((t1 + t2) / 2)
    return Movement(opening, latest, latest - opening, velocity, acceleration)


def provider_dispersion(observations: list[MarketObservation]) -> float | None:
    if not observations:
        return None
    odds = [float(o.decimal_odds) for o in observations]
    return max(odds) - min(odds)
