from dataclasses import dataclass

from .metrics import METRICS

COMPARATORS = ("<=", ">=")


@dataclass(frozen=True)
class Requirement:
    id: str
    title: str
    metric: str
    comparator: str
    threshold: float
    unit: str = ""
    method: str = "Analysis"
    rationale: str = ""

    @property
    def scope_kind(self) -> str:
        return METRICS[self.metric].scope

    @property
    def statement(self) -> str:
        return f"{METRICS[self.metric].label} {self.comparator} {self.threshold:g} {self.unit}".strip()


def parse_requirement(raw: dict) -> Requirement:
    missing = [k for k in ("id", "title", "metric", "comparator", "threshold") if k not in raw]
    if missing:
        raise ValueError(f"Requirement {raw.get('id', '?')} is missing fields: {', '.join(missing)}")
    if raw["metric"] not in METRICS:
        known = ", ".join(sorted(METRICS))
        raise ValueError(f"Requirement {raw['id']}: unknown metric '{raw['metric']}' (known: {known})")
    if raw["comparator"] not in COMPARATORS:
        raise ValueError(f"Requirement {raw['id']}: comparator must be one of {COMPARATORS}")
    return Requirement(
        id=str(raw["id"]),
        title=str(raw["title"]),
        metric=str(raw["metric"]),
        comparator=str(raw["comparator"]),
        threshold=float(raw["threshold"]),
        unit=str(raw.get("unit", METRICS[raw["metric"]].unit)),
        method=str(raw.get("method", "Analysis")),
        rationale=str(raw.get("rationale", "")),
    )
