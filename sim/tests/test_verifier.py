import torch
from torch.nn.utils import parameters_to_vector

from leviathan_sim.attacks import InjectionConfig, Injector
from leviathan_sim.model import build_model
from leviathan_sim.swarm import SwarmWorker
from leviathan_sim.verifier import relative_distance, replay_and_verify

BAND = 0.05
BLOCK_SIZE = 16
DEVICE = torch.device("cpu")


def make_swarm(corpus, n_workers: int = 4):
    model = build_model(corpus.vocab_size, BLOCK_SIZE, seed=7, device=DEVICE)
    theta = parameters_to_vector(model.parameters()).detach().clone()
    workers = [
        SwarmWorker(
            wid, corpus, n_workers, True, inner_steps=2, inner_lr=2e-3,
            batch_size=4, block_size=BLOCK_SIZE, seed=100 + wid, device=DEVICE,
        )
        for wid in range(n_workers)
    ]
    return model, theta, workers


def test_honest_replay_is_exact(corpus):
    model, theta, workers = make_swarm(corpus)
    submitted = workers[0].local_round(theta, model, 0).delta
    verdict = replay_and_verify(workers[0], model, theta, 0, submitted, BAND)
    assert verdict.distance < 1e-6
    assert not verdict.fraud


def test_sign_flip_lands_far_above_the_band(corpus):
    model, theta, workers = make_swarm(corpus)
    honest = workers[1].local_round(theta, model, 0).delta
    verdict = replay_and_verify(workers[1], model, theta, 0, -5.0 * honest, BAND)
    assert verdict.distance > 1.0
    assert verdict.fraud


def test_lazy_zero_delta_is_caught(corpus):
    model, theta, workers = make_swarm(corpus)
    verdict = replay_and_verify(
        workers[2], model, theta, 0, torch.zeros_like(theta), BAND
    )
    assert abs(verdict.distance - 1.0) < 1e-5
    assert verdict.fraud


def test_within_band_submission_passes_replay(corpus):
    model, theta, workers = make_swarm(corpus)
    updates = {w.wid: w.local_round(theta, model, 0) for w in workers}
    injector = Injector(
        InjectionConfig(n_malicious=1, attack="within_band", band=BAND),
        [w.wid for w in workers],
        seed=11,
    )
    attacked, report = injector.apply(updates)
    wid = min(report.malicious_ids)
    verdict = replay_and_verify(workers[wid], model, theta, 0, attacked[wid].delta, BAND)
    assert not verdict.fraud
    assert abs(verdict.distance - BAND * 0.9) < 1e-4


def test_relative_distance_is_scale_invariant():
    a = torch.randn(32, generator=torch.Generator().manual_seed(2))
    assert relative_distance(3.0 * a, 3.0 * a) == 0.0
    assert abs(relative_distance(1.1 * a, a) - 0.1) < 1e-6
