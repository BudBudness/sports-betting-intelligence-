from dataclasses import dataclass
from typing import Protocol

class ProbabilityModel(Protocol):
    name: str
    version: str
    def predict_probability(self, features: dict[str, float]) -> float: ...

@dataclass(frozen=True)
class ModelSpec:
    name: str
    version: str
    market: str
    sport: str

class ModelRegistry:
    def __init__(self) -> None:
        self._models: dict[tuple[str, str], ProbabilityModel] = {}

    def register(self, model: ProbabilityModel) -> None:
        key = (model.name, model.version)
        if key in self._models:
            raise ValueError(f"model already registered: {model.name}@{model.version}")
        self._models[key] = model

    def get(self, name: str, version: str) -> ProbabilityModel:
        try:
            return self._models[(name, version)]
        except KeyError as exc:
            raise KeyError(f"model not registered: {name}@{version}") from exc

    def list(self) -> list[ModelSpec]:
        return [ModelSpec(name=m.name, version=m.version, market="unknown", sport="unknown") for m in self._models.values()]
