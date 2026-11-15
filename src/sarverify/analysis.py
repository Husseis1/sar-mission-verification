from dataclasses import dataclass, replace

import numpy as np

from .access import Access, find_accesses
from .config import MissionConfig
from .geodesy import eci_to_ecef, gmst_rad
from .ground import Contact, delivery_latency_s, find_contacts
from .orbit import Satellite


@dataclass(frozen=True)
class MissionAnalysis:
    config: MissionConfig
    satellites: tuple[str, ...]
    accesses: tuple[Access, ...]
    contacts: tuple[Contact, ...]

    @property
    def duration_s(self) -> float:
        return self.config.duration_s

    def without(self, *names: str) -> "MissionAnalysis":
        lost = set(names)
        return replace(
            self,
            satellites=tuple(s for s in self.satellites if s not in lost),
            accesses=tuple(a for a in self.accesses if a.satellite not in lost),
            contacts=tuple(c for c in self.contacts if c.satellite not in lost),
        )


def time_grid(config: MissionConfig) -> np.ndarray:
    return np.arange(0.0, config.duration_s + config.step_s / 2.0, config.step_s)


def propagate(satellite: Satellite, config: MissionConfig, times: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    r_ecef = eci_to_ecef(satellite.position_eci(times), gmst_rad(config.epoch, times))
    v_ecef = np.gradient(r_ecef, times, axis=0)
    return r_ecef, v_ecef


def run_analysis(config: MissionConfig) -> MissionAnalysis:
    times = time_grid(config)
    downlink_s = config.operations.downlink_duration_min * 60.0
    processing_s = config.operations.processing_min * 60.0
    accesses: list[Access] = []
    contacts: list[Contact] = []
    for satellite in config.satellites:
        r_ecef, v_ecef = propagate(satellite, config, times)
        sat_contacts = [
            c
            for station in config.ground_stations
            for c in find_contacts(satellite.name, times, r_ecef, station, config.operations.min_contact_s)
        ]
        contacts.extend(sat_contacts)
        for target in config.targets:
            for access in find_accesses(satellite.name, times, r_ecef, v_ecef, target, config.sensor):
                latency = delivery_latency_s(access.time_s, sat_contacts, downlink_s, processing_s)
                accesses.append(replace(access, latency_s=latency))
    accesses.sort(key=lambda a: a.time_s)
    contacts.sort(key=lambda c: c.start_s)
    return MissionAnalysis(
        config=config,
        satellites=tuple(s.name for s in config.satellites),
        accesses=tuple(accesses),
        contacts=tuple(contacts),
    )
