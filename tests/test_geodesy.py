from datetime import datetime, timezone

import numpy as np
import pytest

from sarverify.constants import R_EARTH, WGS84_F
from sarverify.geodesy import eci_to_ecef, elevation_deg, geodetic_to_ecef, gmst_rad, julian_date, local_up


def test_julian_date_of_j2000():
    assert julian_date(datetime(2000, 1, 1, 12, tzinfo=timezone.utc)) == pytest.approx(2451545.0)


def test_gmst_at_j2000():
    theta = gmst_rad(datetime(2000, 1, 1, 12, tzinfo=timezone.utc), np.array([0.0]))
    assert np.degrees(theta[0]) == pytest.approx(280.46061837)


def test_equator_and_pole_positions():
    assert np.allclose(geodetic_to_ecef(0.0, 0.0), [R_EARTH, 0.0, 0.0])
    assert np.allclose(geodetic_to_ecef(90.0, 0.0), [0.0, 0.0, R_EARTH * (1 - WGS84_F)], atol=1e-6)


def test_eci_to_ecef_rotation_preserves_norm():
    r = np.array([[7000.0, 100.0, 50.0], [-3000.0, 6000.0, 2000.0]])
    rotated = eci_to_ecef(r, np.array([0.3, 2.1]))
    assert np.allclose(np.linalg.norm(rotated, axis=1), np.linalg.norm(r, axis=1))
    assert np.allclose(eci_to_ecef(r, np.zeros(2)), r)


def test_elevation_of_zenith_and_horizon():
    site = geodetic_to_ecef(0.0, 0.0)
    up = local_up(0.0, 0.0)
    r = np.array([site + 500.0 * up, site + np.array([0.0, 500.0, 0.0])])
    assert np.allclose(elevation_deg(r, site, up), [90.0, 0.0], atol=1e-9)
