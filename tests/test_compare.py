
import pytest

from sarverify.compare import build_decision_memo, evaluate_option, recommend
from sarverify.config import parse_config
from tests_support import example_raw


@pytest.fixture(scope="module")
def options():
    raw = example_raw(duration_days=2, step_s=20)
    base = parse_config(raw)
    raw_b = example_raw(duration_days=2, step_s=20)
    raw_b["ground_stations"].append({"name": "Southern Finland", "lat_deg": 60.19, "lon_deg": 24.83})
    raw_b["mission"]["name"] = "With local station"
    return [evaluate_option("A", base), evaluate_option("B", parse_config(raw_b))]


def test_local_station_cuts_latency(options):
    a, b = options
    lat_a = next(s for s in a.summaries if s.requirement.metric == "latency_p90_min").worst.measured
    lat_b = next(s for s in b.summaries if s.requirement.metric == "latency_p90_min").worst.measured
    assert lat_b < lat_a


def test_recommendation_prefers_fewer_problems(options):
    best = recommend(options)
    assert best.rank_key() == min(o.rank_key() for o in options)


def test_decision_memo_lists_every_requirement(options):
    memo = build_decision_memo(options)
    for s in options[0].summaries:
        assert s.requirement.id in memo
    assert "## Recommendation" in memo
