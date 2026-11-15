import numpy as np
import pytest

from sarverify.access import find_accesses
from sarverify.config import Sensor, Target
from sarverify.constants import R_EARTH


def flyby(cross_track_km: float, altitude_km: float = 500.0):
    times = np.arange(0.0, 300.0, 10.0)
    y = 7.5 * (times - 151.0)
    r = np.column_stack([np.full_like(y, R_EARTH + altitude_km), y, np.full_like(y, cross_track_km)])
    v = np.tile([0.0, 7.5, 0.0], (times.size, 1))
    return times, r, v


def test_broadside_crossing_time_and_incidence():
    times, r, v = flyby(300.0)
    target = Target("T", 0.0, 0.0)
    accesses = find_accesses("S", times, r, v, target, Sensor(15.0, 45.0))
    assert len(accesses) == 1
    access = accesses[0]
    assert access.time_s == pytest.approx(151.0, abs=1e-6)
    assert access.incidence_deg == pytest.approx(np.degrees(np.arctan2(300.0, 500.0)), abs=1e-6)
    assert access.look_side == "right"
    assert access.slant_range_km == pytest.approx(np.hypot(300.0, 500.0))


def test_look_side_filter():
    times, r, v = flyby(-300.0)
    target = Target("T", 0.0, 0.0)
    assert find_accesses("S", times, r, v, target, Sensor(15.0, 45.0, ("right",))) == []
    left = find_accesses("S", times, r, v, target, Sensor(15.0, 45.0, ("left",)))
    assert [a.look_side for a in left] == ["left"]


def test_incidence_envelope_rejects_near_nadir_and_far_range():
    target = Target("T", 0.0, 0.0)
    sensor = Sensor(15.0, 45.0)
    assert find_accesses("S", *flyby(50.0), target, sensor) == []
    assert find_accesses("S", *flyby(900.0), target, sensor) == []
