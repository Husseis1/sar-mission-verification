from dataclasses import dataclass

import numpy as np

from .constants import J2, MU_EARTH, R_EARTH, TROPICAL_YEAR_S


@dataclass(frozen=True)
class Satellite:
    name: str
    altitude_km: float
    inclination_deg: float
    raan_deg: float
    arg_lat_deg: float

    @property
    def semi_major_axis_km(self) -> float:
        return R_EARTH + self.altitude_km

    @property
    def mean_motion(self) -> float:
        return float(np.sqrt(MU_EARTH / self.semi_major_axis_km**3))

    @property
    def _j2_factor(self) -> float:
        return 1.5 * J2 * (R_EARTH / self.semi_major_axis_km) ** 2

    @property
    def raan_rate(self) -> float:
        return -self._j2_factor * self.mean_motion * np.cos(np.radians(self.inclination_deg))

    @property
    def arg_lat_rate(self) -> float:
        c = np.cos(np.radians(self.inclination_deg))
        return self.mean_motion * (1.0 + 0.5 * self._j2_factor * (8.0 * c * c - 2.0))

    @property
    def nodal_period_s(self) -> float:
        return 2.0 * np.pi / self.arg_lat_rate

    def position_eci(self, t_s: np.ndarray) -> np.ndarray:
        t = np.asarray(t_s, dtype=float)
        a = self.semi_major_axis_km
        inc = np.radians(self.inclination_deg)
        u = np.radians(self.arg_lat_deg) + self.arg_lat_rate * t
        raan = np.radians(self.raan_deg) + self.raan_rate * t
        cu, su = np.cos(u), np.sin(u)
        co, so = np.cos(raan), np.sin(raan)
        ci, si = np.cos(inc), np.sin(inc)
        x = a * (co * cu - so * su * ci)
        y = a * (so * cu + co * su * ci)
        z = a * (su * si)
        return np.column_stack([x, y, z])


def sso_inclination_deg(altitude_km: float) -> float:
    a = R_EARTH + altitude_km
    n = np.sqrt(MU_EARTH / a**3)
    required_rate = 2.0 * np.pi / TROPICAL_YEAR_S
    cos_i = -required_rate / (1.5 * J2 * (R_EARTH / a) ** 2 * n)
    if not -1.0 <= cos_i <= 1.0:
        raise ValueError(f"No sun-synchronous inclination exists for altitude {altitude_km} km")
    return float(np.degrees(np.arccos(cos_i)))
