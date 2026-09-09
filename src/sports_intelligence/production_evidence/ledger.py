from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class LedgerRecord:
    prediction_id: str
    event_id: str
    prediction_timestamp: datetime
    data_version: str
    feature_version: str
    model_version: str
    calibration_version: str
    probability: float
    fair_price: float | None
    market_price: float | None
    edge: float | None
    ev: float | None
    confidence: int | None
    assessment: str

class PredictionLedger:
    def __init__(self) -> None:
        self._records: dict[str, LedgerRecord] = {}

    def append(self, record: LedgerRecord) -> None:
        if record.prediction_id in self._records:
            raise ValueError(f"prediction_id already exists: {record.prediction_id}")
        self._records[record.prediction_id] = record

    def get(self, prediction_id: str) -> LedgerRecord:
        return self._records[prediction_id]

    def all(self) -> tuple[LedgerRecord, ...]:
        return tuple(self._records.values())
