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
    phase_offset_deg: float = 0.0


def _evaluate(variant: MissionConfig) -> TradePoint:
    analysis = run_analysis(variant)
    summaries = summarize(verify(analysis, variant.requirements, variant.marginal_band))
    return TradePoint(
        satellites_per_plane=variant.planes[0].satellites,
        total_satellites=len(variant.satellites),
        status=overall_status(summaries),
        summaries=tuple(summaries),
        altitude_km=variant.planes[0].altitude_km,
        phase_offset_deg=variant.planes[1].phase_offset_deg if len(variant.planes) > 1 else 0.0,
    )


def satellites_per_plane_sweep(config: MissionConfig, counts: list[int]) -> list[TradePoint]:
    return [_evaluate(config.with_satellites_per_plane(count)) for count in counts]


def altitude_sweep(config: MissionConfig, altitudes_km: list[float]) -> list[TradePoint]:
    return [_evaluate(config.with_altitude(altitude)) for altitude in altitudes_km]


def smallest_compliant(points: list[TradePoint]) -> TradePoint | None:
    compliant = [p for p in points if p.status is not Status.FAIL]
    return min(compliant, key=lambda p: p.total_satellites) if compliant else None


def phase_offset_sweep(config: MissionConfig, offsets_deg: list[float]) -> list[TradePoint]:
    return [_evaluate(config.with_plane_phase_offset(offset)) for offset in offsets_deg]


def balanced_score(point: TradePoint) -> float:
    margins = [min(max(s.worst.margin, -1.0), 1.0) for s in point.summaries]
    return sum(margins) / len(margins) if margins else 0.0


def best_point(points: list[TradePoint]) -> TradePoint:
    return min(points, key=lambda p: (p.status.severity, -balanced_score(p)))
