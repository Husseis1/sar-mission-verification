from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .metrics import revisit_gaps_h


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
