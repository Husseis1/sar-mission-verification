import json
import math
from datetime import datetime, timezone

from . import __version__
from .degradation import LossCase
from .metrics import (
    daily_access_rate,
    daily_contact_count,
    daily_contact_min,
    delivered_fraction,
    latency_p90_min,
    max_revisit_h,
    mean_revisit_h,
)
from .verify import RequirementSummary, Status, overall_status

ASSUMPTIONS = (
    "Circular orbits propagated analytically with secular J2 effects (RAAN precession and argument-of-latitude drift); drag and higher-order harmonics are neglected.",
    "An imaging opportunity is the zero-Doppler (broadside) crossing of a target, accepted when the incidence angle and look side are inside the sensor envelope.",
    "Revisit statistics use gaps between consecutive opportunities inside the analysis window; edge gaps at the window boundaries are excluded.",
    "Delivery latency assumes the acquisition is downlinked in the first contact of the same satellite that can fit the full downlink, followed by fixed ground processing time.",
    "Tasking conflicts are resolved per satellite by a greedy earliest-first scheduler with a minimum separation between acquisitions and an optional per-orbit acquisition budget; customer priorities and power or thermal limits beyond that budget are not modelled.",
)


def fmt(value: float, digits: int = 2) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "n/a"
    if math.isinf(value):
        return "no data" if value > 0 else "-inf"
    return f"{value:.{digits}f}"


def fmt_margin(margin: float) -> str:
    if math.isinf(margin):
        return "+inf" if margin > 0 else "-inf"
    return f"{margin * 100:+.1f}%"


def _table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def _incidence_range(analysis, target: str) -> str:
    values = [a.incidence_deg for a in analysis.accesses if a.target == target]
    return f"{min(values):.1f} - {max(values):.1f}" if values else "n/a"


def _tasking_summary(ops) -> str:
    if not ops.constrains_tasking:
        return "unconstrained (every geometric opportunity counted)"
    parts = []
    if ops.min_acquisition_separation_s > 0:
        parts.append(f"min {ops.min_acquisition_separation_s:g} s between acquisitions")
    if ops.max_acquisitions_per_orbit > 0:
        parts.append(f"max {ops.max_acquisitions_per_orbit} acquisitions per orbit")
    return ", ".join(parts)


def build_markdown(analysis, summaries: list[RequirementSummary], loss_cases: list[LossCase] | None = None) -> str:
    cfg = analysis.config
    status = overall_status(summaries)
    out = [
        f"# Mission Verification Report: {cfg.name}",
        "",
        f"- Customer: {cfg.customer or 'n/a'}",
        f"- Analysis window: {cfg.epoch:%Y-%m-%d %H:%M} UTC + {cfg.duration_days:g} days, step {cfg.step_s:g} s",
        f"- Constellation: {len(analysis.satellites)} satellites in {len(cfg.planes)} planes",
        f"- Tasking: {_tasking_summary(cfg.operations)}",
        f"- Generated: {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC by sarverify {__version__}",
        "",
        f"**Acceptance status: {status.value}**",
        "",
        "## 1. Requirements verification matrix",
        "",
        _table(
            ["ID", "Requirement", "Method", "Criterion", "Worst case", "Scope", "Margin", "Status"],
            [
                [
                    s.requirement.id,
                    s.requirement.title,
                    s.requirement.method,
                    s.requirement.statement,
                    fmt(s.worst.measured),
                    s.worst.scope,
                    fmt_margin(s.worst.margin),
                    s.status.value,
                ]
                for s in summaries
            ],
        ),
        "",
        f"Margins below {cfg.marginal_band * 100:.0f}% are reported as MARGINAL.",
        "",
        "## 2. Coverage by area of interest",
        "",
        _table(
            ["AOI", "Opportunities/day", "Lost to conflicts", "Mean revisit (h)", "Max revisit (h)", "P90 latency (min)", "Delivered", "Incidence (deg)"],
            [
                [
                    t.name,
                    fmt(daily_access_rate(analysis, t.name)),
                    str(sum(1 for a in analysis.unscheduled if a.target == t.name)),
                    fmt(mean_revisit_h(analysis, t.name)),
                    fmt(max_revisit_h(analysis, t.name)),
                    fmt(latency_p90_min(analysis, t.name), 1),
                    f"{delivered_fraction(analysis, t.name) * 100:.0f}%",
                    _incidence_range(analysis, t.name),
                ]
                for t in cfg.targets
            ],
        ),
        "",
        "## 3. Ground segment contacts",
        "",
        _table(
            ["Satellite", "Contacts/day", "Contact time (min/day)"],
            [[s, fmt(daily_contact_count(analysis, s), 1), fmt(daily_contact_min(analysis, s), 1)] for s in analysis.satellites],
        ),
        "",
    ]
    if loss_cases is not None:
        out += [
            "## 4. Single-satellite loss analysis",
            "",
            "Each row re-runs the verification with one satellite removed, to show which requirements depend on full constellation availability.",
            "",
            _table(
                ["Lost satellite", "Status", "Failed requirements", "Marginal requirements"],
                [
                    [
                        c.lost_satellite,
                        c.status.value,
                        ", ".join(c.ids_with(Status.FAIL)) or "-",
                        ", ".join(c.ids_with(Status.MARGINAL)) or "-",
                    ]
                    for c in loss_cases
                ],
            ),
            "",
        ]
    out += ["## 5. Detailed results", ""]
    for s in summaries:
        out += [f"### {s.requirement.id}: {s.requirement.title}", ""]
        if s.requirement.rationale:
            out += [f"Rationale: {s.requirement.rationale}", ""]
        out += [
            _table(
                ["Scope", "Measured", "Threshold", "Margin", "Status"],
                [
                    [r.scope, fmt(r.measured), f"{r.requirement.comparator} {r.requirement.threshold:g} {r.requirement.unit}", fmt_margin(r.margin), r.status.value]
                    for r in s.results
                ],
            ),
            "",
        ]
    out += ["## 6. Assumptions and limitations", ""] + [f"- {a}" for a in ASSUMPTIONS] + [""]
    return "\n".join(out)


def _num(value: float):
    return None if value is None or math.isinf(value) or math.isnan(value) else round(value, 4)


def build_json(analysis, summaries: list[RequirementSummary], loss_cases: list[LossCase] | None = None) -> str:
    cfg = analysis.config
    payload = {
        "mission": cfg.name,
        "customer": cfg.customer,
        "epoch": cfg.epoch.isoformat(),
        "duration_days": cfg.duration_days,
        "status": overall_status(summaries).value,
        "requirements": [
            {
                "id": s.requirement.id,
                "title": s.requirement.title,
                "metric": s.requirement.metric,
                "criterion": s.requirement.statement,
                "status": s.status.value,
                "worst_scope": s.worst.scope,
                "worst_measured": _num(s.worst.measured),
                "worst_margin": _num(s.worst.margin),
                "results": [
                    {"scope": r.scope, "measured": _num(r.measured), "margin": _num(r.margin), "status": r.status.value}
                    for r in s.results
                ],
            }
            for s in summaries
        ],
        "accesses": [
            {
                "satellite": a.satellite,
                "target": a.target,
                "time_s": round(a.time_s, 1),
                "incidence_deg": round(a.incidence_deg, 2),
                "look_side": a.look_side,
                "latency_min": None if a.latency_s is None else round(a.latency_s / 60.0, 1),
            }
            for a in analysis.accesses
        ],
    }
    if loss_cases is not None:
        payload["single_satellite_loss"] = [
            {
                "lost_satellite": c.lost_satellite,
                "status": c.status.value,
                "failed": c.ids_with(Status.FAIL),
                "marginal": c.ids_with(Status.MARGINAL),
            }
            for c in loss_cases
        ]
    return json.dumps(payload, indent=2)
