import argparse
import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
from torch.nn.utils import parameters_to_vector

from leviathan_sim.aggregators import CenteredClipAggregator, MeanAggregator
from leviathan_sim.attacks import InjectionConfig, Injector
from leviathan_sim.economy import EconomyConfig, StakeLedger, calibration_table
from leviathan_sim.model import build_model, parameter_count
from leviathan_sim.swarm import NesterovOuter, SwarmWorker, evaluate, load_corpus

LOSS_CEILING = 12.0

PALETTE = ["#2a78d6", "#1baf7a", "#eda100", "#008300", "#4a3aa7", "#e34948", "#e87ba4", "#eb6834"]
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SURFACE = "#fcfcfb"


@dataclass(frozen=True)
class Scenario:
    key: str
    label: str
    iid: bool
    attack: str
    n_malicious: int
    aggregator: str
    audit_probability: float


SCENARIOS = [
    Scenario("honest-mean-iid", "Honest swarm, mean", True, "none", 0, "mean", 0.0),
    Scenario("signflip-mean-iid", "Sign flip 5/16 vs mean", True, "sign_flip", 5, "mean", 0.0),
    Scenario("signflip-clip-iid", "Sign flip 5/16 vs clip", True, "sign_flip", 5, "clip", 0.0),
    Scenario("alie-clip-iid", "ALIE 5/16 vs clip", True, "alie", 5, "clip", 0.0),
    Scenario("alie-clip-audit-iid", "ALIE 5/16 vs clip + audit", True, "alie", 5, "clip", 0.1),
    Scenario("honest-mean-noniid", "Honest non-IID, mean", False, "none", 0, "mean", 0.0),
    Scenario("honest-clip-noniid", "Honest non-IID, clip", False, "none", 0, "clip", 0.0),
]

SCENARIO_COLORS = {scenario.key: PALETTE[i] for i, scenario in enumerate(SCENARIOS)}


def make_aggregator(kind: str):
    if kind == "mean":
        return MeanAggregator()
    return CenteredClipAggregator(iterations=3, excision_multiplier=3.0)


def clamp_loss(value: float) -> float:
    if math.isnan(value) or math.isinf(value):
        return LOSS_CEILING
    return min(value, LOSS_CEILING)


def run_scenario(
    scenario: Scenario,
    corpus,
    rounds: int,
    n_workers: int,
    inner_steps: int,
    batch_size: int,
    block_size: int,
    device: torch.device,
) -> dict:
    model = build_model(corpus.vocab_size, block_size, seed=7, device=device)
    theta = parameters_to_vector(model.parameters()).detach().clone()
    worker_ids = list(range(n_workers))
    workers = [
        SwarmWorker(
            wid,
            corpus,
            n_workers,
            scenario.iid,
            inner_steps,
            inner_lr=2e-3,
            batch_size=batch_size,
            block_size=block_size,
            seed=100 + wid,
            device=device,
        )
        for wid in worker_ids
    ]
    injector = Injector(
        InjectionConfig(n_malicious=scenario.n_malicious, attack=scenario.attack),
        worker_ids,
        seed=11,
    )
    aggregator = make_aggregator(scenario.aggregator)
    ledger = StakeLedger(
        worker_ids,
        EconomyConfig(audit_probability=scenario.audit_probability),
        seed=17,
    )
    outer = NesterovOuter(theta)
    val_losses: list[float] = []
    selected_counts = {wid: 0 for wid in worker_ids}
    seen_counts = {wid: 0 for wid in worker_ids}
    for round_index in range(rounds):
        active_workers = [w for w in workers if w.wid in ledger.active_ids]
        updates = {w.wid: w.local_round(theta, model, round_index) for w in active_workers}
        attacked, report = injector.apply(updates)
        deltas = {wid: u.delta for wid, u in attacked.items()}
        delta_agg, mask = aggregator.aggregate(deltas)
        ledger.settle_round(round_index, mask, report.malicious_ids)
        for wid, selected in mask.items():
            seen_counts[wid] += 1
            if selected:
                selected_counts[wid] += 1
        theta = outer.step(delta_agg)
        val_losses.append(
            clamp_loss(evaluate(model, corpus, theta, batch_size, block_size, device))
        )
    malicious = injector.malicious_ids
    honest = [wid for wid in worker_ids if wid not in malicious]
    honest_rate = selection_rate(selected_counts, seen_counts, honest)
    malicious_rate = selection_rate(selected_counts, seen_counts, list(malicious))
    pnl = ledger.pnl()
    return {
        "scenario": asdict(scenario),
        "val_losses": val_losses,
        "final_val_loss": val_losses[-1],
        "best_val_loss": min(val_losses),
        "honest_selection_rate": honest_rate,
        "malicious_selection_rate": malicious_rate,
        "honest_fpr": 1.0 - honest_rate if honest_rate is not None else None,
        "caught_rounds": dict(sorted(ledger.caught.items())),
        "honest_mean_pnl": mean_of([pnl[wid] for wid in honest]),
        "malicious_mean_pnl": mean_of([pnl[wid] for wid in malicious]),
        "clip_counts": getattr(aggregator, "clip_counts", {}),
    }


def selection_rate(selected: dict[int, int], seen: dict[int, int], wids: list[int]) -> float | None:
    total_seen = sum(seen[wid] for wid in wids)
    if total_seen == 0:
        return None
    return sum(selected[wid] for wid in wids) / total_seen


def mean_of(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def style_axes(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(True, axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def plot_loss_curves(results: dict[str, dict], out_path: Path):
    fig, (left, right) = plt.subplots(1, 2, figsize=(12.5, 4.6), facecolor=SURFACE)
    iid_keys = [
        "honest-mean-iid",
        "signflip-mean-iid",
        "signflip-clip-iid",
        "alie-clip-iid",
        "alie-clip-audit-iid",
    ]
    noniid_keys = ["honest-mean-noniid", "honest-clip-noniid"]
    for ax, keys, title in (
        (left, iid_keys, "IID swarm under attack"),
        (right, noniid_keys, "Honest non-IID swarm"),
    ):
        style_axes(ax)
        for key in keys:
            result = results[key]
            losses = result["val_losses"]
            ax.plot(
                range(1, len(losses) + 1),
                losses,
                color=SCENARIO_COLORS[key],
                linewidth=2.0,
                label=result["scenario"]["label"],
            )
        ax.set_title(title, color=INK, fontsize=11, loc="left", pad=10)
        ax.set_xlabel("outer round", color=INK_SECONDARY, fontsize=9)
        ax.set_ylabel("validation loss", color=INK_SECONDARY, fontsize=9)
        ax.legend(frameon=False, fontsize=8, labelcolor=INK_SECONDARY)
    left.annotate(
        "mean collapses",
        xy=(len(results["signflip-mean-iid"]["val_losses"]) * 0.55, LOSS_CEILING * 0.92),
        color=INK_SECONDARY,
        fontsize=8,
    )
    fig.suptitle(
        "Centered clip + excision on real transformer gradients",
        color=INK,
        fontsize=13,
        x=0.01,
        ha="left",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out_path, dpi=180, facecolor=SURFACE)
    plt.close(fig)


def plot_security_economics(results: dict[str, dict], calibration: list[dict], out_path: Path):
    fig, (left, right) = plt.subplots(1, 2, figsize=(12.5, 4.6), facecolor=SURFACE)
    style_axes(left)
    attack_keys = ["signflip-clip-iid", "alie-clip-iid", "honest-clip-noniid"]
    labels = ["Sign flip\nvs clip", "ALIE\nvs clip", "Honest\nnon-IID clip"]
    honest_rates = [results[k]["honest_selection_rate"] or 0.0 for k in attack_keys]
    malicious_rates = [results[k]["malicious_selection_rate"] or 0.0 for k in attack_keys]
    x = range(len(attack_keys))
    width = 0.38
    left.bar(
        [i - width / 2 for i in x],
        honest_rates,
        width,
        color=PALETTE[0],
        label="honest accepted",
    )
    left.bar(
        [i + width / 2 for i in x],
        malicious_rates,
        width,
        color=PALETTE[5],
        label="malicious accepted",
    )
    left.set_xticks(list(x), labels, color=INK_SECONDARY, fontsize=9)
    left.set_ylim(0, 1.05)
    left.set_ylabel("selection rate", color=INK_SECONDARY, fontsize=9)
    left.set_title("Who does the aggregator accept?", color=INK, fontsize=11, loc="left", pad=10)
    left.legend(frameon=False, fontsize=8, labelcolor=INK_SECONDARY)
    style_axes(right)
    presets = sorted({row["preset"] for row in calibration})
    ordered = [p for p in ["125M proof run", "1B genesis run", "7B scale run"] if p in presets]
    for i, preset in enumerate(ordered):
        rows = [row for row in calibration if row["preset"] == preset]
        rows.sort(key=lambda r: r["audit_probability"])
        right.plot(
            [row["audit_probability"] for row in rows],
            [row["break_even_bond_usd"] for row in rows],
            color=PALETTE[i],
            linewidth=2.0,
            marker="o",
            markersize=4,
            label=preset,
        )
    right.axvline(0.1, color=AXIS, linewidth=1.0)
    right.annotate("operating point p=0.1", xy=(0.105, right.get_ylim()[1] * 0.5), color=MUTED, fontsize=8)
    right.set_yscale("log")
    right.set_xlabel("audit probability per contribution", color=INK_SECONDARY, fontsize=9)
    right.set_ylabel("break-even bond, USD per worker", color=INK_SECONDARY, fontsize=9)
    right.set_title("Bond that makes cheating unprofitable", color=INK, fontsize=11, loc="left", pad=10)
    right.legend(frameon=False, fontsize=8, labelcolor=INK_SECONDARY)
    fig.suptitle(
        "Economic security calibrated to H100 market compute",
        color=INK,
        fontsize=13,
        x=0.01,
        ha="left",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out_path, dpi=180, facecolor=SURFACE)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=30)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--inner-steps", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--block-size", type=int, default=128)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    rounds = 3 if args.smoke else args.rounds
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    base = Path(__file__).resolve().parent.parent
    corpus = load_corpus(base / "data" / "shakespeare.txt")
    probe = build_model(corpus.vocab_size, args.block_size, seed=7, device=device)
    print(f"device={device.type} vocab={corpus.vocab_size} params={parameter_count(probe):,}")
    results: dict[str, dict] = {}
    for scenario in SCENARIOS:
        started = time.time()
        results[scenario.key] = run_scenario(
            scenario,
            corpus,
            rounds,
            args.workers,
            args.inner_steps,
            args.batch_size,
            args.block_size,
            device,
        )
        result = results[scenario.key]
        print(
            f"{scenario.key}: final={result['final_val_loss']:.3f} "
            f"best={result['best_val_loss']:.3f} "
            f"honest_sel={fmt(result['honest_selection_rate'])} "
            f"mal_sel={fmt(result['malicious_selection_rate'])} "
            f"caught={list(result['caught_rounds'].values())} "
            f"({time.time() - started:.0f}s)"
        )
    calibration = calibration_table([0.02, 0.05, 0.1, 0.2, 0.3])
    out_dir = base / "out"
    out_dir.mkdir(exist_ok=True)
    prefix = "smoke_" if args.smoke else ""
    payload = {
        "config": {
            "rounds": rounds,
            "workers": args.workers,
            "inner_steps": args.inner_steps,
            "batch_size": args.batch_size,
            "block_size": args.block_size,
            "device": device.type,
            "model_parameters": parameter_count(probe),
        },
        "scenarios": results,
        "economy_calibration": calibration,
    }
    (out_dir / f"{prefix}results.json").write_text(json.dumps(payload, indent=2))
    plot_loss_curves(results, out_dir / f"{prefix}loss_curves.png")
    plot_security_economics(results, calibration, out_dir / f"{prefix}security_economics.png")
    print(f"wrote {out_dir / (prefix + 'results.json')}")


def fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}"


if __name__ == "__main__":
    main()
