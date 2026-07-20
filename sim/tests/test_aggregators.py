import torch

from leviathan_sim.aggregators import CenteredClipAggregator, MeanAggregator


def make_deltas(n_honest: int = 7, n_malicious: int = 1, scale: float = 40.0):
    generator = torch.Generator().manual_seed(5)
    base = torch.randn(64, generator=generator)
    deltas = {}
    for wid in range(n_honest):
        noise = torch.randn(64, generator=generator) * 0.05
        deltas[wid] = base + noise
    for wid in range(n_honest, n_honest + n_malicious):
        deltas[wid] = -scale * base
    honest_mean = torch.stack([deltas[w] for w in range(n_honest)]).mean(dim=0)
    return deltas, honest_mean, set(range(n_honest, n_honest + n_malicious))


def test_mean_is_corrupted_by_one_outlier():
    deltas, honest_mean, _ = make_deltas()
    agg, mask = MeanAggregator().aggregate(deltas)
    assert all(mask.values())
    assert torch.linalg.vector_norm(agg - honest_mean) > torch.linalg.vector_norm(honest_mean)


def test_clip_excises_far_outlier_and_tracks_honest_mean():
    deltas, honest_mean, malicious = make_deltas()
    agg, mask = CenteredClipAggregator().aggregate(deltas)
    for wid in malicious:
        assert mask[wid] is False
    for wid in range(7):
        assert mask[wid] is True
    error = torch.linalg.vector_norm(agg - honest_mean) / torch.linalg.vector_norm(honest_mean)
    assert error < 0.1


def test_clip_center_persists_across_rounds():
    deltas, _, _ = make_deltas(n_malicious=0)
    aggregator = CenteredClipAggregator()
    first, _ = aggregator.aggregate(deltas)
    assert aggregator.center is not None
    second, _ = aggregator.aggregate(deltas)
    assert torch.linalg.vector_norm(second - first) < torch.linalg.vector_norm(first)


def test_excision_falls_back_to_keep_all_when_everything_is_far():
    deltas = {0: torch.full((8,), 100.0), 1: torch.full((8,), -100.0)}
    _, mask = CenteredClipAggregator(excision_multiplier=0.0).aggregate(deltas)
    assert all(mask.values())
