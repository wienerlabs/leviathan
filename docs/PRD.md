# Product requirements, Phase 1 to 2

## Users

- GPU volunteer: has a 16 to 24 GB consumer card and 50 Mbps broadband. Wants one-line install, a wallet, visible earnings, no ML expertise.
- Datacenter supplier: has H100/B200 fleets (DanteGPU cohort). Wants predictable yield per GPU-hour and clean settlement in USDC or the network token.
- Verifier operator: runs replay audits for bounty income. Wants deterministic tooling and honest dispute resolution.
- Model consumer: wants open weights, checkpoints, and a paid inference endpoint whose revenue funds the flywheel.
- Spectator: the growth engine. Watches the collective loss curve go down, sees the node map, joins.

## Jobs to be done

1. Join the swarm in under 5 minutes: install daemon, fund bond, start earning.
2. See my contribution: per-round accepted work, PoG earned, my rank.
3. Trust the run: live uncaught-rate, audit stats, slash events, all public.
4. Catch a cheater: verifier files a fraud proof and collects the bounty without human support.
5. Leave cleanly: exit after challenge window, bond returned.

## Phase 1 acceptance (devnet core)

- Coordinator fork deploys to devnet with bond, audit assignment, dispute and slash instructions live.
- 4-process local swarm trains the 826k-parameter sim model through the real chain path: join with bond, commit roots, witness, aggregate, checkpoint.
- End-to-end conviction demo: a node submitting fabricated deltas is audited, disputed, slashed and ejected, recorded in one continuous capture.
- All state transitions covered by anchor tests; replay verifier reproduces a sampled contribution within the tolerance band on two different GPUs.

## Phase 2 acceptance (Genesis Run)

- 50+ external nodes sustain a 350M to 1B run for 7+ days with churn.
- Public site: live loss curve, node map, leaderboard, audit and slash feed, join command.
- At least one real slash event or a standing red-team bounty that failed to cheat undetected.
- Checkpoint lineage on Arweave; final weights published open.

## Non-goals for now

- Frontier-scale model quality; the product is the trust machine.
- Windows node support; Linux plus CUDA first, macOS observer mode later.
- Generic compute marketplace features; DanteGPU already covers rental.
- On-chain gradient storage in any form.

## Success metrics

- Time-to-join under 5 minutes at p50.
- Round attestation reliability over 99% across 7 days.
- Uncaught-cheat rate at or under the published 1/(p x R) target.
- Zero honest-node slashes (the Condorcet FPR discipline: false positives are the failure metric that matters).
- Spectator conversion: unique visitors to node joins.
