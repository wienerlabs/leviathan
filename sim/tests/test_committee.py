from leviathan_sim.committee import (
    byzantine_tolerance,
    collusion_capital_usd,
    committee_table,
    minimum_bounty_bps,
    quorum_for,
    required_bond_usd,
    verifier_expected_value_usd,
    verifier_sustainable_slash_usd,
)
from leviathan_sim.economy import PRESETS, break_even_bond


def test_quorum_is_two_thirds_rounded_up():
    assert quorum_for(3) == 2
    assert quorum_for(4) == 3
    assert quorum_for(6) == 4
    assert quorum_for(1) == 1
    assert quorum_for(0) == 0


def test_two_thirds_quorum_tolerates_one_third_malicious():
    for size in [3, 6, 9, 12, 30]:
        tolerance = byzantine_tolerance(size)
        assert tolerance["tolerated_fraction"] <= 1.0 / 3.0 + 1e-9
        assert tolerance["tolerated_malicious"] == size - tolerance["quorum"]


def test_safety_and_liveness_bounds_are_reported_separately():
    tolerance = byzantine_tolerance(6)
    assert tolerance["quorum"] == 4
    assert tolerance["max_malicious_for_safety"] == 3
    assert tolerance["max_malicious_for_liveness"] == 2
    assert tolerance["tolerated_malicious"] == 2


def test_collusion_requires_locking_a_quorum_of_bonds():
    assert collusion_capital_usd(4, 25.0) == 100.0


def test_verifier_loses_money_without_a_bounty():
    ev = verifier_expected_value_usd(
        fraud_rate=0.1,
        slash_usd=100.0,
        bounty_bps=0,
        quorum=2,
        audit_cost_usd=1.0,
    )
    assert ev == -1.0


def test_minimum_bounty_makes_verifier_participation_break_even():
    fraud_rate = 0.1
    slash = 100.0
    quorum = 2
    audit_cost = 1.0
    bps = minimum_bounty_bps(fraud_rate, slash, quorum, audit_cost)
    assert bps is not None
    ev = verifier_expected_value_usd(fraud_rate, slash, bps, quorum, audit_cost)
    assert ev >= 0.0
    below = verifier_expected_value_usd(fraud_rate, slash, bps - 1, quorum, audit_cost)
    assert below < ev


def test_minimum_bounty_is_none_when_slash_cannot_cover_audit_cost():
    assert minimum_bounty_bps(0.01, 1.0, 8, 5.0) is None
    assert minimum_bounty_bps(0.0, 100.0, 2, 1.0) is None


def test_larger_quorum_needs_a_larger_bounty_per_verifier():
    small = minimum_bounty_bps(0.1, 1000.0, 2, 1.0)
    large = minimum_bounty_bps(0.1, 1000.0, 6, 1.0)
    assert small is not None and large is not None
    assert large > small


def test_sustainable_slash_pays_back_the_audit_cost_at_the_fraud_rate():
    slash = verifier_sustainable_slash_usd(
        fraud_rate=0.1,
        quorum=2,
        audit_cost_usd=1.0,
        bounty_bps=10_000,
    )
    assert slash == 20.0
    ev = verifier_expected_value_usd(0.1, slash, 10_000, 2, 1.0)
    assert abs(ev) < 1e-9


def test_required_bond_takes_the_larger_of_the_two_constraints():
    cheap_audit = required_bond_usd(0.1, 1.0, 2, 0.001, 10_000)
    assert cheap_audit["binding_constraint"] == "deterrence"
    assert cheap_audit["required_bond_usd"] == break_even_bond(0.1, 1.0)

    expensive_audit = required_bond_usd(0.1, 1.0, 6, 1.0, 5_000)
    assert expensive_audit["binding_constraint"] == "verifier_sustainability"
    assert expensive_audit["required_bond_usd"] > break_even_bond(0.1, 1.0)


def test_required_bond_keeps_verifiers_profitable_across_presets():
    for row in committee_table([3, 6, 9]):
        assert row["verifier_ev_usd"] >= -1e-9
        assert row["bond_usd"] >= row["deterrence_bond_usd"]


def test_committee_table_covers_every_preset_and_size():
    sizes = [3, 6, 9]
    rows = committee_table(sizes)
    assert len(rows) == len(PRESETS) * len(sizes)
    for row in rows:
        assert row["quorum"] == quorum_for(row["committee_size"])
        assert row["collusion_capital_usd"] == row["quorum"] * row["bond_usd"]
        assert row["tolerated_malicious"] >= 0
