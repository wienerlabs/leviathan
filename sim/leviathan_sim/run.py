import argparse
import json
import math
import time
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
from torch.nn.utils import parameters_to_vector

from leviathan_sim.aggregators import CenteredClipAggregator, MeanAggregator
from leviathan_sim.attacks import InjectionConfig, Injector
from leviathan_sim.economy import (
    EconomyConfig,
    StakeLedger,
    audit_burn_projection,
    calibration_table,
    genesis_parameters,
)
from leviathan_sim.model import build_model, parameter_count
from leviathan_sim.sparse import chunked_topk_sign
from leviathan_sim.swarm import NesterovOuter, SwarmWorker, evaluate, load_corpus
from leviathan_sim.verifier import replay_and_verify

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
    sparse_density: float | None = None,
    sparse_chunk: int = 64,
    attack_band: float = 0.05,
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
        InjectionConfig(n_malicious=scenario.n_malicious, attack=scenario.attack, band=attack_band),
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
    density_samples: list[float] = []
    for round_index in range(rounds):
        active_workers = [w for w in workers if w.wid in ledger.active_ids]
        updates = {w.wid: w.local_round(theta, model, round_index) for w in active_workers}
        if sparse_density is not None:
            for wid, update in updates.items():
                compressed = chunked_topk_sign(update.delta, sparse_density, sparse_chunk, True)
                if round_index == 0:
                    density_samples.append(float((compressed != 0).float().mean()))
                updates[wid] = replace(update, delta=compressed)
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
        "mean_density": mean_of(density_samples) if density_samples else None,
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
    parser.add_argument("--sparse", action="store_true")
    parser.add_argument("--sparse-density", type=float, default=0.02)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--band-sweep", action="store_true")
    parser.add_argument("--drift", type=float, default=0.01)
    parser.add_argument("--band", type=float, default=0.05)
    args = parser.parse_args()
    rounds = 3 if args.smoke else args.rounds
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    base = Path(__file__).resolve().parent.parent
    corpus = load_corpus(base / "data" / "shakespeare.txt")
    probe = build_model(corpus.vocab_size, args.block_size, seed=7, device=device)
    print(f"device={device.type} vocab={corpus.vocab_size} params={parameter_count(probe):,}")
    if args.verify:
        run_verify_experiment(args, corpus, device, base)
        return
    if args.band_sweep:
        run_band_sweep(args, corpus, rounds, device, base, probe)
        return
    if args.sparse:
        run_sparse_comparison(args, corpus, rounds, device, base, probe)
        return
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
        "audit_burn_projection": audit_burn_projection([0.02, 0.05, 0.1, 0.2, 0.3]),
        "genesis_parameters": genesis_parameters(),
    }
    (out_dir / f"{prefix}results.json").write_text(json.dumps(payload, indent=2))
    plot_loss_curves(results, out_dir / f"{prefix}loss_curves.png")
    plot_security_economics(results, calibration, out_dir / f"{prefix}security_economics.png")
    print(f"wrote {out_dir / (prefix + 'results.json')}")


def run_verify_experiment(args, corpus, device, base):
    n_workers = 10
    model = build_model(corpus.vocab_size, args.block_size, seed=7, device=device)
    theta = parameters_to_vector(model.parameters()).detach().clone()
    workers = [
        SwarmWorker(
            wid, corpus, n_workers, True, args.inner_steps, 2e-3,
            args.batch_size, args.block_size, 100 + wid, device,
        )
        for wid in range(n_workers)
    ]
    tamper = {1: "sign_flip", 4: "gaussian", 7: "lazy"}
    generator = torch.Generator(device="cpu").manual_seed(4242)
    rows = []
    for worker in workers:
        honest = worker.local_round(theta, model, 0).delta
        if worker.wid in tamper:
            attack = tamper[worker.wid]
            if attack == "sign_flip":
                submitted = -5.0 * honest
            elif attack == "gaussian":
                submitted = (torch.randn(honest.shape, generator=generator) * float(honest.abs().mean().cpu())).to(honest.device)
            else:
                submitted = torch.zeros_like(honest)
            kind = attack
        else:
            drift = torch.randn(honest.shape, generator=generator).to(honest.device)
            drift = drift / torch.linalg.vector_norm(drift) * torch.linalg.vector_norm(honest) * args.drift
            submitted = honest + drift
            kind = "honest"
        verdict = replay_and_verify(worker, model, theta, 0, submitted, args.band)
        rows.append({"wid": worker.wid, "kind": kind, "distance": verdict.distance, "fraud": verdict.fraud})
        print(f"worker {worker.wid:2d} {kind:9s} distance={verdict.distance:.4f} fraud={verdict.fraud}")

    honest_rows = [r for r in rows if r["kind"] == "honest"]
    cheat_rows = [r for r in rows if r["kind"] != "honest"]
    honest_fp = sum(1 for r in honest_rows if r["fraud"])
    cheat_caught = sum(1 for r in cheat_rows if r["fraud"])
    print(
        f"band={args.band} drift={args.drift} honest_false_positives={honest_fp}/{len(honest_rows)} "
        f"cheaters_caught={cheat_caught}/{len(cheat_rows)}"
    )
    out_dir = base / "out"
    out_dir.mkdir(exist_ok=True)
    payload = {
        "config": {"band": args.band, "drift": args.drift, "workers": n_workers},
        "rows": rows,
        "honest_false_positives": honest_fp,
        "cheaters_caught": cheat_caught,
    }
    (out_dir / "verify_results.json").write_text(json.dumps(payload, indent=2))
    plot_verify(rows, args.band, args.drift, out_dir / "verify.png")
    print(f"wrote {out_dir / 'verify_results.json'}")


def plot_verify(rows, band, drift, out_path: Path):
    fig, ax = plt.subplots(figsize=(11, 4.6), facecolor=SURFACE)
    style_axes(ax)
    colors = {"honest": PALETTE[1], "sign_flip": PALETTE[5], "gaussian": PALETTE[7], "lazy": PALETTE[3]}
    ordered = sorted(rows, key=lambda r: r["wid"])
    positions = range(len(ordered))
    heights = [max(r["distance"], 1e-3) for r in ordered]
    bar_colors = [colors[r["kind"]] for r in ordered]
    ax.bar(list(positions), heights, color=bar_colors, width=0.7)
    ax.axhline(band, color=INK_SECONDARY, linewidth=1.2, linestyle="--")
    ax.annotate(f"tolerance band {band}", xy=(0.1, band * 1.15), color=INK_SECONDARY, fontsize=9)
    ax.set_yscale("log")
    ax.set_xticks(list(positions), [f"w{r['wid']}\n{r['kind']}" for r in ordered], color=INK_SECONDARY, fontsize=7)
    ax.set_ylabel("relative replay distance", color=INK_SECONDARY, fontsize=9)
    ax.set_title(
        f"Replay audit: honest drift ~{drift} passes, every attack lands above the band",
        color=INK, fontsize=12, loc="left", pad=10,
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=180, facecolor=SURFACE)
    plt.close(fig)


BAND_SWEEP = [0.02, 0.05, 0.1, 0.2]


def within_band_replay_evidence(args, corpus, device, band: float) -> dict:
    """One round of explicit replay: a within-band submission must pass the
    audit at exactly band_margin * band relative distance. This is the proof
    that layer 2 is blind to this adversary, not an assumption."""
    n_workers = args.workers
    model = build_model(corpus.vocab_size, args.block_size, seed=7, device=device)
    theta = parameters_to_vector(model.parameters()).detach().clone()
    workers = [
        SwarmWorker(
            wid, corpus, n_workers, True, args.inner_steps, 2e-3,
            args.batch_size, args.block_size, 100 + wid, device,
        )
        for wid in range(n_workers)
    ]
    updates = {w.wid: w.local_round(theta, model, 0) for w in workers}
    injector = Injector(
        InjectionConfig(n_malicious=5, attack="within_band", band=band),
        list(range(n_workers)),
        seed=11,
    )
    attacked, report = injector.apply(updates)
    target_wid = min(report.malicious_ids)
    verdict = replay_and_verify(
        workers[target_wid], model, theta, 0, attacked[target_wid].delta, band
    )
    return {"wid": target_wid, "distance": verdict.distance, "fraud": verdict.fraud}


def run_band_sweep(args, corpus, rounds, device, base, probe):
    honest = run_scenario(
        Scenario("withinband-honest", "Honest, clip", True, "none", 0, "clip", 0.0),
        corpus, rounds, args.workers, args.inner_steps,
        args.batch_size, args.block_size, device,
    )
    print(f"withinband-honest: final={honest['final_val_loss']:.3f}")
    rows = []
    for band in BAND_SWEEP:
        scenario = Scenario(
            f"withinband-{band}", f"Within-band 5/16, band {band}", True,
            "within_band", 5, "clip", 0.0,
        )
        result = run_scenario(
            scenario, corpus, rounds, args.workers, args.inner_steps,
            args.batch_size, args.block_size, device, attack_band=band,
        )
        evidence = within_band_replay_evidence(args, corpus, device, band)
        row = {
            "band": band,
            "final_val_loss": result["final_val_loss"],
            "damage_vs_honest": result["final_val_loss"] - honest["final_val_loss"],
            "malicious_selection_rate": result["malicious_selection_rate"],
            "replay_distance": evidence["distance"],
            "replay_fraud": evidence["fraud"],
            "val_losses": result["val_losses"],
        }
        rows.append(row)
        print(
            f"withinband band={band}: final={row['final_val_loss']:.3f} "
            f"damage={row['damage_vs_honest']:+.3f} "
            f"mal_sel={fmt(row['malicious_selection_rate'])} "
            f"replay_distance={row['replay_distance']:.4f} "
            f"replay_fraud={row['replay_fraud']}"
        )
    out_dir = base / "out"
    out_dir.mkdir(exist_ok=True)
    prefix = "smoke_band_" if args.smoke else "band_"
    payload = {
        "config": {
            "rounds": rounds, "workers": args.workers, "n_malicious": 5,
            "device": device.type, "model_parameters": parameter_count(probe),
            "bands": BAND_SWEEP,
        },
        "honest_reference": {
            "final_val_loss": honest["final_val_loss"],
            "val_losses": honest["val_losses"],
        },
        "sweep": rows,
    }
    (out_dir / f"{prefix}sweep_results.json").write_text(json.dumps(payload, indent=2))
    plot_band_sweep(rows, honest["final_val_loss"], out_dir / f"{prefix}sweep.png")
    print(f"wrote {out_dir / (prefix + 'sweep_results.json')}")


def plot_band_sweep(rows, honest_final, out_path: Path):
    fig, (left, right) = plt.subplots(1, 2, figsize=(12.5, 4.6), facecolor=SURFACE)
    bands = [r["band"] for r in rows]
    style_axes(left)
    left.plot(bands, [r["final_val_loss"] for r in rows], color=PALETTE[5],
              linewidth=2.0, marker="o", markersize=5, label="within-band 5/16, clip")
    left.axhline(honest_final, color=PALETTE[1], linewidth=1.6, linestyle="--",
                 label="honest reference")
    left.set_xlabel("published tolerance band", color=INK_SECONDARY, fontsize=9)
    left.set_ylabel("final validation loss", color=INK_SECONDARY, fontsize=9)
    left.set_title("Loss damage that fits inside the band", color=INK,
                   fontsize=11, loc="left", pad=10)
    left.legend(frameon=False, fontsize=8, labelcolor=INK_SECONDARY)
    style_axes(right)
    right.bar([str(b) for b in bands], [r["malicious_selection_rate"] or 0.0 for r in rows],
              color=PALETTE[7], width=0.6)
    right.set_ylim(0, 1.05)
    right.set_xlabel("published tolerance band", color=INK_SECONDARY, fontsize=9)
    right.set_ylabel("malicious selection rate", color=INK_SECONDARY, fontsize=9)
    right.set_title("Aggregation is the only layer that pushes back", color=INK,
                    fontsize=11, loc="left", pad=10)
    fig.suptitle(
        "The band is the adversary's budget: replay audits pass by construction",
        color=INK, fontsize=13, x=0.01, ha="left",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out_path, dpi=180, facecolor=SURFACE)
    plt.close(fig)


SPARSE_KEYS = [
    "honest-mean-iid",
    "signflip-clip-iid",
    "alie-clip-audit-iid",
    "honest-clip-noniid",
]


def run_sparse_comparison(args, corpus, rounds, device, base, probe):
    scenarios = {s.key: s for s in SCENARIOS}
    rows = []
    for key in SPARSE_KEYS:
        scenario = scenarios[key]
        dense = run_scenario(
            scenario, corpus, rounds, args.workers, args.inner_steps,
            args.batch_size, args.block_size, device,
        )
        sparse = run_scenario(
            scenario, corpus, rounds, args.workers, args.inner_steps,
            args.batch_size, args.block_size, device,
            sparse_density=args.sparse_density, sparse_chunk=64,
        )
        row = {
            "key": key,
            "label": scenario.label,
            "dense_final": dense["final_val_loss"],
            "sparse_final": sparse["final_val_loss"],
            "dense_mal_sel": dense["malicious_selection_rate"],
            "sparse_mal_sel": sparse["malicious_selection_rate"],
            "sparse_density": sparse["mean_density"],
        }
        rows.append(row)
        print(
            f"{key}: dense_final={row['dense_final']:.3f} sparse_final={row['sparse_final']:.3f} "
            f"dense_mal={fmt(row['dense_mal_sel'])} sparse_mal={fmt(row['sparse_mal_sel'])} "
            f"density={fmt(row['sparse_density'])}"
        )
    out_dir = base / "out"
    out_dir.mkdir(exist_ok=True)
    prefix = "smoke_sparse_" if args.smoke else "sparse_"
    payload = {
        "config": {
            "rounds": rounds, "workers": args.workers, "device": device.type,
            "target_density": args.sparse_density, "chunk": 64,
            "model_parameters": parameter_count(probe),
        },
        "comparison": rows,
    }
    (out_dir / f"{prefix}results.json").write_text(json.dumps(payload, indent=2))
    plot_sparse_comparison(rows, args.sparse_density, out_dir / f"{prefix}comparison.png")
    print(f"wrote {out_dir / (prefix + 'results.json')}")


def plot_sparse_comparison(rows, target_density, out_path: Path):
    fig, (left, right) = plt.subplots(1, 2, figsize=(12.5, 4.6), facecolor=SURFACE)
    labels = [r["label"] for r in rows]
    x = range(len(rows))
    width = 0.38
    style_axes(left)
    left.bar([i - width / 2 for i in x], [r["dense_final"] for r in rows], width,
             color=PALETTE[0], label="dense delta")
    left.bar([i + width / 2 for i in x], [r["sparse_final"] for r in rows], width,
             color=PALETTE[1], label=f"sparse {int(target_density * 100)}% + sign")
    left.set_xticks(list(x), labels, color=INK_SECONDARY, fontsize=8, rotation=20, ha="right")
    left.set_ylabel("final validation loss", color=INK_SECONDARY, fontsize=9)
    left.set_title("Same defense, compressed transport", color=INK, fontsize=11, loc="left", pad=10)
    left.legend(frameon=False, fontsize=8, labelcolor=INK_SECONDARY)
    style_axes(right)
    sel_rows = [r for r in rows if r["dense_mal_sel"] is not None]
    sx = range(len(sel_rows))
    right.bar([i - width / 2 for i in sx], [r["dense_mal_sel"] for r in sel_rows], width,
              color=PALETTE[5], label="dense")
    right.bar([i + width / 2 for i in sx], [r["sparse_mal_sel"] for r in sel_rows], width,
              color=PALETTE[7], label="sparse")
    right.set_xticks(list(sx), [r["label"] for r in sel_rows], color=INK_SECONDARY, fontsize=8, rotation=20, ha="right")
    right.set_ylim(0, 1.05)
    right.set_ylabel("malicious selection rate", color=INK_SECONDARY, fontsize=9)
    right.set_title("Coalition still rejected under compression", color=INK, fontsize=11, loc="left", pad=10)
    right.legend(frameon=False, fontsize=8, labelcolor=INK_SECONDARY)
    fig.suptitle(
        "Clip + excision holds in the SparseLoCo transport domain",
        color=INK, fontsize=13, x=0.01, ha="left",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out_path, dpi=180, facecolor=SURFACE)
    plt.close(fig)


def fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}"


if __name__ == "__main__":
    main()
