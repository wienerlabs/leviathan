import torch

from leviathan_sim.attacks import InjectionConfig, Injector
from leviathan_sim.swarm import LocalUpdate


def make_updates(n_workers: int = 6, dim: int = 128, seed: int = 9):
    generator = torch.Generator().manual_seed(seed)
    return {
        wid: LocalUpdate(wid, torch.randn(dim, generator=generator), 8)
        for wid in range(n_workers)
    }


def relative_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm(a - b) / torch.linalg.vector_norm(b))


def test_within_band_stays_inside_the_published_band():
    band = 0.05
    updates = make_updates()
    injector = Injector(
        InjectionConfig(n_malicious=2, attack="within_band", band=band), list(range(6)), seed=1
    )
    attacked, report = injector.apply(updates)
    assert report.malicious_ids == frozenset({0, 1})
    for wid in report.malicious_ids:
        distance = relative_distance(attacked[wid].delta, updates[wid].delta)
        assert distance <= band
        assert abs(distance - band * 0.9) < 1e-5
    for wid in range(2, 6):
        assert torch.equal(attacked[wid].delta, updates[wid].delta)


def test_within_band_scales_with_the_band():
    updates = make_updates()
    for band in (0.02, 0.2):
        injector = Injector(
            InjectionConfig(n_malicious=1, attack="within_band", band=band), list(range(6)), seed=1
        )
        attacked, _ = injector.apply(updates)
        assert abs(relative_distance(attacked[0].delta, updates[0].delta) - band * 0.9) < 1e-5


def test_within_band_bias_opposes_honest_mean():
    updates = make_updates()
    injector = Injector(
        InjectionConfig(n_malicious=1, attack="within_band", band=0.1), list(range(6)), seed=1
    )
    attacked, _ = injector.apply(updates)
    honest_mean = torch.stack([updates[w].delta for w in range(1, 6)]).mean(dim=0)
    bias = attacked[0].delta - updates[0].delta
    cosine = torch.dot(bias, honest_mean) / (
        torch.linalg.vector_norm(bias) * torch.linalg.vector_norm(honest_mean)
    )
    assert cosine < -0.99


def test_sign_flip_scales_and_negates():
    updates = make_updates()
    injector = Injector(InjectionConfig(n_malicious=1, attack="sign_flip"), list(range(6)), seed=1)
    attacked, _ = injector.apply(updates)
    assert torch.allclose(attacked[0].delta, -5.0 * updates[0].delta)


def test_lazy_zeroes_delta_and_work():
    updates = make_updates()
    injector = Injector(InjectionConfig(n_malicious=1, attack="lazy"), list(range(6)), seed=1)
    attacked, _ = injector.apply(updates)
    assert torch.count_nonzero(attacked[0].delta) == 0
    assert attacked[0].work_done == 0


def test_alie_coalition_submits_identical_crafted_delta():
    updates = make_updates()
    injector = Injector(InjectionConfig(n_malicious=2, attack="alie"), list(range(6)), seed=1)
    attacked, _ = injector.apply(updates)
    assert torch.equal(attacked[0].delta, attacked[1].delta)
    honest = torch.stack([updates[w].delta for w in range(2, 6)])
    expected = honest.mean(dim=0) + 1.5 * honest.std(dim=0)
    assert torch.allclose(attacked[0].delta, expected)


def test_unknown_attack_rejected():
    try:
        Injector(InjectionConfig(attack="nope"), [0], seed=1)
    except ValueError:
        return
    raise AssertionError("expected ValueError")
