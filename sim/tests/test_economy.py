from leviathan_sim.economy import (
    EconomyConfig,
    StakeLedger,
    audit_burn_projection,
    break_even_bond,
    calibration_table,
    genesis_parameters,
)


def test_break_even_bond_is_nine_rewards_at_p_10():
    assert break_even_bond(0.1, 1.0) == 9.0


def test_certain_audit_slashes_malicious_on_first_round():
    ledger = StakeLedger([0, 1], EconomyConfig(audit_probability=1.0), seed=17)
    caught = ledger.settle_round(0, {0: True, 1: True}, frozenset({1}))
    assert caught == [1]
    assert ledger.balances[1] == 0.0
    assert 1 not in ledger.active_ids
    assert ledger.caught[1] == 0


def test_slash_splits_bond_between_bounty_and_treasury():
    config = EconomyConfig(bond=10.0, slash_bounty_fraction=0.5)
    ledger = StakeLedger([0], config, seed=17)
    ledger.slash(0)
    assert ledger.verifier_income == 5.0
    assert ledger.treasury == 5.0
    assert ledger.pnl()[0] == -10.0


def test_honest_selected_worker_earns_reward():
    ledger = StakeLedger([0], EconomyConfig(audit_probability=0.0), seed=17)
    ledger.settle_round(0, {0: True}, frozenset())
    assert ledger.pnl()[0] == ledger.config.reward_selected


def test_calibration_bond_scales_with_reward():
    rows = calibration_table([0.1])
    by_preset = {row["preset"]: row for row in rows}
    for row in rows:
        assert abs(row["break_even_bond_usd"] - 9.0 * row["round_reward_usd"]) < 1e-9
    assert (
        by_preset["7B scale run"]["break_even_bond_usd"]
        > by_preset["125M proof run"]["break_even_bond_usd"]
    )


def test_zero_fraud_burn_share_is_preset_independent():
    rows = audit_burn_projection([0.1])
    expected = 0.1 * 1.1 / 1.2
    for row in rows:
        assert abs(row["burn_share_of_rewards"] - expected) < 1e-9
        assert row["treasury_burn_per_round_usd"] > 0.0


def test_genesis_parameters_follow_the_published_discipline():
    params = genesis_parameters(audit_probability=0.1, band=0.05)
    assert params["preset"] == "1B genesis run"
    assert params["bond_rounds_of_reward"] == 9.0
    assert abs(params["bond_usd"] - 9.0 * params["round_reward_usd"]) < 1e-9
    assert params["expected_rounds_to_catch"] == 10.0
    assert params["tolerance_band"] == 0.05
