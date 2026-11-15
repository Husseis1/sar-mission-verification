import math
from dataclasses import dataclass
from enum import Enum

from .metrics import evaluate_metric
from .requirements import Requirement


class Status(str, Enum):
    PASS = "PASS"
    MARGINAL = "MARGINAL"
    FAIL = "FAIL"

    @property
    def severity(self) -> int:
        return {"PASS": 0, "MARGINAL": 1, "FAIL": 2}[self.value]


@dataclass(frozen=True)
class VerificationResult:
    requirement: Requirement
    scope: str
    measured: float
    margin: float
    status: Status


@dataclass(frozen=True)
class RequirementSummary:
    requirement: Requirement
    status: Status
    worst: VerificationResult
    results: tuple[VerificationResult, ...]


def compute_margin(comparator: str, measured: float, threshold: float) -> float:
    if math.isnan(measured):
        return -math.inf
    if math.isinf(measured):
        positive = measured > 0
        return -math.inf if (comparator == "<=") == positive else math.inf
    scale = abs(threshold) if threshold != 0 else 1.0
    if comparator == "<=":
        return (threshold - measured) / scale
    return (measured - threshold) / scale


def classify(margin: float, marginal_band: float) -> Status:
    if margin < 0:
        return Status.FAIL
    if margin < marginal_band:
        return Status.MARGINAL
    return Status.PASS


def verify(analysis, requirements, marginal_band: float = 0.1) -> list[VerificationResult]:
    results = []
    for req in requirements:
        for scope, measured in evaluate_metric(analysis, req.metric):
            margin = compute_margin(req.comparator, measured, req.threshold)
            results.append(VerificationResult(req, scope, measured, margin, classify(margin, marginal_band)))
    return results


def summarize(results: list[VerificationResult]) -> list[RequirementSummary]:
    grouped: dict[str, list[VerificationResult]] = {}
    for result in results:
        grouped.setdefault(result.requirement.id, []).append(result)
    summaries = []
    for items in grouped.values():
        worst = min(items, key=lambda r: r.margin)
        status = max((r.status for r in items), key=lambda s: s.severity)
        summaries.append(RequirementSummary(items[0].requirement, status, worst, tuple(items)))
    return summaries


def overall_status(summaries: list[RequirementSummary]) -> Status:
    if not summaries:
        return Status.PASS
    return max((s.status for s in summaries), key=lambda s: s.severity)
