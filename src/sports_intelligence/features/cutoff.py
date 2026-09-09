from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class CutoffGuard:
    cutoff: datetime

    def check(self, information_time: datetime) -> None:
        if information_time > self.cutoff:
            raise ValueError("future information detected: information_time exceeds cutoff")

    def filter(self, timestamps: list[datetime]) -> list[datetime]:
        return [ts for ts in timestamps if ts <= self.cutoff]
