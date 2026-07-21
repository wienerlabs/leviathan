#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sim"))

from leviathan_sim.economy import (  # noqa: E402
    audit_burn_projection,
    calibration_table,
    genesis_parameters,
)


def main() -> int:
    payload = {
        "genesis": genesis_parameters(),
        "calibration_p": calibration_table([0.02, 0.05, 0.1, 0.2, 0.3]),
        "zero_fraud_burn": audit_burn_projection([0.1]),
        "slash_bounty_fraction_default": 0.5,
        "slash_bounty_bps_default": 5000,
    }
    out = ROOT / "docs" / "assets" / "tokenomics.json"
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {out}")
    print(json.dumps(payload["genesis"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
