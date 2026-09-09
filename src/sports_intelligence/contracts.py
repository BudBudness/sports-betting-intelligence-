from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from pydantic import BaseModel, Field

class Assessment(StrEnum):
    VALUE_IDENTIFIED = "VALUE IDENTIFIED"
    MARGINAL_VALUE = "MARGINAL VALUE"
    FAIRLY_PRICED = "FAIRLY PRICED"
    NO_CLEAR_VALUE = "NO CLEAR VALUE"
    INSUFFICIENT_DATA = "INSUFFICIENT DATA"
    MODEL_REVIEW_REQUIRED = "MODEL REVIEW REQUIRED"

class DataQualityStatus(StrEnum):
    VALID = "VALID"
    VALID_WITH_WARNINGS = "VALID WITH WARNINGS"
    DEGRADED = "DEGRADED"
    INVALID = "INVALID"

class MarketObservation(BaseModel):
    event_id: str
    market_id: str
    selection_id: str
    provider: str
    source_timestamp: datetime
    ingestion_timestamp: datetime
    decimal_odds: Decimal = Field(gt=1)
    line: Decimal | None = None
    status: str = "open"

class Prediction(BaseModel):
    event_id: str
    prediction_timestamp: datetime
    model_name: str
    model_version: str
    feature_version: str
    data_version: str
    calibration_version: str
    probability: float = Field(ge=0, le=1)

class MarketValue(BaseModel):
    model_probability: float = Field(ge=0, le=1)
    market_implied_probability: float = Field(ge=0, le=1)
    fair_decimal_odds: float = Field(gt=0)
    observed_decimal_odds: float = Field(gt=1)
    edge: float
    ev: float

class AnalysisResult(BaseModel):
    event_id: str
    data_quality: DataQualityStatus
    assessment: Assessment
    value: MarketValue | None = None
    confidence: int | None = Field(default=None, ge=0, le=100)
    risks: list[str] = []
    assumptions: list[str] = []
    facts_to_verify: list[str] = []
