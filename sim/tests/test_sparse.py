import torch

from leviathan_sim.sparse import chunked_topk_sign


def test_density_close_to_target():
    vector = torch.randn(64 * 100, generator=torch.Generator().manual_seed(4))
    compressed = chunked_topk_sign(vector, density=0.02, chunk_size=64, quantize_sign=True)
    density = float((compressed != 0).float().mean())
    assert 0.005 <= density <= 0.05


def test_shape_preserved_with_padding():
    vector = torch.randn(1000, generator=torch.Generator().manual_seed(4))
    compressed = chunked_topk_sign(vector, density=0.05, chunk_size=64, quantize_sign=True)
    assert compressed.shape == vector.shape


def test_signs_match_original():
    vector = torch.randn(256, generator=torch.Generator().manual_seed(4))
    compressed = chunked_topk_sign(vector, density=0.1, chunk_size=64, quantize_sign=True)
    kept = compressed != 0
    assert torch.equal(torch.sign(compressed[kept]), torch.sign(vector[kept]))


def test_full_density_is_identity():
    vector = torch.randn(128, generator=torch.Generator().manual_seed(4))
    assert torch.equal(chunked_topk_sign(vector, 1.0, 64, True), vector)


def test_kept_entries_are_the_largest_magnitudes():
    vector = torch.arange(1.0, 65.0)
    compressed = chunked_topk_sign(vector, density=0.05, chunk_size=64, quantize_sign=False)
    kept_indices = torch.nonzero(compressed).flatten().tolist()
    assert kept_indices == [61, 62, 63]
