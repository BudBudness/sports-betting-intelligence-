from datetime import datetime
from pydantic import BaseModel, Field

class Event(BaseModel):
    event_id: str
    sport: str
    competition: str
    home_team: str
    away_team: str
    scheduled_at: datetime

class SourceRef(BaseModel):
    source: str
    source_timestamp: datetime
    ingestion_timestamp: datetime
    data_version: str

class FeatureValue(BaseModel):
    name: str
    value: float | None
    information_cutoff: datetime
    source: str | None = None

class QualityReport(BaseModel):
    status: str
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    checks: dict[str, bool] = Field(default_factory=dict)
