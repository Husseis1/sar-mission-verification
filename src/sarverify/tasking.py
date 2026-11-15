from .access import Access


def _conflict_groups(accesses: list[Access], min_separation_s: float) -> list[list[Access]]:
    groups: list[list[Access]] = []
    for access in accesses:
        if groups and access.time_s - groups[-1][-1].time_s < min_separation_s:
            groups[-1].append(access)
        else:
            groups.append([access])
    return groups


def schedule_satellite(
    accesses: list[Access],
    min_separation_s: float,
    max_per_orbit: int,
    orbit_period_s: float,
    served: dict[str, int] | None = None,
) -> tuple[list[Access], list[Access]]:
    served = {} if served is None else served
    accepted: list[Access] = []
    rejected: list[Access] = []
    per_orbit: dict[int, int] = {}
    last_time = None
    for group in _conflict_groups(sorted(accesses, key=lambda a: a.time_s), min_separation_s):
        remaining = list(group)
        while remaining:
            feasible = [
                a
                for a in remaining
                if (last_time is None or a.time_s - last_time >= min_separation_s)
                and (max_per_orbit <= 0 or per_orbit.get(int(a.time_s // orbit_period_s), 0) < max_per_orbit)
            ]
            if not feasible:
                rejected.extend(remaining)
                break
            choice = min(feasible, key=lambda a: (served.get(a.target, 0), a.time_s))
            accepted.append(choice)
            served[choice.target] = served.get(choice.target, 0) + 1
            per_orbit[int(choice.time_s // orbit_period_s)] = per_orbit.get(int(choice.time_s // orbit_period_s), 0) + 1
            last_time = choice.time_s
            rejected.extend(a for a in remaining if a is not choice and a.time_s <= choice.time_s)
            remaining = [a for a in remaining if a.time_s > choice.time_s]
    return accepted, rejected
