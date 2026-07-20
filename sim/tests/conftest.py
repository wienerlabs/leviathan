import torch
import pytest

from leviathan_sim.swarm import CharCorpus


@pytest.fixture(scope="session")
def corpus() -> CharCorpus:
    generator = torch.Generator().manual_seed(3)
    vocab_size = 16
    tokens = torch.randint(0, vocab_size, (4096,), generator=generator)
    return CharCorpus(tokens[:3600], tokens[3600:], vocab_size)
