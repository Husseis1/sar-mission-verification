import numpy as np
import pytest

from sarverify.constants import TROPICAL_YEAR_S
from sarverify.orbit import Satellite, sso_inclination_deg


def test_sso_inclination_matches_reference_values():
    assert sso_inclination_deg(560.0) == pytest.approx(97.63, abs=0.02)
    assert sso_inclination_deg(800.0) == pytest.approx(98.60, abs=0.03)


def test_sso_orbit_precesses_once_per_year():
    sat = Satellite("S", 560.0, sso_inclination_deg(560.0), 0.0, 0.0)
    assert sat.raan_rate * TROPICAL_YEAR_S == pytest.approx(2 * np.pi, rel=1e-9)


def test_nodal_period_is_close_to_keplerian():
    sat = Satellite("S", 560.0, 97.6, 0.0, 0.0)
    assert sat.nodal_period_s / 60.0 == pytest.approx(95.98, abs=0.1)


def test_circular_orbit_keeps_constant_radius():
    sat = Satellite("S", 500.0, 53.0, 10.0, 20.0)
    r = sat.position_eci(np.linspace(0.0, 86400.0, 500))
    assert np.allclose(np.linalg.norm(r, axis=1), sat.semi_major_axis_km)


def test_inclination_bounds_latitude():
    sat = Satellite("S", 500.0, 45.0, 0.0, 0.0)
    r = sat.position_eci(np.linspace(0.0, sat.nodal_period_s, 2000))
    max_lat = np.degrees(np.arcsin(np.abs(r[:, 2]) / np.linalg.norm(r, axis=1))).max()
    assert max_lat == pytest.approx(45.0, abs=0.05)


def test_no_sso_solution_raises():
    with pytest.raises(ValueError):
        sso_inclination_deg(10000.0)
