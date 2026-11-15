from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Access:
    satellite: str
    target: str
    time_s: float
    incidence_deg: float
    look_side: str
    slant_range_km: float
    latency_s: float | None = None


def find_accesses(satellite: str, times: np.ndarray, r_ecef: np.ndarray, v_ecef: np.ndarray, target, sensor) -> list[Access]:
    p = target.ecef
    up = target.up
    doppler = np.einsum("ij,ij->i", p[None, :] - r_ecef, v_ecef)
    k = np.nonzero((doppler[:-1] > 0.0) & (doppler[1:] <= 0.0))[0]
    if k.size == 0:
        return []
    frac = doppler[k] / (doppler[k] - doppler[k + 1])
    t = times[k] + frac * (times[k + 1] - times[k])
    r = r_ecef[k] + frac[:, None] * (r_ecef[k + 1] - r_ecef[k])
    v = v_ecef[k] + frac[:, None] * (v_ecef[k + 1] - v_ecef[k])
    los = r - p
    rng = np.linalg.norm(los, axis=1)
    incidence = np.degrees(np.arccos(np.clip(los @ up / rng, -1.0, 1.0)))
    normal = np.cross(r, v)
    side = np.where(np.einsum("ij,ij->i", p[None, :] - r, normal) > 0.0, "left", "right")
    keep = (
        (incidence >= sensor.incidence_min_deg)
        & (incidence <= sensor.incidence_max_deg)
        & np.isin(side, sensor.look_sides)
    )
    return [
        Access(satellite, target.name, float(t[i]), float(incidence[i]), str(side[i]), float(rng[i]))
        for i in np.nonzero(keep)[0]
    ]
