from datetime import datetime, timezone

import numpy as np

from .constants import OMEGA_EARTH, R_EARTH, WGS84_E2

J2000 = datetime(2000, 1, 1, 12, tzinfo=timezone.utc)


def ensure_utc(epoch: datetime) -> datetime:
    if epoch.tzinfo is None:
        return epoch.replace(tzinfo=timezone.utc)
    return epoch.astimezone(timezone.utc)


def julian_date(epoch: datetime) -> float:
    return 2451545.0 + (ensure_utc(epoch) - J2000).total_seconds() / 86400.0


def gmst_rad(epoch: datetime, t_s: np.ndarray) -> np.ndarray:
    jd = julian_date(epoch)
    theta0 = np.radians((280.46061837 + 360.98564736629 * (jd - 2451545.0)) % 360.0)
    return theta0 + OMEGA_EARTH * np.asarray(t_s, dtype=float)


def eci_to_ecef(r_eci: np.ndarray, theta: np.ndarray) -> np.ndarray:
    c, s = np.cos(theta), np.sin(theta)
    x = c * r_eci[:, 0] + s * r_eci[:, 1]
    y = -s * r_eci[:, 0] + c * r_eci[:, 1]
    return np.column_stack([x, y, r_eci[:, 2]])


def geodetic_to_ecef(lat_deg: float, lon_deg: float, alt_km: float = 0.0) -> np.ndarray:
    lat, lon = np.radians(lat_deg), np.radians(lon_deg)
    n = R_EARTH / np.sqrt(1.0 - WGS84_E2 * np.sin(lat) ** 2)
    return np.array(
        [
            (n + alt_km) * np.cos(lat) * np.cos(lon),
            (n + alt_km) * np.cos(lat) * np.sin(lon),
            (n * (1.0 - WGS84_E2) + alt_km) * np.sin(lat),
        ]
    )


def local_up(lat_deg: float, lon_deg: float) -> np.ndarray:
    lat, lon = np.radians(lat_deg), np.radians(lon_deg)
    return np.array([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)])


def elevation_deg(r_ecef: np.ndarray, site_ecef: np.ndarray, site_up: np.ndarray) -> np.ndarray:
    los = r_ecef - site_ecef
    rng = np.linalg.norm(los, axis=1)
    return np.degrees(np.arcsin(np.clip(los @ site_up / rng, -1.0, 1.0)))


def ecef_to_geodetic(r_ecef: np.ndarray, iterations: int = 5) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    r = np.atleast_2d(r_ecef)
    x, y, z = r[:, 0], r[:, 1], r[:, 2]
    lon = np.arctan2(y, x)
    p = np.hypot(x, y)
    lat = np.arctan2(z, p * (1.0 - WGS84_E2))
    for _ in range(iterations):
        n = R_EARTH / np.sqrt(1.0 - WGS84_E2 * np.sin(lat) ** 2)
        alt = p / np.cos(lat) - n
        lat = np.arctan2(z, p * (1.0 - WGS84_E2 * n / (n + alt)))
    n = R_EARTH / np.sqrt(1.0 - WGS84_E2 * np.sin(lat) ** 2)
    alt = p / np.cos(lat) - n
    return np.degrees(lat), np.degrees(lon), alt
