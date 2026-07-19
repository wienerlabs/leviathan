import torch


def chunked_topk_sign(
    vector: torch.Tensor,
    density: float,
    chunk_size: int,
    quantize_sign: bool,
) -> torch.Tensor:
    if density >= 1.0:
        return vector
    length = vector.numel()
    pad = (chunk_size - length % chunk_size) % chunk_size
    padded = torch.cat([vector, vector.new_zeros(pad)]) if pad else vector
    chunks = padded.view(-1, chunk_size)
    keep = max(1, int(round(density * chunk_size)))
    magnitudes = chunks.abs()
    threshold_index = chunk_size - keep
    kth = magnitudes.kthvalue(threshold_index, dim=1, keepdim=True).values if threshold_index > 0 else magnitudes.new_zeros(chunks.size(0), 1)
    mask = magnitudes > kth
    kept = chunks * mask
    if quantize_sign:
        per_chunk_scale = (kept.abs().sum(dim=1, keepdim=True) / mask.sum(dim=1, keepdim=True).clamp(min=1))
        kept = torch.sign(kept) * per_chunk_scale * mask
    out = kept.reshape(-1)[:length]
    return out.contiguous()


def compress_updates(deltas, density: float, chunk_size: int, quantize_sign: bool):
    return {
        wid: chunked_topk_sign(delta, density, chunk_size, quantize_sign)
        for wid, delta in deltas.items()
    }
