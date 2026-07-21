#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class Signal:
    name: str
    fired: bool
    severity: str
    detail: str


def assess_security(audit_probability: float, reward: float, bond: float, slash: float) -> dict[str, Any]:
    p = max(0.0, min(1.0, audit_probability))
    effective = min(slash, bond)
    ev = (1.0 - p) * reward - p * effective
    return {
        "audit_probability": p,
        "effective_penalty": effective,
        "expected_fraud_value_per_round": ev,
        "economically_secure": p > 0.0 and ev <= 0.0,
    }


def evaluate(telemetry: dict[str, Any]) -> list[Signal]:
    signals: list[Signal] = []

    p = float(telemetry.get("audit_probability", 0.0))
    reward = float(telemetry.get("reward_per_round", 0.0))
    bond = float(telemetry.get("bond", 0.0))
    slash = float(telemetry.get("slash_when_caught", bond))
    sec = telemetry.get("security") or assess_security(p, reward, bond, slash)
    signals.append(
        Signal(
            name="economic_insecurity",
            fired=not bool(sec.get("economically_secure", False)),
            severity="critical",
            detail=f"ev={sec.get('expected_fraud_value_per_round')}",
        )
    )

    registered = int(telemetry.get("registered_clients", 0))
    active = int(telemetry.get("active_clients", 0))
    live = str(telemetry.get("run_state", "")).lower() not in {"finished", "paused", "uninitialized", ""}
    ratio = (active / registered) if registered > 0 else 1.0
    signals.append(
        Signal(
            name="mesh_partition",
            fired=live and registered > 0 and ratio < 0.5,
            severity="high",
            detail=f"active={active} registered={registered} ratio={ratio:.3f}",
        )
    )

    vault = telemetry.get("vault_balance")
    expected_outflow = telemetry.get("explained_outflow")
    if vault is not None and expected_outflow is not None:
        prev = telemetry.get("vault_balance_prev", vault)
        drop = float(prev) - float(vault)
        signals.append(
            Signal(
                name="treasury_drain",
                fired=drop > float(expected_outflow) + 1e-9,
                severity="critical",
                detail=f"drop={drop} explained={expected_outflow}",
            )
        )

    fraud_proofs = int(telemetry.get("fraud_proofs", 0))
    slash_events = int(telemetry.get("slash_events", 0))
    signals.append(
        Signal(
            name="uncaught_fraud",
            fired=fraud_proofs > slash_events,
            severity="critical",
            detail=f"fraud_proofs={fraud_proofs} slash_events={slash_events}",
        )
    )

    honest_slashes = int(telemetry.get("honest_slashes", 0))
    signals.append(
        Signal(
            name="honest_fpr",
            fired=honest_slashes > 0,
            severity="critical",
            detail=f"honest_slashes={honest_slashes}",
        )
    )

    lag = telemetry.get("indexer_slot_lag")
    if lag is not None:
        signals.append(
            Signal(
                name="indexer_lag",
                fired=int(lag) > 100,
                severity="high",
                detail=f"lag={lag}",
            )
        )

    return signals


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Leviathan kill-switch signals from JSON telemetry")
    parser.add_argument("telemetry", type=Path, help="Path to run telemetry JSON")
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()

    data = json.loads(args.telemetry.read_text())
    signals = evaluate(data)
    fired = [s for s in signals if s.fired]

    if args.json_out:
        args.json_out.write_text(json.dumps([asdict(s) for s in signals], indent=2) + "\n")

    for s in signals:
        mark = "FIRE" if s.fired else "ok"
        print(f"{mark:4} {s.severity:8} {s.name}: {s.detail}")

    if fired:
        print(f"kill_switches_fired={len(fired)}")
        return 2
    print("kill_switches_fired=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
