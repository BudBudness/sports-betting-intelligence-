from datetime import datetime
from .contracts import MarketObservation


def canonical_event_key(obs: MarketObservation) -> tuple[str, str, str]:
    return obs.event_id, obs.market_id, obs.selection_id


def deduplicate(observations: list[MarketObservation]) -> list[MarketObservation]:
    latest: dict[tuple[str, str, str, str, datetime], MarketObservation] = {}
    for obs in observations:
        key = (*canonical_event_key(obs), obs.provider, obs.source_timestamp)
        latest[key] = obs
    return list(latest.values())
