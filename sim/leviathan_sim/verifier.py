from dataclasses import dataclass

import torch

from leviathan_sim.model import TinyGPT
from leviathan_sim.swarm import SwarmWorker


@dataclass(frozen=True)
class Verdict:
    target_wid: int
    distance: float
    band: float
    fraud: bool


def relative_distance(submitted: torch.Tensor, recomputed: torch.Tensor) -> float:
    denom = torch.linalg.vector_norm(recomputed).clamp(min=1e-12)
    return float(torch.linalg.vector_norm(submitted - recomputed) / denom)


def replay_and_verify(
    worker: SwarmWorker,
    model: TinyGPT,
    global_vector: torch.Tensor,
    round_index: int,
    submitted_delta: torch.Tensor,
    band: float,
) -> Verdict:
    recomputed = worker.local_round(global_vector, model, round_index).delta
    distance = relative_distance(submitted_delta, recomputed)
    return Verdict(worker.wid, distance, band, distance > band)
