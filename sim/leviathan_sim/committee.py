import math

from leviathan_sim.economy import AUDIT_FEE_MULTIPLIER
from leviathan_sim.economy import PRESETS
from leviathan_sim.economy import REWARD_MARGIN
from leviathan_sim.economy import break_even_bond
from leviathan_sim.economy import h100_round_cost_usd


def quorum_for(committee_size: int) -> int:
    if committee_size <= 0:
        return 0
    return max(1, math.ceil(2 * committee_size / 3))


def byzantine_tolerance(committee_size: int, quorum: int | None = None) -> dict:
    resolved_quorum = quorum_for(committee_size) if quorum is None else quorum
    safety_bound = resolved_quorum - 1
    liveness_bound = committee_size - resolved_quorum
    tolerated = max(0, min(safety_bound, liveness_bound))
    return {
        "committee_size": committee_size,
        "quorum": resolved_quorum,
        "max_malicious_for_safety": max(0, safety_bound),
        "max_malicious_for_liveness": max(0, liveness_bound),
        "tolerated_malicious": tolerated,
        "tolerated_fraction": tolerated / committee_size if committee_size else 0.0,
    }


def collusion_capital_usd(quorum: int, bond_usd: float) -> float:
    return quorum * bond_usd


def verifier_expected_value_usd(
    fraud_rate: float,
    slash_usd: float,
    bounty_bps: int,
    quorum: int,
    audit_cost_usd: float,
) -> float:
    if quorum <= 0:
        return -audit_cost_usd
    bounty_pool = slash_usd * bounty_bps / 10_000.0
    share = bounty_pool / quorum
    return fraud_rate * share - audit_cost_usd


def minimum_bounty_bps(
    fraud_rate: float,
    slash_usd: float,
    quorum: int,
    audit_cost_usd: float,
) -> int | None:
    if fraud_rate <= 0.0 or slash_usd <= 0.0 or quorum <= 0:
        return None
    required_pool = audit_cost_usd / fraud_rate * quorum
    bps = math.ceil(required_pool / slash_usd * 10_000.0)
    if bps > 10_000:
        return None
    return bps


def verifier_sustainable_slash_usd(
    fraud_rate: float,
    quorum: int,
    audit_cost_usd: float,
    bounty_bps: int,
) -> float | None:
    if fraud_rate <= 0.0 or bounty_bps <= 0 or quorum <= 0:
        return None
    return audit_cost_usd * quorum / (fraud_rate * bounty_bps / 10_000.0)


def required_bond_usd(
    audit_probability: float,
    reward_per_round: float,
    quorum: int,
    audit_cost_usd: float,
    bounty_bps: int,
) -> dict:
    deterrence = break_even_bond(audit_probability, reward_per_round)
    sustainability = verifier_sustainable_slash_usd(
        audit_probability, quorum, audit_cost_usd, bounty_bps
    )
    if sustainability is None:
        return {
            "deterrence_bond_usd": deterrence,
            "verifier_sustainable_bond_usd": None,
            "required_bond_usd": deterrence,
            "binding_constraint": "deterrence",
        }
    required = max(deterrence, sustainability)
    binding = "deterrence" if deterrence >= sustainability else "verifier_sustainability"
    return {
        "deterrence_bond_usd": deterrence,
        "verifier_sustainable_bond_usd": sustainability,
        "required_bond_usd": required,
        "binding_constraint": binding,
    }


def committee_table(
    committee_sizes: list[int],
    fraud_rate: float = 0.1,
    bounty_bps: int = 5_000,
) -> list[dict]:
    rows = []
    for preset in PRESETS:
        round_cost = h100_round_cost_usd(preset)
        reward = REWARD_MARGIN * round_cost
        audit_cost = AUDIT_FEE_MULTIPLIER * round_cost
        for size in committee_sizes:
            tolerance = byzantine_tolerance(size)
            quorum = tolerance["quorum"]
            bond_requirement = required_bond_usd(
                fraud_rate, reward, quorum, audit_cost, bounty_bps
            )
            bond = bond_requirement["required_bond_usd"]
            slash = bond
            rows.append(
                {
                    "preset": preset.label,
                    "committee_size": size,
                    "quorum": quorum,
                    "tolerated_malicious": tolerance["tolerated_malicious"],
                    "tolerated_fraction": tolerance["tolerated_fraction"],
                    "deterrence_bond_usd": bond_requirement["deterrence_bond_usd"],
                    "verifier_sustainable_bond_usd": bond_requirement[
                        "verifier_sustainable_bond_usd"
                    ],
                    "bond_usd": bond,
                    "binding_constraint": bond_requirement["binding_constraint"],
                    "slash_usd": slash,
                    "collusion_capital_usd": collusion_capital_usd(quorum, bond),
                    "audit_cost_usd": audit_cost,
                    "verifier_ev_usd": verifier_expected_value_usd(
                        fraud_rate, slash, bounty_bps, quorum, audit_cost
                    ),
                    "minimum_bounty_bps": minimum_bounty_bps(
                        fraud_rate, slash, quorum, audit_cost
                    ),
                }
            )
    return rows
