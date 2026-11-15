from sarverify.access import Access
from sarverify.tasking import schedule_satellite


def make(times):
    return [Access("S", f"T{i}", t, 30.0, "right", 700.0) for i, t in enumerate(times)]


def test_unconstrained_schedule_keeps_everything():
    accepted, rejected = schedule_satellite(make([0, 10, 20]), 0.0, 0, 5000.0)
    assert len(accepted) == 3 and not rejected


def test_minimum_separation_rejects_conflicts():
    accepted, rejected = schedule_satellite(make([0, 30, 70, 100]), 60.0, 0, 5000.0)
    assert [a.time_s for a in accepted] == [0, 70]
    assert [a.time_s for a in rejected] == [30, 100]


def test_orbit_budget_resets_each_orbit():
    accepted, _ = schedule_satellite(make([0, 100, 200, 5100, 5200]), 0.0, 2, 5000.0)
    assert [a.time_s for a in accepted] == [0, 100, 5100, 5200]


def test_greedy_schedule_is_maximal_for_separation():
    times = [0, 50, 100, 150, 200]
    accepted, _ = schedule_satellite(make(times), 60.0, 0, 5000.0)
    assert len(accepted) == 3


def test_conflicts_are_resolved_in_favour_of_least_served_target():
    accesses = [
        Access("S", "Busy", 0.0, 30.0, "right", 700.0),
        Access("S", "Starved", 20.0, 30.0, "right", 700.0),
    ]
    accepted, rejected = schedule_satellite(accesses, 60.0, 0, 5000.0, served={"Busy": 5})
    assert [a.target for a in accepted] == ["Starved"]
    assert [a.target for a in rejected] == ["Busy"]


def test_served_counts_are_updated_for_the_next_satellite():
    served = {}
    schedule_satellite(make([0, 100]), 60.0, 0, 5000.0, served)
    assert served == {"T0": 1, "T1": 1}
