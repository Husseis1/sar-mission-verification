import math

import pytest

from sarverify.requirements import Requirement, parse_requirement
from sarverify.verify import Status, VerificationResult, classify, compute_margin, overall_status, summarize


def test_margin_for_upper_and_lower_bounds():
    assert compute_margin("<=", 9.0, 12.0) == pytest.approx(0.25)
    assert compute_margin(">=", 3.0, 4.0) == pytest.approx(-0.25)


def test_margin_for_missing_data():
    assert compute_margin("<=", math.inf, 12.0) == -math.inf
    assert compute_margin(">=", math.inf, 4.0) == math.inf
    assert compute_margin("<=", math.nan, 12.0) == -math.inf


def test_classification_bands():
    assert classify(0.25, 0.1) is Status.PASS
    assert classify(0.05, 0.1) is Status.MARGINAL
    assert classify(0.0, 0.1) is Status.MARGINAL
    assert classify(-0.01, 0.1) is Status.FAIL


def test_summary_reports_worst_scope():
    req = Requirement("R1", "Revisit", "max_revisit_h", "<=", 12.0, "h")
    results = [
        VerificationResult(req, "A", 6.0, 0.5, Status.PASS),
        VerificationResult(req, "B", 11.5, 0.04, Status.MARGINAL),
    ]
    [summary] = summarize(results)
    assert summary.worst.scope == "B"
    assert summary.status is Status.MARGINAL
    assert overall_status([summary]) is Status.MARGINAL


def test_parse_requirement_validates_metric_and_comparator():
    base = {"id": "R", "title": "t", "metric": "max_revisit_h", "comparator": "<=", "threshold": 1}
    assert parse_requirement(base).unit == "h"
    with pytest.raises(ValueError):
        parse_requirement({**base, "metric": "nope"})
    with pytest.raises(ValueError):
        parse_requirement({**base, "comparator": "<"})
