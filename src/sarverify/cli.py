import argparse
import sys
from pathlib import Path

from .analysis import run_analysis
from .compare import build_decision_memo, evaluate_option, recommend
from .config import ConfigError, load_config
from .degradation import single_satellite_loss
from .robustness import phasing_monte_carlo
from .report import build_json, build_markdown, build_traceability_csv, fmt
from .trade import altitude_sweep, satellites_per_plane_sweep, smallest_compliant
from .verify import Status, overall_status, summarize, verify


def _gate(status: Status, fail_on: str) -> int:
    if status is Status.FAIL:
        return 1
    if status is Status.MARGINAL and fail_on == "marginal":
        return 1
    return 0


def cmd_run(args) -> int:
    config = load_config(args.config)
    analysis = run_analysis(config)
    summaries = summarize(verify(analysis, config.requirements, config.marginal_band))
    loss = None if args.skip_loss else single_satellite_loss(analysis, config.requirements, config.marginal_band)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "verification_report.md").write_text(build_markdown(analysis, summaries, loss), encoding="utf-8")
    (out / "verification_results.json").write_text(build_json(analysis, summaries, loss), encoding="utf-8")
    (out / "traceability_matrix.csv").write_text(build_traceability_csv(summaries), encoding="utf-8")
    if not args.no_plots:
        from .plots import plot_access_timeline, plot_coverage_map, plot_revisit_distribution

        revisit_req = next((r for r in config.requirements if r.metric == "max_revisit_h"), None)
        plot_access_timeline(analysis, out / "access_timeline.png")
        plot_coverage_map(analysis, out / "coverage_map.png")
        plot_revisit_distribution(analysis, out / "revisit_gaps.png", revisit_req.threshold if revisit_req else None)
    status = overall_status(summaries)
    width = max(len(s.requirement.id) for s in summaries)
    print(f"{config.name}: {len(analysis.satellites)} satellites, {len(analysis.accesses)} opportunities, {len(analysis.contacts)} contacts")
    for s in summaries:
        print(f"  {s.requirement.id:<{width}}  {s.status.value:<8}  worst {fmt(s.worst.measured)} {s.requirement.unit} at {s.worst.scope}")
    if loss is not None:
        fragile = [c.lost_satellite for c in loss if c.status is Status.FAIL]
        print(f"  Single-satellite loss: {len(fragile)}/{len(loss)} cases break at least one requirement")
    print(f"Acceptance status: {status.value}  (report written to {out})")
    return _gate(status, args.fail_on)


def cmd_trade(args) -> int:
    config = load_config(args.config)
    ids = [r.id for r in config.requirements]
    if args.altitudes:
        points = altitude_sweep(config, args.altitudes)
        lines = ["| Altitude (km) | Status | " + " | ".join(ids) + " |", "|" + "---|" * (len(ids) + 2)]
        for p in points:
            cells = [f"{fmt(s.worst.measured)} ({s.status.value})" for s in p.summaries]
            lines.append(f"| {p.altitude_km:g} | {p.status.value} | " + " | ".join(cells) + " |")
        compliant = [p.altitude_km for p in points if p.status is not Status.FAIL]
        verdict = (
            f"Compliant altitudes: {', '.join(f'{a:g}' for a in compliant)} km"
            if compliant
            else "No swept altitude meets all requirements"
        )
    else:
        points = satellites_per_plane_sweep(config, args.counts)
        lines = ["| Sats/plane | Total | Status | " + " | ".join(ids) + " |", "|" + "---|" * (len(ids) + 3)]
        for p in points:
            cells = [f"{fmt(s.worst.measured)} ({s.status.value})" for s in p.summaries]
            lines.append(f"| {p.satellites_per_plane} | {p.total_satellites} | {p.status.value} | " + " | ".join(cells) + " |")
        best = smallest_compliant(points)
        verdict = (
            f"Smallest compliant constellation: {best.satellites_per_plane} per plane ({best.total_satellites} satellites)"
            if best
            else "No swept configuration meets all requirements"
        )
    table = "\n".join(lines)
    print(table)
    print(verdict)
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "trade_study.md").write_text(f"# Trade study: {config.name}\n\n{table}\n\n{verdict}\n", encoding="utf-8")
    return 0


def cmd_compare(args) -> int:
    labels = [chr(ord("A") + i) for i in range(len(args.configs))]
    options = [evaluate_option(label, load_config(path)) for label, path in zip(labels, args.configs)]
    memo = build_decision_memo(options)
    for o in options:
        print(f"Option {o.label}: {o.config.name}: {o.status.value}, {o.count(Status.FAIL)} FAIL, {o.count(Status.MARGINAL)} MARGINAL")
    best = recommend(options)
    print(f"Recommended: option {best.label} ({best.config.name})")
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "decision_memo.md").write_text(memo, encoding="utf-8")
    return 0


def cmd_robustness(args) -> int:
    config = load_config(args.config)
    result = phasing_monte_carlo(config, args.samples, args.phase_sigma, args.raan_sigma, args.seed)
    lines = [
        f"# Phasing robustness: {config.name}",
        "",
        f"{result.samples} samples, in-plane phase error sigma {result.phase_sigma_deg:g} deg, RAAN error sigma {result.raan_sigma_deg:g} deg.",
        "",
        "| Requirement | Criterion | P(compliant) | P10 | P50 | P90 |",
        "|---|---|---|---|---|---|",
    ]
    for s in result.spreads:
        lines.append(f"| {s.requirement_id} | {s.statement} | {s.compliance_probability * 100:.0f}% | {fmt(s.p10)} | {fmt(s.p50)} | {fmt(s.p90)} |")
    lines += ["", f"Probability that every requirement is met: {result.all_compliant_probability * 100:.0f}%", ""]
    text = "\n".join(lines)
    print(text)
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "robustness.md").write_text(text, encoding="utf-8")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sarverify", description="Verify SAR mission requirements against a constellation design.")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Analyse a mission and write a verification report")
    run.add_argument("config", help="Mission configuration (YAML or JSON)")
    run.add_argument("--out", default="reports", help="Output directory")
    run.add_argument("--no-plots", action="store_true", help="Skip PNG figures")
    run.add_argument("--skip-loss", action="store_true", help="Skip single-satellite loss analysis")
    run.add_argument("--fail-on", choices=["fail", "marginal"], default="fail", help="Exit non-zero at this status")
    run.set_defaults(func=cmd_run)
    trade = sub.add_parser("trade", help="Sweep satellites per plane and compare compliance")
    trade.add_argument("config")
    trade.add_argument("--counts", type=int, nargs="+", default=[1, 2, 3, 4])
    trade.add_argument("--altitudes", type=float, nargs="+", default=None, help="Sweep orbit altitude (km) instead of satellites per plane")
    trade.add_argument("--out", default=None)
    trade.set_defaults(func=cmd_trade)
    compare = sub.add_parser("compare", help="Compare design options and write a decision memo")
    compare.add_argument("configs", nargs="+", help="Two or more mission configurations")
    compare.add_argument("--out", default=None)
    compare.set_defaults(func=cmd_compare)
    robust = sub.add_parser("robustness", help="Monte Carlo over satellite phasing and plane errors")
    robust.add_argument("config")
    robust.add_argument("--samples", type=int, default=50)
    robust.add_argument("--phase-sigma", type=float, default=10.0, help="In-plane phasing error, 1 sigma (deg)")
    robust.add_argument("--raan-sigma", type=float, default=0.5, help="Plane RAAN error, 1 sigma (deg)")
    robust.add_argument("--seed", type=int, default=0)
    robust.add_argument("--out", default=None)
    robust.set_defaults(func=cmd_robustness)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
