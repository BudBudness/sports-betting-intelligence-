from datetime import datetime
from .contracts import MarketObservation


def snapshot_id(observations: list[MarketObservation]) -> str:
    import hashlib
    canonical = "|".join(
        f"{o.event_id}:{o.market_id}:{o.selection_id}:{o.provider}:{o.source_timestamp.isoformat()}:{o.decimal_odds}"
        for o in sorted(observations, key=lambda x: (x.event_id, x.market_id, x.selection_id, x.provider, x.source_timestamp.isoformat()))
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def as_of(observations: list[MarketObservation], cutoff: datetime) -> list[MarketObservation]:
    return [o for o in observations if o.source_timestamp <= cutoff]
