# Leviathan

Trustless training for the People's model. Working draft v0, 2026-07-19.

## 1. Thesis

Frontier AI is produced inside five balance sheets. The constraint is not algorithmic: the mathematics of training over the open internet is solved and shipping. The constraint is trust. Nobody has made it safe to accept a gradient from a stranger and pay them for it.

Leviathan is a Solana-coordinated training network where anyone with a GPU joins by posting a bond, earns by contributing gradients that survive verification, and loses the bond if they lie. The chain carries commitments, audits and money. The mesh carries compressed tensors. The model belongs to the network that trained it.

Hobbes drew Leviathan as a giant composed of thousands of individuals. This one is composed of thousands of GPUs.

## 2. Why this is possible now

Every load-bearing claim below shipped in public between 2024 and 2026:

- Bandwidth. DiLoCo-class outer loops cut synchronization ~500x. SparseLoCo adds chunked top-k at 1-2% density with 2-bit quantization and error feedback: a 1B-scale sync fits in tens of MB, under 1 Mbps sustained on home broadband.
- Scale. Templar's Covenant-72B pretrained a 72.7B model over ~1.1T tokens across ~70 permissionless heterogeneous peers at 94.5% compute utilization. Nous post-trained Hermes 4.3 (36B) on Psyche across 24 nodes at 144k tok/s and beat the centrally trained control. Prime Intellect ran INTELLECT-2 (32B) as decentralized RL. The transport layer is no longer the frontier.
- Coordination. Psyche put the full training state machine on Solana: rounds, witnesses, checkpoints, all advanced by a permissionless crank. It works. It is Apache-2.0. We fork it.
- Verification. OVIG (June 2026) demonstrated the bonded-commit, sampled-replay, slashing loop for training integrity at 1.143x overhead, with tolerance bands calibrated to survive heterogeneous-hardware numerical drift. What was an open problem is now an engineering problem.

## 3. The open slot

Survey the field and a matrix appears. Everyone picked one column:

| | Verification guarantees | Live economics (bonds, slashing) |
|---|---|---|
| Bittensor training subnets | scoring gates, admitted gaps | emissions only, no bonds |
| Nous Psyche | witness liveness, verifier is a todo | no stake, dead slash code, whitelist |
| Gensyn Verde | strong, but FP32 single-GPU determinism | pre-mainnet |
| OVIG | strong, tolerance-band replay | paper, not a network |
| Leviathan | OVIG-style replay audits | bonds sized (1-p)/p, live slashing |

Nobody runs bonded contributions plus random replay audits plus slashing for live LLM training. That combination is the entire moat, and the pieces are individually proven.

## 4. Protocol

Roles: trainers produce compressed pseudo-gradients from deterministic (checkpoint, seed, data) assignments. Verifiers replay sampled contributions inside published tolerance bands and file fraud proofs. The coordinator program sequences rounds and assigns audits from on-chain randomness. The ledger mints Proof of Gradient rewards for accepted work and slashes convicted fraud.

Round lifecycle: assign, train, commit root on chain, witness availability, audit lottery at probability p, aggregate with centered clipping and far-outlier excision, outer step, checkpoint to Arweave, settle.

Proof of Gradient: work is rewarded if and only if it was committed before aggregation, survived selection, and was not convicted in audit. Rewards scale with accepted work, calibrated to market compute cost. Bitcoin paid for hashes; this pays for learning.

## 5. Security model

Three layers, each covering the others' gap:

1. Robust aggregation bounds damage. Centered clipping with excision caps any contribution's influence radius in the round it happens. Ported from Condorcet and re-validated on real transformer gradients in sim/: naive mean collapses under a 5/16 sign-flip coalition while clip plus excision tracks the honest baseline and ejects the coalition from selection.
2. Replay audits price lying. Each contribution is audited with probability p. Local rounds are replayable pure functions, so a mismatch beyond the tolerance band is a binary fraud proof judged by a bonded committee.
3. Bonds make sybil a cost. Break-even bond = reward x (1-p)/p. At p = 0.1 the bond is 9 rounds of reward; expected time to catch a persistent cheater is 1/p rounds; a slashed identity re-enters only by posting a fresh bond. Security is self-funding under attack: slashed stake pays the verifiers hunting it.

What we do not claim: cryptographic proof of training. The uncaught-rate, the tolerance band width, and the bond curve are published dashboard metrics, because the honest version of this system is the only durable one. Stealth attacks like ALIE that hide inside honest variance defeat aggregation alone; they are exactly what the audit layer exists to catch, and the sim quantifies both halves.

## 6. Economics

Calibration anchors rewards to compute reality: reward per round = 1.2x the H100-market cost of the round's FLOPs. The sim ships the full table; the shape is what matters. At audit rate p = 0.1, bonds stay under ten rounds of reward at every scale from 125M to 7B, an entry cost measured in tens of dollars for volunteers and low thousands for datacenter suppliers, while making persistent cheating expected-negative.

Flywheel: inference fees (vLLM workers verified by TOPLOC activation commitments) flow to the treasury; the treasury funds the next training run; futarchy (Wienerpad) decides what the network trains next.

## 7. Roadmap

- Phase 0, proof. This document, the prior-art decision log, and the sim: Condorcet security economics re-derived on real transformer gradients. Done.
- Phase 1, devnet core. Fork the nousnet coordinator, wire the bond, audit and slash accounts upstream left dead, run a 4-node local swarm with an end-to-end conviction demo.
- Phase 2, Genesis Run. Public testnet: 50+ volunteer nodes, 350M to 1B model, live collective loss curve, one-line join.
- Phase 3, mainnet. TGE, real bonds, Proof of Gradient live, open-weight release, inference network v0.
- Phase 4, scale. DanteGPU enterprise supply, 7B+, futarchy governance, optional TEE attestation lane.

## 8. Honest limitations

- Economic security has a floor: coalitions below the excision threshold that also stay inside the tolerance band can bias training slowly. The published band is the adversary's budget; we choose it with the sim, and we would rather publish that number than pretend it is zero.
- A 1B volunteer-trained model is not a frontier model. The claim is a proven path, not an arrived destination: each run scales the trust machine that a frontier-scale run requires.
- Solana congestion or program bugs stall rounds; the coordinator inherits Psyche's pause and resume machinery, and the fork keeps its centralized backend for disaster recovery.
- Token design must survive regulation; utility-first, no yield promises, legal review before TGE.
