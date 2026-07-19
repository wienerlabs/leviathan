import torch
import torch.nn.functional as F
from torch import nn


class CausalSelfAttention(nn.Module):
    def __init__(self, n_embd: int, n_head: int):
        super().__init__()
        self.n_head = n_head
        self.qkv = nn.Linear(n_embd, 3 * n_embd)
        self.proj = nn.Linear(n_embd, n_embd)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch, length, width = x.shape
        query, key, value = self.qkv(x).split(width, dim=2)
        head_width = width // self.n_head
        query = query.view(batch, length, self.n_head, head_width).transpose(1, 2)
        key = key.view(batch, length, self.n_head, head_width).transpose(1, 2)
        value = value.view(batch, length, self.n_head, head_width).transpose(1, 2)
        attended = F.scaled_dot_product_attention(query, key, value, is_causal=True)
        merged = attended.transpose(1, 2).contiguous().view(batch, length, width)
        return self.proj(merged)


class TransformerBlock(nn.Module):
    def __init__(self, n_embd: int, n_head: int):
        super().__init__()
        self.attn_norm = nn.LayerNorm(n_embd)
        self.attn = CausalSelfAttention(n_embd, n_head)
        self.mlp_norm = nn.LayerNorm(n_embd)
        self.mlp = nn.Sequential(
            nn.Linear(n_embd, 4 * n_embd),
            nn.GELU(),
            nn.Linear(4 * n_embd, n_embd),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.attn_norm(x))
        x = x + self.mlp(self.mlp_norm(x))
        return x


class TinyGPT(nn.Module):
    def __init__(self, vocab_size: int, block_size: int, n_layer: int, n_head: int, n_embd: int):
        super().__init__()
        self.block_size = block_size
        self.token_embedding = nn.Embedding(vocab_size, n_embd)
        self.position_embedding = nn.Parameter(torch.zeros(1, block_size, n_embd))
        self.blocks = nn.ModuleList(TransformerBlock(n_embd, n_head) for _ in range(n_layer))
        self.final_norm = nn.LayerNorm(n_embd)
        self.lm_head = nn.Linear(n_embd, vocab_size, bias=False)

    def forward(self, tokens: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        length = tokens.size(1)
        x = self.token_embedding(tokens) + self.position_embedding[:, :length]
        for block in self.blocks:
            x = block(x)
        logits = self.lm_head(self.final_norm(x))
        return F.cross_entropy(logits.view(-1, logits.size(-1)), targets.reshape(-1))


def build_model(vocab_size: int, block_size: int, seed: int, device: torch.device) -> TinyGPT:
    torch.manual_seed(seed)
    model = TinyGPT(vocab_size, block_size, n_layer=4, n_head=4, n_embd=128)
    return model.to(device)


def parameter_count(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())
