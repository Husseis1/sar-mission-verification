import numpy as np
import pytest

from sarverify.config import parse_config
from sarverify.robustness import perturb, phasing_monte_carlo
from tests_support import example_raw


@pytest.fixture(scope="module")
def config():
    return parse_config(example_raw(duration_days=1, step_s=30))


def test_zero_sigma_perturbation_is_identity(config):
    perturbed = perturb(config, np.random.default_rng(1), 0.0, 0.0)
    assert [s.arg_lat_deg for s in perturbed.satellites] == pytest.approx([s.arg_lat_deg for s in config.satellites])


def test_perturbation_keeps_altitude_and_inclination(config):
    perturbed = perturb(config, np.random.default_rng(1), 20.0, 2.0)
    for a, b in zip(config.satellites, perturbed.satellites):
        assert a.altitude_km == b.altitude_km and a.inclination_deg == b.inclination_deg
        assert a.name == b.name


def test_monte_carlo_is_reproducible_and_bounded(config):
    first = phasing_monte_carlo(config, 4, 10.0, 0.5, seed=3)
    second = phasing_monte_carlo(config, 4, 10.0, 0.5, seed=3)
    assert first == second
    assert 0.0 <= first.all_compliant_probability <= 1.0
    for spread in first.spreads:
        assert spread.p10 <= spread.p50 <= spread.p90
