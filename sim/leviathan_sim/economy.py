from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class EconomyConfig:
    bond: float = 9.0
    reward_selected: float = 1.0
    audit_probability: float = 0.1
    audit_fee: float = 0.1
    slash_bounty_fraction: float = 0.5


class StakeLedger:
    def __init__(self, worker_ids: list[int], config: EconomyConfig, seed: int):
        self.config = config
        self.balances = {wid: config.bond for wid in worker_ids}
        self.active_ids = set(worker_ids)
        self.treasury = 0.0
        self.verifier_income = 0.0
        self.rng = np.random.default_rng(seed)
        self.caught: dict[int, int] = {}

    def settle_round(
        self, round_index: int, mask: dict[int, bool], malicious_ids: frozenset[int]
    ) -> list[int]:
        caught_now: list[int] = []
        for wid, selected in mask.items():
            if wid not in self.active_ids:
                continue
            if self.rng.random() < self.config.audit_probability:
                self.treasury -= self.config.audit_fee
                self.verifier_income += self.config.audit_fee
                if wid in malicious_ids:
                    self.slash(wid)
                    self.caught[wid] = round_index
                    caught_now.append(wid)
                    continue
            if selected:
                self.balances[wid] += self.config.reward_selected
        return caught_now

    def slash(self, wid: int) -> None:
        seized = self.balances[wid]
        self.balances[wid] = 0.0
        self.active_ids.discard(wid)
        bounty = self.config.slash_bounty_fraction * seized
        self.verifier_income += bounty
        self.treasury += seized - bounty

    def pnl(self) -> dict[int, float]:
        return {wid: balance - self.config.bond for wid, balance in self.balances.items()}


def break_even_bond(audit_probability: float, reward_per_round: float) -> float:
    return reward_per_round * (1.0 - audit_probability) / audit_probability


@dataclass(frozen=True)
class RunPreset:
    label: str
    params_billion: float
    round_tokens_million: float


PRESETS = [
    RunPreset("125M proof run", 0.125, 8.0),
    RunPreset("1B genesis run", 1.0, 20.0),
    RunPreset("7B scale run", 7.0, 40.0),
]


def h100_round_cost_usd(
    preset: RunPreset,
    usd_per_gpu_hour: float = 2.49,
    dense_tflops: float = 989.0,
    utilization: float = 0.35,
) -> float:
    flops = 6.0 * preset.params_billion * 1e9 * preset.round_tokens_million * 1e6
    seconds = flops / (dense_tflops * 1e12 * utilization)
    return seconds / 3600.0 * usd_per_gpu_hour


def calibration_table(audit_probabilities: list[float]) -> list[dict]:
    rows = []
    for preset in PRESETS:
        cost = h100_round_cost_usd(preset)
        reward = 1.2 * cost
        for p in audit_probabilities:
            rows.append(
                {
                    "preset": preset.label,
                    "round_cost_usd": cost,
                    "round_reward_usd": reward,
                    "audit_probability": p,
                    "break_even_bond_usd": break_even_bond(p, reward),
                    "expected_rounds_to_catch": 1.0 / p,
                }
            )
    return rows
