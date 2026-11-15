import numpy as np
import pytest

from sarverify.ground import Contact, delivery_latency_s, mask_to_intervals


def test_mask_to_intervals():
    times = np.arange(10.0)
    mask = np.array([0, 1, 1, 0, 0, 1, 0, 1, 1, 1], dtype=bool)
    assert mask_to_intervals(times, mask) == [(1.0, 2.0), (5.0, 5.0), (7.0, 9.0)]
    assert mask_to_intervals(times, np.zeros(10, dtype=bool)) == []


def test_latency_uses_first_contact_that_fits_downlink():
    contacts = [Contact("S", "A", 1000.0, 1100.0), Contact("S", "B", 2000.0, 2600.0)]
    assert delivery_latency_s(500.0, contacts, 300.0, 600.0) == pytest.approx(2000.0 + 300.0 + 600.0 - 500.0)


def test_latency_inside_ongoing_contact():
    contacts = [Contact("S", "A", 0.0, 1000.0)]
    assert delivery_latency_s(100.0, contacts, 120.0, 0.0) == pytest.approx(120.0)


def test_latency_none_when_no_contact_fits():
    contacts = [Contact("S", "A", 0.0, 100.0)]
    assert delivery_latency_s(500.0, contacts, 60.0, 0.0) is None
    assert delivery_latency_s(500.0, [], 60.0, 0.0) is None
