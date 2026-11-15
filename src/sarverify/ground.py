from dataclasses import dataclass

import numpy as np

from .geodesy import elevation_deg


@dataclass(frozen=True)
class Contact:
    satellite: str
    station: str
    start_s: float
    end_s: float

    @property
    def duration_s(self) -> float:
        return self.end_s - self.start_s


def mask_to_intervals(times: np.ndarray, mask: np.ndarray) -> list[tuple[float, float]]:
    mask = np.asarray(mask, dtype=bool)
    if not mask.any():
        return []
    edges = np.diff(np.concatenate([[0], mask.astype(np.int8), [0]]))
    starts = np.nonzero(edges == 1)[0]
    ends = np.nonzero(edges == -1)[0] - 1
    return [(float(times[s]), float(times[e])) for s, e in zip(starts, ends)]


def find_contacts(satellite: str, times: np.ndarray, r_ecef: np.ndarray, station, min_duration_s: float = 0.0) -> list[Contact]:
    visible = elevation_deg(r_ecef, station.ecef, station.up) >= station.min_elevation_deg
    return [
        Contact(satellite, station.name, start, end)
        for start, end in mask_to_intervals(times, visible)
        if end - start >= min_duration_s
    ]


def delivery_latency_s(acquisition_s: float, contacts: list[Contact], downlink_s: float, processing_s: float) -> float | None:
    if not contacts:
        return None
    starts = np.array([c.start_s for c in contacts])
    ends = np.array([c.end_s for c in contacts])
    begin = np.maximum(starts, acquisition_s)
    feasible = begin + downlink_s <= ends
    if not feasible.any():
        return None
    return float(begin[feasible].min() + downlink_s + processing_s - acquisition_s)
