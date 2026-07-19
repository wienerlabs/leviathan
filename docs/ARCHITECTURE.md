# Architecture

## System overview

```
                    Solana mainnet
   +---------------------------------------------------+
   |  coordinator      ledger          treasury        |
   |  round state      bonds, PoG      inference fees  |
   |  machine, audit   mint, slash     endowment       |
   |  assignment       routing                         |
   +-------^-------------------^-----------------------+
           | commitments,      | claims,
           | witness, audit    | rewards
           | verdicts          |
   +-------+-------------------+-----------------------+
   |                iroh P2P mesh                      |
   |  gossip: metadata     blobs: compressed deltas    |
   +---^-----------------^------------------^----------+
       |                 |                  |
  +----+-----+     +-----+-----+      +-----+-----+
  | trainer  |     | trainer   |      | verifier  |
  | daemon   |     | daemon    | ...  | daemon    |
  | GPU node |     | GPU node  |      | replay    |
  +----------+     +-----------+      | audits    |
                                      +-----------+
       checkpoints -> Arweave (zk-lokomotive rail)
       live telemetry -> web (collective loss curve)
```

The chain never carries tensors. It carries merkle commitments, witness quorums, audit verdicts, bonds and rewards. Compressed pseudo-gradients move over iroh; checkpoints land on Arweave and mirrors.

## On-chain programs (nousnet fork + our layer)

Inherited from the fork and kept:

- coordinator: run state machine (WaitingForMembers, Warmup, RoundTrain, RoundWitness, Cooldown) advanced by a permissionless tick crank; per-round random seed; commitment format sha256 data hash + signature; epoch boundaries for join and leave
- authorizer: set to the permissionless sentinel; authority gating stays available for private runs
- treasurer: escrow paying per earned point
- distributor: merkle airdrop with vesting, reused at TGE
- mining pool: funder escrow, reused for the compute endowment

Our additions, the part upstream left as todo:

- bond account per participant: join requires depositing the bond; leaving returns it after a challenge window
- audit assignment: each round, the on-chain seed deterministically selects contributions for replay audit at probability p, and assigns each to a verifier committee via shuffled-index selection
- dispute and verdict: a verifier submits a fraud claim with the replayed commitment; a bonded committee votes; conviction slashes the full bond, routes a bounty to the reporting verifier, ejects the identity
- reward routing: earned points convert to Proof of Gradient emissions only for contributions that survived selection, weighted by accepted work; treasurer reads slash state, which upstream never wired

## Off-chain daemons

- trainer: fork of the nousnet Rust client. Local DiLoCo inner loop, SparseLoCo-class compression on the outer sync, deterministic per-round derived seeds so every local round is a replayable pure function of (checkpoint, seed, data assignment). Publishes delta blobs to iroh, commits the merkle root on chain.
- verifier: replays sampled contributions from the same (checkpoint, seed, data) tuple and compares within a calibrated tolerance band, OVIG style, rather than demanding bitwise equality. The band is calibrated per hardware class and published; drift outside the band is a fraud proof. Runs the centered-clip excision check as a cheap pre-filter.
- aggregation: centered clipping with far-outlier excision over compressed pseudo-gradients, ported from Condorcet and validated in sim/ on real transformer gradients. Norm-capping by construction bounds any single contribution's damage radius between audits.
- relay and tracker: iroh relay fallback for the ~10% of nodes that cannot hole-punch.
- web: live collective loss curve, node map, leaderboard, one-line install.

## Round lifecycle

1. Coordinator publishes round seed and data assignments.
2. Trainers run H inner steps locally, produce compressed pseudo-gradient delta, publish blob, commit root on chain.
3. Witness quorum attests availability (bloom filters, inherited mechanism).
4. Audit lottery fires at probability p per contribution; assigned verifiers replay and submit verdicts. Disputes settle before reward distribution for that round's audited subset; unaudited contributions pay out optimistically.
5. Aggregator output (clip + excision) becomes the outer step with Nesterov momentum; designated checkpointers publish to Arweave and update the on-chain pointer.
6. Ledger settles: accepted work earns PoG, convicted fraud slashes bonds, bounties pay verifiers.

## Security model, three layers

1. Robust aggregation bounds the damage radius of anything that slips through in the current round.
2. Random replay audits raise the price of lying; detection probability p per contribution per round.
3. Bonds make the adversary fraction a priced quantity: bond >= reward x (1-p)/p makes expected cheating value negative, and slashing plus identity ejection makes sybil re-entry cost the bond again.

Claims discipline: this is economic security with published parameters (p, tolerance band width, uncaught rate 1/(p x rounds)), not cryptographic proof. TEE attestation (Blackwell confidential computing) is a planned optional fourth layer for datacenter-class suppliers, not a base requirement.

## Determinism strategy

Bitwise replay across heterogeneous GPUs is not assumed. Following OVIG and NAO, verifier comparison uses stride-aligned interval evidence with empirically calibrated tolerance boundaries per hardware class. The published band width is explicitly the adversary's safe margin; sim/ tracks how much loss damage fits inside a given band so the parameter is chosen with eyes open. RepOps-style bitwise determinism (30-130% overhead, FP32, single GPU) was rejected as the base path but remains viable for high-value dispute escalation.

## What runs where, phase by phase

- Phase 1: coordinator + ledger on devnet, 4-node local swarm on one machine, full slash demo end to end.
- Phase 2 Genesis Run: public testnet, 50+ volunteer nodes, 350M to 1B model, live site.
- Phase 3: mainnet, TGE via Wiener Launchpad, real bonds, inference network v0 with TOPLOC.
- Phase 4: DanteGPU enterprise supply, 7B+ runs, Wienerpad futarchy choosing the next model.
