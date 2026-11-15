from dataclasses import dataclass
from typing import Callable

import numpy as np

HOUR_S = 3600.0
DAY_S = 86400.0


def access_times(analysis, target: str) -> np.ndarray:
    return np.sort(np.array([a.time_s for a in analysis.accesses if a.target == target], dtype=float))


def revisit_gaps_h(analysis, target: str) -> np.ndarray:
    times = access_times(analysis, target)
    if times.size < 2:
        return np.array([], dtype=float)
    return np.diff(times) / HOUR_S


def max_revisit_h(analysis, target: str) -> float:
    gaps = revisit_gaps_h(analysis, target)
    return float(gaps.max()) if gaps.size else float("inf")


def mean_revisit_h(analysis, target: str) -> float:
    gaps = revisit_gaps_h(analysis, target)
    return float(gaps.mean()) if gaps.size else float("inf")


def daily_access_rate(analysis, target: str) -> float:
    return access_times(analysis, target).size / (analysis.duration_s / DAY_S)


def latencies_min(analysis, target: str) -> np.ndarray:
    return np.array(
        [a.latency_s / 60.0 for a in analysis.accesses if a.target == target and a.latency_s is not None],
        dtype=float,
    )


def latency_p90_min(analysis, target: str) -> float:
    lat = latencies_min(analysis, target)
    return float(np.percentile(lat, 90)) if lat.size else float("inf")


def delivered_fraction(analysis, target: str) -> float:
    total = [a for a in analysis.accesses if a.target == target]
    if not total:
        return 0.0
    return sum(a.latency_s is not None for a in total) / len(total)


def daily_contact_min(analysis, satellite: str) -> float:
    total = sum(c.duration_s for c in analysis.contacts if c.satellite == satellite)
    return total / 60.0 / (analysis.duration_s / DAY_S)


def daily_contact_count(analysis, satellite: str) -> float:
    count = sum(1 for c in analysis.contacts if c.satellite == satellite)
    return count / (analysis.duration_s / DAY_S)


@dataclass(frozen=True)
class MetricSpec:
    scope: str
    label: str
    unit: str
    fn: Callable


METRICS: dict[str, MetricSpec] = {
    "max_revisit_h": MetricSpec("target", "Maximum revisit gap", "h", max_revisit_h),
    "mean_revisit_h": MetricSpec("target", "Mean revisit gap", "h", mean_revisit_h),
    "daily_access_rate": MetricSpec("target", "Imaging opportunities per day", "1/day", daily_access_rate),
    "latency_p90_min": MetricSpec("target", "90th percentile delivery latency", "min", latency_p90_min),
    "delivered_fraction": MetricSpec("target", "Fraction of acquisitions delivered", "", delivered_fraction),
    "daily_contact_min": MetricSpec("satellite", "Ground contact time per day", "min", daily_contact_min),
    "daily_contact_count": MetricSpec("satellite", "Ground contacts per day", "1/day", daily_contact_count),
}


def evaluate_metric(analysis, metric: str) -> list[tuple[str, float]]:
    spec = METRICS[metric]
    scopes = [t.name for t in analysis.config.targets] if spec.scope == "target" else list(analysis.satellites)
    return [(scope, spec.fn(analysis, scope)) for scope in scopes]
