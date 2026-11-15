from dataclasses import dataclass

from .analysis import run_analysis
from .config import MissionConfig
from .verify import RequirementSummary, Status, overall_status, summarize, verify


@dataclass(frozen=True)
class TradePoint:
    satellites_per_plane: int
    total_satellites: int
    status: Status
    summaries: tuple[RequirementSummary, ...]


def satellites_per_plane_sweep(config: MissionConfig, counts: list[int]) -> list[TradePoint]:
    points = []
    for count in counts:
        variant = config.with_satellites_per_plane(count)
        analysis = run_analysis(variant)
        summaries = summarize(verify(analysis, variant.requirements, variant.marginal_band))
        points.append(TradePoint(count, len(variant.satellites), overall_status(summaries), tuple(summaries)))
    return points


def smallest_compliant(points: list[TradePoint]) -> TradePoint | None:
    compliant = [p for p in points if p.status is not Status.FAIL]
    return min(compliant, key=lambda p: p.total_satellites) if compliant else None
