from pathlib import Path

import pytest
import yaml

from sarverify.analysis import run_analysis
from sarverify.cli import main
from sarverify.config import ConfigError, load_config, parse_config
from sarverify.degradation import single_satellite_loss
from sarverify.metrics import max_revisit_h
from sarverify.verify import summarize, verify

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "baltic_maritime.yaml"


@pytest.fixture(scope="module")
def short_config():
    raw = yaml.safe_load(EXAMPLE.read_text())
    raw["mission"]["duration_days"] = 2
    raw["mission"]["step_s"] = 20
    return parse_config(raw)


@pytest.fixture(scope="module")
def analysis(short_config):
    return run_analysis(short_config)


def test_example_config_loads():
    config = load_config(EXAMPLE)
    assert len(config.satellites) == 6
    assert {s.name for s in config.satellites} >= {"SSO-A-1", "SSO-B-3"}
    assert config.planes[0].inclination_deg == pytest.approx(97.63, abs=0.02)


def test_analysis_finds_accesses_and_contacts(analysis):
    assert analysis.accesses
    assert analysis.contacts
    assert all(15.0 <= a.incidence_deg <= 45.0 for a in analysis.accesses)
    assert [a.time_s for a in analysis.accesses] == sorted(a.time_s for a in analysis.accesses)


def test_every_requirement_is_verified_for_every_scope(analysis, short_config):
    summaries = summarize(verify(analysis, short_config.requirements))
    assert [s.requirement.id for s in summaries] == [r.id for r in short_config.requirements]
    for s in summaries:
        expected = len(short_config.targets) if s.requirement.scope_kind == "target" else len(analysis.satellites)
        assert len(s.results) == expected


def test_losing_a_satellite_never_improves_revisit(analysis, short_config):
    target = short_config.targets[0].name
    baseline = max_revisit_h(analysis, target)
    for sat in analysis.satellites:
        assert max_revisit_h(analysis.without(sat), target) >= baseline
    assert len(single_satellite_loss(analysis, short_config.requirements)) == len(analysis.satellites)


def test_invalid_config_is_rejected():
    with pytest.raises(ConfigError):
        parse_config({"mission": {"name": "x"}})


def test_cli_writes_report(tmp_path):
    code = main(["run", str(EXAMPLE), "--out", str(tmp_path), "--no-plots", "--skip-loss"])
    assert code in (0, 1)
    report = (tmp_path / "verification_report.md").read_text()
    assert "Requirements verification matrix" in report
    assert (tmp_path / "verification_results.json").exists()
    rows = (tmp_path / "traceability_matrix.csv").read_text().strip().splitlines()
    assert rows[0].startswith("requirement_id,")
    assert len(rows) > len(load_config(EXAMPLE).requirements)


def test_altitude_change_keeps_sun_synchronous_planes():
    config = load_config(EXAMPLE).with_altitude(620.0)
    assert all(p.altitude_km == 620.0 for p in config.planes)
    assert config.planes[0].inclination_deg == pytest.approx(97.87, abs=0.02)


def test_altitude_sweep_returns_one_point_per_altitude(short_config):
    from sarverify.trade import altitude_sweep

    points = altitude_sweep(short_config, [500.0, 620.0])
    assert [p.altitude_km for p in points] == [500.0, 620.0]
    assert all(len(p.summaries) == len(short_config.requirements) for p in points)


def test_tasking_constraints_remove_conflicting_opportunities(short_config):
    from dataclasses import replace

    free = run_analysis(short_config)
    constrained_config = replace(
        short_config,
        operations=replace(short_config.operations, min_acquisition_separation_s=120.0, max_acquisitions_per_orbit=2),
    )
    constrained = run_analysis(constrained_config)
    assert len(constrained.accesses) + len(constrained.unscheduled) == len(free.accesses)
    assert constrained.unscheduled
    for sat in constrained.satellites:
        times = sorted(a.time_s for a in constrained.accesses if a.satellite == sat)
        assert all(b - a >= 120.0 for a, b in zip(times, times[1:]))


def test_phase_offset_applies_to_successive_planes():
    config = load_config(EXAMPLE).with_plane_phase_offset(30.0)
    assert config.planes[0].phase_offset_deg == 0.0
    assert config.planes[1].phase_offset_deg == 30.0
    assert config.satellites[3].arg_lat_deg == pytest.approx(30.0)


def test_best_point_prefers_lower_severity(short_config):
    from sarverify.trade import best_point, phase_offset_sweep

    points = phase_offset_sweep(short_config, [0.0, 30.0])
    best = best_point(points)
    assert best.status.severity == min(p.status.severity for p in points)
