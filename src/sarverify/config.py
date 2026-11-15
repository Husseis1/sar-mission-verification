from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

import numpy as np
import yaml

from .geodesy import ensure_utc, geodetic_to_ecef, local_up
from .orbit import Satellite, sso_inclination_deg
from .requirements import Requirement, parse_requirement

LOOK_SIDES = ("left", "right")


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Target:
    name: str
    lat_deg: float
    lon_deg: float
    alt_km: float = 0.0

    @property
    def ecef(self) -> np.ndarray:
        return geodetic_to_ecef(self.lat_deg, self.lon_deg, self.alt_km)

    @property
    def up(self) -> np.ndarray:
        return local_up(self.lat_deg, self.lon_deg)


@dataclass(frozen=True)
class GroundStation:
    name: str
    lat_deg: float
    lon_deg: float
    alt_km: float = 0.0
    min_elevation_deg: float = 5.0

    @property
    def ecef(self) -> np.ndarray:
        return geodetic_to_ecef(self.lat_deg, self.lon_deg, self.alt_km)

    @property
    def up(self) -> np.ndarray:
        return local_up(self.lat_deg, self.lon_deg)


@dataclass(frozen=True)
class Sensor:
    incidence_min_deg: float
    incidence_max_deg: float
    look_sides: tuple[str, ...] = LOOK_SIDES


@dataclass(frozen=True)
class Operations:
    downlink_duration_min: float = 5.0
    processing_min: float = 15.0
    min_contact_s: float = 60.0


@dataclass(frozen=True)
class PlaneSpec:
    name: str
    altitude_km: float
    inclination_deg: float
    raan_deg: float
    satellites: int
    phase_offset_deg: float = 0.0

    def build(self) -> tuple[Satellite, ...]:
        return tuple(
            Satellite(
                name=f"{self.name}-{k + 1}",
                altitude_km=self.altitude_km,
                inclination_deg=self.inclination_deg,
                raan_deg=self.raan_deg,
                arg_lat_deg=(self.phase_offset_deg + 360.0 * k / self.satellites) % 360.0,
            )
            for k in range(self.satellites)
        )


@dataclass(frozen=True)
class MissionConfig:
    name: str
    customer: str
    epoch: datetime
    duration_days: float
    step_s: float
    planes: tuple[PlaneSpec, ...]
    sensor: Sensor
    targets: tuple[Target, ...]
    ground_stations: tuple[GroundStation, ...]
    operations: Operations
    requirements: tuple[Requirement, ...]
    marginal_band: float = 0.1

    @property
    def satellites(self) -> tuple[Satellite, ...]:
        return tuple(sat for plane in self.planes for sat in plane.build())

    @property
    def duration_s(self) -> float:
        return self.duration_days * 86400.0

    def with_satellites_per_plane(self, count: int) -> "MissionConfig":
        return replace(self, planes=tuple(replace(p, satellites=count) for p in self.planes))


def _get(raw: dict, key: str, where: str):
    if key not in raw:
        raise ConfigError(f"Missing '{key}' in {where}")
    return raw[key]


def _parse_epoch(value) -> datetime:
    if isinstance(value, datetime):
        return ensure_utc(value)
    try:
        return ensure_utc(datetime.fromisoformat(str(value).replace("Z", "+00:00")))
    except ValueError as exc:
        raise ConfigError(f"Invalid epoch '{value}'") from exc


def _parse_plane(raw: dict, index: int) -> PlaneSpec:
    where = f"constellation.planes[{index}]"
    altitude = float(_get(raw, "altitude_km", where))
    inclination = raw.get("inclination_deg", "sso")
    inclination = sso_inclination_deg(altitude) if inclination == "sso" else float(inclination)
    count = int(_get(raw, "satellites", where))
    if count < 1:
        raise ConfigError(f"{where}: satellites must be at least 1")
    return PlaneSpec(
        name=str(raw.get("name", f"P{index + 1}")),
        altitude_km=altitude,
        inclination_deg=inclination,
        raan_deg=float(raw.get("raan_deg", 0.0)),
        satellites=count,
        phase_offset_deg=float(raw.get("phase_offset_deg", 0.0)),
    )


def _parse_sensor(raw: dict) -> Sensor:
    sides = tuple(str(s).lower() for s in raw.get("look_sides", LOOK_SIDES))
    bad = [s for s in sides if s not in LOOK_SIDES]
    if bad:
        raise ConfigError(f"sensor.look_sides contains invalid values: {bad}")
    lo = float(_get(raw, "incidence_min_deg", "sensor"))
    hi = float(_get(raw, "incidence_max_deg", "sensor"))
    if not 0.0 <= lo < hi < 90.0:
        raise ConfigError("sensor incidence range must satisfy 0 <= min < max < 90")
    return Sensor(lo, hi, sides)


def parse_config(raw: dict) -> MissionConfig:
    mission = _get(raw, "mission", "config")
    planes = _get(_get(raw, "constellation", "config"), "planes", "constellation")
    targets = tuple(
        Target(str(t["name"]), float(t["lat_deg"]), float(t["lon_deg"]), float(t.get("alt_km", 0.0)))
        for t in _get(raw, "targets", "config")
    )
    stations = tuple(
        GroundStation(
            str(g["name"]),
            float(g["lat_deg"]),
            float(g["lon_deg"]),
            float(g.get("alt_km", 0.0)),
            float(g.get("min_elevation_deg", 5.0)),
        )
        for g in _get(raw, "ground_stations", "config")
    )
    ops_raw = raw.get("operations", {})
    operations = Operations(
        downlink_duration_min=float(ops_raw.get("downlink_duration_min", 5.0)),
        processing_min=float(ops_raw.get("processing_min", 15.0)),
        min_contact_s=float(ops_raw.get("min_contact_s", 60.0)),
    )
    try:
        requirements = tuple(parse_requirement(r) for r in _get(raw, "requirements", "config"))
    except ValueError as exc:
        raise ConfigError(str(exc)) from exc
    ids = [r.id for r in requirements]
    if len(ids) != len(set(ids)):
        raise ConfigError("Requirement ids must be unique")
    if not targets:
        raise ConfigError("At least one target is required")
    config = MissionConfig(
        name=str(_get(mission, "name", "mission")),
        customer=str(mission.get("customer", "")),
        epoch=_parse_epoch(_get(mission, "epoch", "mission")),
        duration_days=float(mission.get("duration_days", 7.0)),
        step_s=float(mission.get("step_s", 10.0)),
        planes=tuple(_parse_plane(p, i) for i, p in enumerate(planes)),
        sensor=_parse_sensor(_get(raw, "sensor", "config")),
        targets=targets,
        ground_stations=stations,
        operations=operations,
        requirements=requirements,
        marginal_band=float(raw.get("verification", {}).get("marginal_band", 0.1)),
    )
    if config.step_s <= 0 or config.duration_days <= 0:
        raise ConfigError("duration_days and step_s must be positive")
    return config


def load_config(path: str | Path) -> MissionConfig:
    text = Path(path).read_text(encoding="utf-8")
    raw = yaml.safe_load(text)
    if not isinstance(raw, dict):
        raise ConfigError(f"{path} does not contain a mission configuration")
    return parse_config(raw)
