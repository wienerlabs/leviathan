from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_telemetry import (  # noqa: E402
    analyze_band_sweep,
    analyze_phase0,
    analyze_verify,
    decide,
    load_json,
    structural_gates,
)


def test_phase0_gates_pass_on_checked_in_assets():
    results = load_json(ROOT / "docs" / "assets" / "results.json")
    gates = analyze_phase0(results)
    assert all(g.passed for g in gates)


def test_band_and_verify_pass():
    band = load_json(ROOT / "docs" / "assets" / "band_sweep_results.json")
    verify = load_json(ROOT / "docs" / "assets" / "verify_results.json")
    assert all(g.passed for g in analyze_band_sweep(band) if g.required)
    assert all(g.passed for g in analyze_verify(verify))


def test_structural_gates_force_nogo():
    results = load_json(ROOT / "docs" / "assets" / "results.json")
    band = load_json(ROOT / "docs" / "assets" / "band_sweep_results.json")
    verify = load_json(ROOT / "docs" / "assets" / "verify_results.json")
    gates = []
    gates.extend(analyze_phase0(results))
    gates.extend(analyze_band_sweep(band))
    gates.extend(analyze_verify(verify))
    gates.extend(structural_gates())
    assert decide(gates) == "NO-GO"
