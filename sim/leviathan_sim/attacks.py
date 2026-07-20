from dataclasses import dataclass, replace

import torch

from leviathan_sim.swarm import LocalUpdate

VALID_ATTACKS = frozenset({"none", "sign_flip", "gaussian", "lazy", "alie", "within_band"})


@dataclass(frozen=True)
class InjectionConfig:
    n_malicious: int = 0
    attack: str = "none"
    sign_flip_scale: float = 5.0
    gaussian_std: float = 0.02
    alie_z: float = 1.5
    band: float = 0.05
    band_margin: float = 0.9


@dataclass(frozen=True)
class InjectionReport:
    malicious_ids: frozenset[int]


class Injector:
    def __init__(self, config: InjectionConfig, worker_ids: list[int], seed: int):
        if config.attack not in VALID_ATTACKS:
            raise ValueError(f"unknown attack: {config.attack}")
        self.config = config
        self.generator = torch.Generator().manual_seed(seed)
        self.malicious_ids = frozenset(sorted(worker_ids)[: config.n_malicious])

    def apply(self, updates: dict[int, LocalUpdate]) -> tuple[dict[int, LocalUpdate], InjectionReport]:
        return self._attack(updates), InjectionReport(self.malicious_ids)

    def _attack(self, updates: dict[int, LocalUpdate]) -> dict[int, LocalUpdate]:
        config = self.config
        if config.attack == "none" or not self.malicious_ids:
            return updates
        out = dict(updates)
        if config.attack == "within_band":
            # The adversary's whole budget is the published tolerance band: each
            # malicious worker submits its honest delta plus a coordinated bias
            # scaled so the relative replay distance stays at band_margin * band.
            # Replay audits pass by construction; only aggregation limits this.
            honest = torch.stack(
                [u.delta for wid, u in updates.items() if wid not in self.malicious_ids]
            )
            direction = honest.mean(dim=0)
            direction = direction / torch.linalg.vector_norm(direction).clamp(min=1e-12)
            budget = config.band * config.band_margin
            for wid in self.malicious_ids:
                if wid not in out:
                    continue
                update = out[wid]
                bias = -direction * budget * torch.linalg.vector_norm(update.delta)
                out[wid] = replace(update, delta=update.delta + bias)
            return out
        if config.attack == "alie":
            honest = torch.stack(
                [u.delta for wid, u in updates.items() if wid not in self.malicious_ids]
            )
            crafted = honest.mean(dim=0) + config.alie_z * honest.std(dim=0)
            for wid in self.malicious_ids:
                if wid in out:
                    out[wid] = replace(out[wid], delta=crafted.clone())
            return out
        for wid in self.malicious_ids:
            if wid not in out:
                continue
            update = out[wid]
            if config.attack == "sign_flip":
                out[wid] = replace(update, delta=-config.sign_flip_scale * update.delta)
            elif config.attack == "gaussian":
                noise = torch.randn(update.delta.shape, generator=self.generator)
                out[wid] = replace(update, delta=(noise * config.gaussian_std).to(update.delta.device))
            elif config.attack == "lazy":
                out[wid] = replace(update, delta=torch.zeros_like(update.delta), work_done=0)
        return out
