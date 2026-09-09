from datetime import datetime
from .contracts import MarketObservation


def validate_market_observation(obs: MarketObservation, now: datetime | None = None) -> list[str]:
    errors: list[str] = []
    if obs.decimal_odds <= 1:
        errors.append("decimal_odds must be greater than 1")
    if obs.source_timestamp > obs.ingestion_timestamp:
        errors.append("source_timestamp cannot be after ingestion_timestamp")
    if now is not None and obs.source_timestamp > now:
        errors.append("source_timestamp cannot be in the future")
    return errors


def quality_status(errors: list[str], warnings: list[str] | None = None) -> str:
    if errors:
        return "INVALID"
    if warnings:
        return "VALID WITH WARNINGS"
    return "VALID"
