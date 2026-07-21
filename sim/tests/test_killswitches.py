import json
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from check_killswitches import assess_security, evaluate  # noqa: E402


def test_secure_at_break_even():
    sec = assess_security(0.1, reward=1000.0, bond=100_000.0, slash=9000.0)
    assert sec["economically_secure"] is True
    assert sec["expected_fraud_value_per_round"] <= 0.0


def test_insecure_when_slash_too_small():
    sec = assess_security(0.1, reward=1000.0, bond=100_000.0, slash=1000.0)
    assert sec["economically_secure"] is False


def test_mesh_partition_signal():
    signals = evaluate(
        {
            "audit_probability": 0.1,
            "reward_per_round": 1.0,
            "bond": 9.0,
            "slash_when_caught": 9.0,
            "registered_clients": 20,
            "active_clients": 5,
            "run_state": "RoundTrain",
            "fraud_proofs": 0,
            "slash_events": 0,
            "honest_slashes": 0,
        }
    )
    by_name = {s.name: s for s in signals}
    assert by_name["mesh_partition"].fired is True
    assert by_name["economic_insecurity"].fired is False


def test_uncaught_fraud_signal():
    signals = evaluate(
        {
            "audit_probability": 0.1,
            "reward_per_round": 1.0,
            "bond": 9.0,
            "slash_when_caught": 9.0,
            "registered_clients": 10,
            "active_clients": 10,
            "run_state": "RoundTrain",
            "fraud_proofs": 2,
            "slash_events": 0,
            "honest_slashes": 0,
        }
    )
    by_name = {s.name: s for s in signals}
    assert by_name["uncaught_fraud"].fired is True


def test_fixture_roundtrip(tmp_path: Path):
    path = tmp_path / "t.json"
    reward = 0.288
    bond = reward * 9.0
    path.write_text(
        json.dumps(
            {
                "audit_probability": 0.1,
                "reward_per_round": reward,
                "bond": bond,
                "slash_when_caught": bond,
                "registered_clients": 50,
                "active_clients": 48,
                "run_state": "RoundTrain",
                "fraud_proofs": 0,
                "slash_events": 0,
                "honest_slashes": 0,
                "indexer_slot_lag": 3,
            }
        )
    )
    data = json.loads(path.read_text())
    fired = [s for s in evaluate(data) if s.fired]
    assert fired == []
