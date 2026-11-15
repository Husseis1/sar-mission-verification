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
