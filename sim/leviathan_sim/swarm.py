from dataclasses import dataclass
from pathlib import Path

import torch
from torch.nn.utils import parameters_to_vector

from leviathan_sim.model import TinyGPT


def load_vector(model: TinyGPT, vector: torch.Tensor) -> None:
    pointer = 0
    for param in model.parameters():
        numel = param.numel()
        param.data.copy_(vector[pointer : pointer + numel].view_as(param))
        pointer += numel


@dataclass(frozen=True)
class CharCorpus:
    train_tokens: torch.Tensor
    val_tokens: torch.Tensor
    vocab_size: int


def load_corpus(path: Path, val_fraction: float = 0.1) -> CharCorpus:
    text = path.read_text(encoding="utf-8")
    alphabet = sorted(set(text))
    lookup = {ch: i for i, ch in enumerate(alphabet)}
    data = torch.tensor([lookup[ch] for ch in text], dtype=torch.long)
    split = int(len(data) * (1.0 - val_fraction))
    return CharCorpus(data[:split], data[split:], len(alphabet))


def shard_bounds(n_tokens: int, n_workers: int, wid: int, iid: bool) -> tuple[int, int]:
    if iid:
        return 0, n_tokens
    width = n_tokens // n_workers
    return wid * width, (wid + 1) * width


def sample_batch(
    tokens: torch.Tensor,
    lo: int,
    hi: int,
    batch_size: int,
    block_size: int,
    generator: torch.Generator,
) -> tuple[torch.Tensor, torch.Tensor]:
    span = hi - lo - block_size - 1
    starts = lo + torch.randint(span, (batch_size,), generator=generator)
    inputs = torch.stack([tokens[s : s + block_size] for s in starts])
    targets = torch.stack([tokens[s + 1 : s + 1 + block_size] for s in starts])
    return inputs, targets


def round_seed(worker_seed: int, round_index: int) -> int:
    return (worker_seed * 1_000_003 + round_index) & 0x7FFF_FFFF


@dataclass(frozen=True)
class LocalUpdate:
    wid: int
    delta: torch.Tensor
    work_done: int


class SwarmWorker:
    def __init__(
        self,
        wid: int,
        corpus: CharCorpus,
        n_workers: int,
        iid: bool,
        inner_steps: int,
        inner_lr: float,
        batch_size: int,
        block_size: int,
        seed: int,
        device: torch.device,
    ):
        self.wid = wid
        self.corpus = corpus
        self.lo, self.hi = shard_bounds(len(corpus.train_tokens), n_workers, wid, iid)
        self.inner_steps = inner_steps
        self.inner_lr = inner_lr
        self.batch_size = batch_size
        self.block_size = block_size
        self.seed = seed
        self.device = device

    def local_round(self, global_vector: torch.Tensor, model: TinyGPT, round_index: int) -> LocalUpdate:
        generator = torch.Generator().manual_seed(round_seed(self.seed, round_index))
        load_vector(model, global_vector)
        optimizer = torch.optim.AdamW(model.parameters(), lr=self.inner_lr)
        model.train()
        for _ in range(self.inner_steps):
            inputs, targets = sample_batch(
                self.corpus.train_tokens,
                self.lo,
                self.hi,
                self.batch_size,
                self.block_size,
                generator,
            )
            loss = model(inputs.to(self.device), targets.to(self.device))
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
        theta_local = parameters_to_vector(model.parameters()).detach()
        return LocalUpdate(self.wid, global_vector - theta_local, self.inner_steps)


class NesterovOuter:
    def __init__(self, theta_init: torch.Tensor, lr: float = 0.7, momentum: float = 0.9):
        self.theta = theta_init.clone()
        self.lr = lr
        self.momentum = momentum
        self.buffer = torch.zeros_like(self.theta)

    def step(self, delta_agg: torch.Tensor) -> torch.Tensor:
        self.buffer = self.momentum * self.buffer + delta_agg
        update = delta_agg + self.momentum * self.buffer
        self.theta = self.theta - self.lr * update
        return self.theta


def evaluate(
    model: TinyGPT,
    corpus: CharCorpus,
    global_vector: torch.Tensor,
    batch_size: int,
    block_size: int,
    device: torch.device,
    n_batches: int = 16,
) -> float:
    load_vector(model, global_vector)
    model.eval()
    generator = torch.Generator().manual_seed(1234)
    total = 0.0
    with torch.no_grad():
        for _ in range(n_batches):
            inputs, targets = sample_batch(
                corpus.val_tokens, 0, len(corpus.val_tokens), batch_size, block_size, generator
            )
            total += model(inputs.to(device), targets.to(device)).item()
    return total / n_batches
