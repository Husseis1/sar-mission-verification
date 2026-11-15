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
    altitude_km: float = 0.0


def _evaluate(variant: MissionConfig) -> TradePoint:
    analysis = run_analysis(variant)
    summaries = summarize(verify(analysis, variant.requirements, variant.marginal_band))
    return TradePoint(
        satellites_per_plane=variant.planes[0].satellites,
        total_satellites=len(variant.satellites),
        status=overall_status(summaries),
        summaries=tuple(summaries),
        altitude_km=variant.planes[0].altitude_km,
    )


def satellites_per_plane_sweep(config: MissionConfig, counts: list[int]) -> list[TradePoint]:
    return [_evaluate(config.with_satellites_per_plane(count)) for count in counts]


def altitude_sweep(config: MissionConfig, altitudes_km: list[float]) -> list[TradePoint]:
    return [_evaluate(config.with_altitude(altitude)) for altitude in altitudes_km]


def smallest_compliant(points: list[TradePoint]) -> TradePoint | None:
    compliant = [p for p in points if p.status is not Status.FAIL]
    return min(compliant, key=lambda p: p.total_satellites) if compliant else None
