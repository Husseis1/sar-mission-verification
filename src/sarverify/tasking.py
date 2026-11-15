from .access import Access


def schedule_satellite(accesses: list[Access], min_separation_s: float, max_per_orbit: int, orbit_period_s: float) -> tuple[list[Access], list[Access]]:
    accepted: list[Access] = []
    rejected: list[Access] = []
    last_time = None
    per_orbit: dict[int, int] = {}
    for access in sorted(accesses, key=lambda a: a.time_s):
        orbit = int(access.time_s // orbit_period_s)
        too_close = last_time is not None and access.time_s - last_time < min_separation_s
        orbit_full = max_per_orbit > 0 and per_orbit.get(orbit, 0) >= max_per_orbit
        if too_close or orbit_full:
            rejected.append(access)
            continue
        accepted.append(access)
        last_time = access.time_s
        per_orbit[orbit] = per_orbit.get(orbit, 0) + 1
    return accepted, rejected
