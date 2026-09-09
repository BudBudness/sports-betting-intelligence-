from datetime import datetime, timezone
from decimal import Decimal
import pytest
from sports_intelligence.contracts import MarketObservation
from sports_intelligence.data.validation import validate_market_observation
from sports_intelligence.features.cutoff import CutoffGuard


def obs(ts: datetime) -> MarketObservation:
    return MarketObservation(event_id="e1", market_id="m1", selection_id="s1", provider="p1", source_timestamp=ts, ingestion_timestamp=ts, decimal_odds=Decimal("2.0"))


def test_future_information_is_rejected():
    cutoff = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValueError):
        CutoffGuard(cutoff).check(datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc))


def test_market_timestamp_order_is_validated():
    source = datetime(2026, 1, 1, tzinfo=timezone.utc)
    ingestion = datetime(2025, 12, 31, tzinfo=timezone.utc)
    errors = validate_market_observation(obs(source).model_copy(update={"ingestion_timestamp": ingestion}))
    assert "source_timestamp cannot be after ingestion_timestamp" in errors
