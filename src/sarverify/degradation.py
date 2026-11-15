from dataclasses import dataclass

from .verify import RequirementSummary, Status, overall_status, summarize, verify


@dataclass(frozen=True)
class LossCase:
    lost_satellite: str
    summaries: tuple[RequirementSummary, ...]

    @property
    def status(self) -> Status:
        return overall_status(list(self.summaries))

    def ids_with(self, status: Status) -> list[str]:
        return [s.requirement.id for s in self.summaries if s.status is status]


def single_satellite_loss(analysis, requirements, marginal_band: float = 0.1) -> list[LossCase]:
    cases = []
    for name in analysis.satellites:
        degraded = analysis.without(name)
        cases.append(LossCase(name, tuple(summarize(verify(degraded, requirements, marginal_band)))))
    return sorted(cases, key=lambda c: (-c.status.severity, -len(c.ids_with(Status.FAIL)), c.lost_satellite))
