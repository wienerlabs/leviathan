# Leviathan

Trustless training for the People's model.

Frontier AI is produced inside five balance sheets. The mathematics of training over the open internet is solved and shipping; what remains unsolved is trust. Nobody has made it safe to accept a gradient from a stranger and pay them for it.

Leviathan is a Solana-coordinated training network where anyone with a GPU joins by posting a bond, earns Proof of Gradient for contributions that survive verification, and loses the bond if they lie. The chain carries commitments, audits and money. The mesh carries compressed tensors. The model belongs to the network that trained it.

Hobbes drew Leviathan as a giant composed of thousands of individuals. This one is composed of thousands of GPUs.

## The open slot

Every live network picked one column. Nobody picked both:

| | Verification guarantees | Live economics (bonds, slashing) |
|---|---|---|
| Bittensor training subnets | scoring gates, admitted gaps | emissions only, no bonds |
| Nous Psyche | witness liveness, verifier is a `todo!()` | no stake, dead slash code, whitelist |
| Gensyn Verde | strong, FP32 single-GPU determinism | pre-mainnet |
| OVIG | tolerance-band replay audits | paper, not a network |
| Leviathan | OVIG-style replay audits | bonds sized (1-p)/p, live slashing |

Three security layers, each covering the others' gap: robust aggregation bounds damage in the round it happens, random replay audits price lying, bonds make sybil a cost. Economic security with published parameters, never a cryptographic overclaim.

## This repository

Phase 0: the proof that the security economics survive contact with real transformer gradients.

| path | contents |
|---|---|
| `sim/` | Condorcet's aggregation, attack and staking layers ported from NumPy blobs to a real GPT trained by a 16-worker swarm: centered clip + excision vs sign-flip and ALIE coalitions, stake ledger with replay audits, break-even bond calibration against H100 market cost |
| `docs/WHITEPAPER.md` | thesis, protocol, security model, economics, honest limitations |
| `docs/DECISIONS.md` | prior-art sweep and the six locked decisions, sources inline |
| `docs/ARCHITECTURE.md` | on-chain programs, daemons, round lifecycle, determinism strategy |
| `docs/PRD.md`, `docs/TASKS.md` | phase acceptance criteria and the task ladder |

Reproduce the sim:

```
cd sim
uv sync
PYTORCH_ENABLE_MPS_FALLBACK=1 uv run python -m leviathan_sim.run --rounds 30
```

## Lineage

Built on the shoulders of, and differentiated from: Psyche/nousnet (Apache-2.0 fork substrate: Solana coordinator, iroh P2P, Rust DisTrO), SparseLoCo (MIT compression recipe), TOPLOC (MIT inference verification), OVIG (the audit loop's academic validation), Condorcet (wienerlabs: the aggregation and bond-economics research core), DanteGPU (supply), Wienerpad (futarchy governance), zk-lokomotive (Arweave rail).

Private under wienerlabs while Phase 1 lands.
