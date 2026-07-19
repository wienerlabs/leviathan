import torch

SelectionMask = dict[int, bool]


class MeanAggregator:
    name = "mean"

    def aggregate(self, deltas: dict[int, torch.Tensor]) -> tuple[torch.Tensor, SelectionMask]:
        stacked = torch.stack(list(deltas.values()))
        return stacked.mean(dim=0), {wid: True for wid in deltas}


class CenteredClipAggregator:
    name = "centered-clip"

    def __init__(self, iterations: int = 3, excision_multiplier: float | None = 3.0):
        self.iterations = iterations
        self.excision_multiplier = excision_multiplier
        self.center: torch.Tensor | None = None
        self.clip_counts: dict[int, int] = {}

    def aggregate(self, deltas: dict[int, torch.Tensor]) -> tuple[torch.Tensor, SelectionMask]:
        wids = list(deltas.keys())
        stacked = torch.stack([deltas[wid] for wid in wids])
        center = self.center if self.center is not None else torch.zeros_like(stacked[0])
        keep = torch.ones(len(wids), dtype=torch.bool, device=stacked.device)
        if self.excision_multiplier is not None:
            distances = torch.linalg.vector_norm(stacked - center, dim=1)
            limit = self.excision_multiplier * distances.median()
            keep = distances <= limit
            if not keep.any():
                keep = torch.ones(len(wids), dtype=torch.bool, device=stacked.device)
        kept = stacked[keep]
        kept_wids = [wid for wid, flag in zip(wids, keep.tolist()) if flag]
        clipped: set[int] = set()
        for _ in range(self.iterations):
            offsets = kept - center
            norms = torch.linalg.vector_norm(offsets, dim=1)
            radius = norms.median()
            factors = torch.clamp(radius / torch.clamp(norms, min=1e-12), max=1.0)
            for i in torch.nonzero(factors < 1.0).flatten().tolist():
                clipped.add(kept_wids[i])
            center = center + (offsets * factors.unsqueeze(1)).mean(dim=0)
        self.center = center
        for wid in clipped:
            self.clip_counts[wid] = self.clip_counts.get(wid, 0) + 1
        return center, {wid: bool(flag) for wid, flag in zip(wids, keep.tolist())}
