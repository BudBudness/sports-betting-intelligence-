from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class AppendOnlyEvidenceLedger:
    """Append-only JSONL ledger with a tamper-evident hash chain."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.previous_hash = self._last_hash()

    def _last_hash(self) -> str:
        if not self.path.exists():
            return "GENESIS"
        last = "GENESIS"
        with self.path.open("rb") as handle:
            for line in handle:
                if line.strip():
                    try:
                        last = json.loads(line)["record_hash"]
                    except (KeyError, json.JSONDecodeError):
                        raise ValueError("Evidence ledger contains an invalid record")
        return last

    def append(self, record: dict[str, Any]) -> str:
        if "prediction_id" not in record:
            raise ValueError("prediction_id is required")
        envelope = {"previous_hash": self.previous_hash, **record}
        canonical = json.dumps(envelope, sort_keys=True, separators=(",", ":"), default=str)
        record_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        envelope["record_hash"] = record_hash
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(envelope, sort_keys=True, default=str) + "\n")
        self.previous_hash = record_hash
        return record_hash

    def verify(self) -> bool:
        if not self.path.exists():
            return True
        previous = "GENESIS"
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                envelope = json.loads(line)
                actual = envelope.pop("record_hash", None)
                if envelope.get("previous_hash") != previous:
                    return False
                canonical = json.dumps(envelope, sort_keys=True, separators=(",", ":"), default=str)
                expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
                if actual != expected:
                    return False
                previous = actual
        return True
