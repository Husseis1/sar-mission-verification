from dataclasses import dataclass, replace

import numpy as np

from .analysis import run_analysis
from .config import MissionConfig
from .verify import Status, summarize, verify


@dataclass(frozen=True)
class RequirementSpread:
    requirement_id: str
    statement: str
    compliance_probability: float
    p10: float
    p50: float
    p90: float


@dataclass(frozen=True)
class RobustnessResult:
    samples: int
    phase_sigma_deg: float
    raan_sigma_deg: float
    all_compliant_probability: float
    spreads: tuple[RequirementSpread, ...]


def perturb(config: MissionConfig, rng: np.random.Generator, phase_sigma_deg: float, raan_sigma_deg: float) -> MissionConfig:
    satellites = tuple(
        replace(
            sat,
            arg_lat_deg=(sat.arg_lat_deg + rng.normal(0.0, phase_sigma_deg)) % 360.0,
            raan_deg=(sat.raan_deg + rng.normal(0.0, raan_sigma_deg)) % 360.0,
        )
        for sat in config.satellites
    )
    return config.with_satellites(satellites)


def phasing_monte_carlo(config: MissionConfig, samples: int, phase_sigma_deg: float, raan_sigma_deg: float, seed: int = 0) -> RobustnessResult:
    rng = np.random.default_rng(seed)
    ids = [r.id for r in config.requirements]
    measured = {i: [] for i in ids}
    compliant = {i: 0 for i in ids}
    all_ok = 0
    for _ in range(samples):
        variant = perturb(config, rng, phase_sigma_deg, raan_sigma_deg)
        summaries = summarize(verify(run_analysis(variant), variant.requirements, variant.marginal_band))
        ok = True
        for s in summaries:
            measured[s.requirement.id].append(s.worst.measured)
            if s.status is not Status.FAIL:
                compliant[s.requirement.id] += 1
            else:
                ok = False
        all_ok += ok
    spreads = []
    for req in config.requirements:
        values = np.array(measured[req.id], dtype=float)
        finite = values[np.isfinite(values)]
        p10, p50, p90 = np.percentile(finite, [10, 50, 90]) if finite.size else (np.inf, np.inf, np.inf)
        spreads.append(RequirementSpread(req.id, req.statement, compliant[req.id] / samples, float(p10), float(p50), float(p90)))
    return RobustnessResult(samples, phase_sigma_deg, raan_sigma_deg, all_ok / samples, tuple(spreads))
