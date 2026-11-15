from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import numpy as np

from .geodesy import ecef_to_geodetic
from .metrics import daily_access_rate, revisit_gaps_h


def plot_access_timeline(analysis, path: Path) -> Path:
    cfg = analysis.config
    fig, ax = plt.subplots(figsize=(11, 0.6 * len(cfg.targets) + 1.8))
    colors = plt.get_cmap("tab10")
    for s_idx, sat in enumerate(analysis.satellites):
        xs, ys = [], []
        for t_idx, target in enumerate(cfg.targets):
            for a in analysis.accesses:
                if a.satellite == sat and a.target == target.name:
                    xs.append(a.time_s / 86400.0)
                    ys.append(t_idx)
        ax.scatter(xs, ys, s=28, marker="|", linewidths=2, color=colors(s_idx % 10), label=sat)
    ax.set_yticks(range(len(cfg.targets)), [t.name for t in cfg.targets])
    ax.set_xlabel(f"Days since {cfg.epoch:%Y-%m-%d %H:%M} UTC")
    ax.set_title("Imaging opportunities per area of interest")
    ax.set_xlim(0, cfg.duration_days)
    ax.grid(axis="x", alpha=0.3)
    ax.legend(ncol=min(len(analysis.satellites), 6), fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.2), frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_revisit_distribution(analysis, path: Path, threshold_h: float | None = None) -> Path:
    cfg = analysis.config
    fig, ax = plt.subplots(figsize=(8, 4.5))
    data = [revisit_gaps_h(analysis, t.name) for t in cfg.targets]
    ax.boxplot(data, vert=False, tick_labels=[t.name for t in cfg.targets], whis=(0, 100))
    if threshold_h is not None:
        ax.axvline(threshold_h, color="#c0392b", linestyle="--", label=f"Requirement {threshold_h:g} h")
        ax.legend(loc="lower right")
    ax.set_xlabel("Revisit gap (h)")
    ax.set_title("Revisit gap distribution")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_coverage_map(analysis, path: Path, hours: float = 24.0, margin_deg: float = 5.0) -> Path:
    from .analysis import propagate

    cfg = analysis.config
    lats = [t.lat_deg for t in cfg.targets]
    lons = [t.lon_deg for t in cfg.targets]
    lat_lo, lat_hi = min(lats) - margin_deg, max(lats) + margin_deg
    lon_lo, lon_hi = min(lons) - 3 * margin_deg, max(lons) + 3 * margin_deg
    times = np.arange(0.0, hours * 3600.0, 20.0)
    fig, ax = plt.subplots(figsize=(11, 6.5))
    colors = plt.get_cmap("tab10")
    for idx, sat in enumerate(cfg.satellites):
        if sat.name not in analysis.satellites:
            continue
        r_ecef, _ = propagate(sat, cfg, times)
        lat, lon, _ = ecef_to_geodetic(r_ecef)
        inside = (lat > lat_lo) & (lat < lat_hi) & (lon > lon_lo) & (lon < lon_hi)
        lat = np.where(inside, lat, np.nan)
        lon = np.where(inside, lon, np.nan)
        jumps = np.abs(np.diff(lon, prepend=lon[0])) > 10
        lon[jumps] = np.nan
        ax.plot(lon, lat, lw=0.8, alpha=0.7, color=colors(idx % 10), label=sat.name)
    legend_lines = []
    for idx, target in enumerate(cfg.targets, start=1):
        rate = daily_access_rate(analysis, target.name)
        ax.scatter(target.lon_deg, target.lat_deg, s=140, marker="o", color="white", edgecolors="black", zorder=3)
        ax.annotate(str(idx), (target.lon_deg, target.lat_deg), ha="center", va="center", fontsize=8, fontweight="bold", zorder=4)
        legend_lines.append(f"{idx}  {target.name}: {rate:.1f}/day")
    ax.text(
        1.02,
        0.02,
        "\n".join(legend_lines),
        transform=ax.transAxes,
        fontsize=8,
        va="bottom",
        family="monospace",
    )
    for station in cfg.ground_stations:
        if lat_lo < station.lat_deg < lat_hi and lon_lo < station.lon_deg < lon_hi:
            ax.scatter(station.lon_deg, station.lat_deg, marker="^", s=90, color="#c0392b", zorder=3)
            ax.annotate(station.name, (station.lon_deg, station.lat_deg), xytext=(6, -12), textcoords="offset points", fontsize=8, color="#c0392b")
    ax.set_xlim(lon_lo, lon_hi)
    ax.set_ylim(lat_lo, lat_hi)
    ax.set_aspect(1.0 / np.cos(np.radians(np.mean(lats))), adjustable="box")
    ax.set_xlabel("Longitude (deg)")
    ax.set_ylabel("Latitude (deg)")
    ax.set_title(f"Ground tracks over {hours:g} h and imaging opportunities per area")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
