import math
from dataclasses import dataclass

from .analysis import run_analysis
from .config import MissionConfig
from .degradation import single_satellite_loss
from .report import fmt, fmt_margin
from .verify import RequirementSummary, Status, overall_status, summarize, verify


@dataclass(frozen=True)
class OptionResult:
    label: str
    config: MissionConfig
    summaries: tuple[RequirementSummary, ...]
    loss_failures: int

    @property
    def status(self) -> Status:
        return overall_status(list(self.summaries))

    def count(self, status: Status) -> int:
        return sum(1 for s in self.summaries if s.status is status)

    @property
    def min_margin(self) -> float:
        finite = [s.worst.margin for s in self.summaries if not math.isinf(s.worst.margin)]
        return min(finite) if finite else -math.inf

    def rank_key(self) -> tuple:
        return (self.count(Status.FAIL), self.count(Status.MARGINAL), self.loss_failures, -self.min_margin)


def evaluate_option(label: str, config: MissionConfig) -> OptionResult:
    analysis = run_analysis(config)
    summaries = summarize(verify(analysis, config.requirements, config.marginal_band))
    loss = single_satellite_loss(analysis, config.requirements, config.marginal_band)
    failures = sum(1 for c in loss if c.status is Status.FAIL)
    return OptionResult(label, config, tuple(summaries), failures)


def recommend(options: list[OptionResult]) -> OptionResult:
    return min(options, key=lambda o: o.rank_key())


def build_decision_memo(options: list[OptionResult]) -> str:
    best = recommend(options)
    ids = [s.requirement.id for s in options[0].summaries]
    header = ["Requirement", "Criterion"] + [o.label for o in options]
    rows = []
    for i, req_id in enumerate(ids):
        req = options[0].summaries[i].requirement
        cells = []
        for o in options:
            match = next((s for s in o.summaries if s.requirement.id == req_id), None)
            cells.append("n/a" if match is None else f"{fmt(match.worst.measured)} ({fmt_margin(match.worst.margin)}, {match.status.value})")
        rows.append([req_id, req.statement] + cells)
    lines = [
        "# Option comparison",
        "",
        "| Option | Mission | Satellites | Ground stations | Status | FAIL | MARGINAL | Loss cases that fail | Smallest margin |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for o in options:
        lines.append(
            f"| {o.label} | {o.config.name} | {len(o.config.satellites)} | {len(o.config.ground_stations)} | {o.status.value} | "
            f"{o.count(Status.FAIL)} | {o.count(Status.MARGINAL)} | {o.loss_failures}/{len(o.config.satellites)} | {fmt_margin(o.min_margin)} |"
        )
    lines += ["", "## Requirement by requirement", "", "| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    lines += [
        "",
        "## Recommendation",
        "",
        f"Option {best.label} ({best.config.name}) ranks first: fewest failed requirements, then fewest marginal ones, "
        f"then best resilience to losing a satellite, then the largest smallest margin.",
        "",
    ]
    if best.loss_failures:
        lines.append(
            f"Residual risk: losing any one of {best.loss_failures} satellites still breaks at least one requirement in option {best.label}; "
            "track spare capacity or replacement lead time in the program risk register."
        )
        lines.append("")
    return "\n".join(lines)
