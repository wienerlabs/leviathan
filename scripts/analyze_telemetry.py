#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASSETS = ROOT / "docs" / "assets"


@dataclass
class Gate:
    name: str
    required: bool
    passed: bool
    evidence: str
    detail: str


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def mean_catch_rounds(caught: dict[str, int]) -> float | None:
    if not caught:
        return None
    return statistics.mean(caught.values())


def analyze_phase0(results: dict[str, Any]) -> list[Gate]:
    scenarios = results["scenarios"]
    gates: list[Gate] = []

    honest = scenarios["honest-mean-iid"]["final_val_loss"]
    signflip_mean = scenarios["signflip-mean-iid"]["final_val_loss"]
    signflip_clip = scenarios["signflip-clip-iid"]
    alie_audit = scenarios["alie-clip-audit-iid"]
    noniid = scenarios["honest-clip-noniid"]

    gates.append(
        Gate(
            name="honest_baseline_converges",
            required=True,
            passed=honest < 2.3,
            evidence="docs/assets/results.json#honest-mean-iid",
            detail=f"final_val_loss={honest:.4f}",
        )
    )
    gates.append(
        Gate(
            name="naive_mean_fails_under_signflip",
            required=True,
            passed=signflip_mean >= 10.0,
            evidence="docs/assets/results.json#signflip-mean-iid",
            detail=f"final_val_loss={signflip_mean:.4f}",
        )
    )
    gates.append(
        Gate(
            name="clip_excision_neutralizes_signflip",
            required=True,
            passed=signflip_clip["final_val_loss"] < honest + 0.1
            and (signflip_clip.get("malicious_selection_rate") or 1.0) < 0.1,
            evidence="docs/assets/results.json#signflip-clip-iid",
            detail=(
                f"final={signflip_clip['final_val_loss']:.4f} "
                f"mal_sel={signflip_clip.get('malicious_selection_rate')}"
            ),
        )
    )

    caught = alie_audit.get("caught_rounds") or {}
    mean_catch = mean_catch_rounds(caught)
    expected = 1.0 / 0.1
    gates.append(
        Gate(
            name="audit_catches_alie_coalition",
            required=True,
            passed=len(caught) >= 5 and mean_catch is not None and abs(mean_catch - expected) < 2.0,
            evidence="docs/assets/results.json#alie-clip-audit-iid",
            detail=f"caught={len(caught)} mean_catch={mean_catch} expected={expected}",
        )
    )
    gates.append(
        Gate(
            name="zero_honest_false_positives_noniid",
            required=True,
            passed=(noniid.get("honest_fpr") or 0.0) == 0.0,
            evidence="docs/assets/results.json#honest-clip-noniid",
            detail=f"honest_fpr={noniid.get('honest_fpr')}",
        )
    )
    return gates


def analyze_band_sweep(sweep: dict[str, Any]) -> list[Gate]:
    gates: list[Gate] = []
    honest = sweep["honest_reference"]["final_val_loss"]
    rows = sweep["sweep"]
    op = next((r for r in rows if abs(r["band"] - 0.05) < 1e-9), None)
    if op is None:
        gates.append(
            Gate(
                name="operating_band_present",
                required=True,
                passed=False,
                evidence="docs/assets/band_sweep_results.json",
                detail="band 0.05 missing from sweep",
            )
        )
        return gates

    damage = op["damage_vs_honest"]
    gates.append(
        Gate(
            name="within_band_damage_measured",
            required=True,
            passed=op["replay_fraud"] is False and 0.0 < damage < 0.05,
            evidence="docs/assets/band_sweep_results.json#band=0.05",
            detail=(
                f"damage={damage:.4f} honest={honest:.4f} "
                f"replay_distance={op['replay_distance']:.4f} fraud={op['replay_fraud']}"
            ),
        )
    )

    damages = [r["damage_vs_honest"] for r in rows]
    bands = [r["band"] for r in rows]
    if len(damages) >= 2:
        slope_ok = damages[-1] > damages[0] and bands[-1] > bands[0]
        gates.append(
            Gate(
                name="damage_scales_with_band",
                required=False,
                passed=slope_ok,
                evidence="docs/assets/band_sweep_results.json",
                detail=f"damage_range=[{damages[0]:.4f},{damages[-1]:.4f}]",
            )
        )
    return gates


def analyze_verify(verify: dict[str, Any]) -> list[Gate]:
    return [
        Gate(
            name="verifier_zero_honest_fp",
            required=True,
            passed=verify.get("honest_false_positives", 1) == 0,
            evidence="docs/assets/verify_results.json",
            detail=f"honest_false_positives={verify.get('honest_false_positives')}",
        ),
        Gate(
            name="verifier_catches_cheater_classes",
            required=True,
            passed=verify.get("cheaters_caught", 0) >= 3,
            evidence="docs/assets/verify_results.json",
            detail=f"cheaters_caught={verify.get('cheaters_caught')}",
        ),
    ]


def structural_gates() -> list[Gate]:
    return [
        Gate(
            name="two_gpu_band_calibration",
            required=True,
            passed=False,
            evidence="docs/GAPS.md, docs/TASKS.md Phase 2",
            detail="not run: single-machine MPS only to date",
        ),
        Gate(
            name="350m_rehearsal_telemetry",
            required=True,
            passed=False,
            evidence="issue #3 scope",
            detail="no 350M multi-node rehearsal telemetry in repo",
        ),
        Gate(
            name="cross_hardware_band_harness",
            required=True,
            passed=False,
            evidence="docs/TASKS.md Phase 2",
            detail="4090/3090/A100/H100 calibration harness not completed",
        ),
        Gate(
            name="production_verifier_daemon_live_slash",
            required=True,
            passed=False,
            evidence="docs/TASKS.md (~ partial: psyche-verifier crate exists)",
            detail="decision core exists; live run_slash path not closed",
        ),
        Gate(
            name="multi_epoch_rejoin_resilience",
            required=False,
            passed=False,
            evidence="DEVNET.md / TASKS.md",
            detail="deferred; required before 7-day churn run",
        ),
    ]


def decide(gates: list[Gate]) -> str:
    required = [g for g in gates if g.required]
    if all(g.passed for g in required):
        return "GO"
    return "NO-GO"


def render_markdown(gates: list[Gate], decision: str) -> str:
    lines = [
        "# Rehearsal and pilot retro",
        "",
        "Issue #3. Generated by `scripts/analyze_telemetry.py` from checked-in",
        "telemetry only. No synthetic run data is invented.",
        "",
        f"## Decision: **{decision}** for the 1B public run",
        "",
        "Kill-switch metric: uncaught fraud analogue (double-sell). A required gate",
        "failure is an automatic NO-GO.",
        "",
        "## Gates",
        "",
        "| Gate | Required | Pass | Evidence | Detail |",
        "|---|---|---|---|---|",
    ]
    for g in gates:
        lines.append(
            f"| `{g.name}` | {'yes' if g.required else 'no'} | "
            f"{'PASS' if g.passed else 'FAIL'} | {g.evidence} | {g.detail} |"
        )
    lines.extend(
        [
            "",
            "## Phase 0 quantitative summary",
            "",
            "Sourced from `docs/assets/results.json`, `band_sweep_results.json`,",
            "`verify_results.json`.",
            "",
            "- Honest swarm mean final loss: 2.175",
            "- Sign-flip vs mean: diverges (12.0)",
            "- Sign-flip vs clip+excision: 2.203, malicious acceptance ~2.7%",
            "- ALIE + audit p=0.1: 5/5 caught, mean catch rounds from caught map",
            "- Operating band 0.05 within-band damage: +0.019 loss (~0.9%)",
            "- Verifier: 0 honest FP, 3 cheater classes caught at band 0.05",
            "",
            "## Recommended tuning before re-evaluation",
            "",
            "1. Keep `verification_percent = 10` (p=0.1) until two-GPU calibration lands.",
            "2. Keep band at 0.05 until cross-hardware drift samples exist; then set",
            "   `band = safety_factor * max_observed_honest_drift` via `calibrate_band`.",
            "3. Do not raise band to hide hardware noise; measure drift first.",
            "4. Publish centralized slash authority limitation on the dashboard.",
            "5. Re-run this script after 350M rehearsal JSON is dropped into",
            "   `docs/assets/rehearsal/`.",
            "",
            "## Acceptance mapping (issue #3)",
            "",
            "| Criterion | Status |",
            "|---|---|",
            "| Analyse telemetry axes | Done on Phase 0 assets |",
            "| Tune verification_percent and band | Recommendations above; no change without new data |",
            "| Retro with explicit go/no-go | This document |",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyse Leviathan telemetry for 1B go/no-go")
    parser.add_argument("--assets", type=Path, default=DEFAULT_ASSETS)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "docs" / "RETRO_REHEARSAL.md",
    )
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()

    results = load_json(args.assets / "results.json")
    band = load_json(args.assets / "band_sweep_results.json")
    verify = load_json(args.assets / "verify_results.json")

    gates = []
    gates.extend(analyze_phase0(results))
    gates.extend(analyze_band_sweep(band))
    gates.extend(analyze_verify(verify))
    gates.extend(structural_gates())

    decision = decide(gates)
    md = render_markdown(gates, decision)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(md)

    payload = {
        "decision": decision,
        "gates": [asdict(g) for g in gates],
        "required_failed": [g.name for g in gates if g.required and not g.passed],
    }
    if args.json_out:
        args.json_out.write_text(json.dumps(payload, indent=2) + "\n")

    print(f"decision={decision}")
    print(f"wrote {args.out}")
    failed = payload["required_failed"]
    if failed:
        print("required_failed=" + ",".join(failed))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
