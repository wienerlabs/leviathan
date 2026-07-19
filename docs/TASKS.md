# Task list

## Phase 0, proof (this repo, done except where marked)

- [x] Prior-art sweep: Psyche/nousnet deep dive, framework survey, verification landscape
- [x] Decision log locked (docs/DECISIONS.md)
- [x] Sim: Condorcet aggregation, attacks and stake ledger ported to real transformer gradients
- [x] Sim scenarios: honest baseline, sign-flip vs mean, sign-flip vs clip, ALIE vs clip, ALIE vs clip plus audit, non-IID honest FPR
- [x] Economy calibration: break-even bond vs audit rate on H100 market cost, 125M/1B/7B presets
- [ ] Landing page with manifesto and live sim charts (next session)
- [ ] Name lock: Leviathan vs alternatives, domain and handle check

## Phase 1, devnet core

- [ ] Fork PsycheFoundation/nousnet into wienerlabs, strip to coordinator + client + shared crates, build with Nix
- [ ] Read the coordinator crate end to end; map every state transition and the dead Ejected/slashed paths
- [ ] Anchor: bond account (deposit on join, challenge-window exit)
- [ ] Anchor: audit assignment from round seed (probability p, shuffled-index verifier committee)
- [ ] Anchor: dispute instruction with commitment evidence; committee verdict; slash routing (bounty to reporter, remainder to treasury); ejection that treasurer actually reads
- [ ] Rust verifier daemon: replay a sampled contribution from (checkpoint, seed, data), tolerance-band comparison, fraud proof submission
- [ ] Port centered-clip excision into the aggregation path as pre-filter
- [ ] Local 4-node swarm on one machine against devnet; nanoGPT-scale model through the full chain path
- [ ] Conviction demo capture: fabricated delta caught, slashed, ejected
- [ ] Anchor test suite green; two-GPU replay reproducibility check

## Phase 2, Genesis Run

- [ ] Tolerance band calibration harness across hardware classes (4090, 3090, A100, H100)
- [ ] One-line installer + wallet flow + bond funding UX
- [ ] Public site: live loss curve, node map, leaderboard, audit/slash feed
- [ ] Relay infrastructure for non-hole-punchable nodes
- [ ] Red-team bounty program design
- [ ] 350M run rehearsal with internal nodes, then 1B public run

## Phase 3, mainnet

- [ ] Legal review of token design
- [ ] TGE via Wiener Launchpad rails; distributor program reuse for airdrop and vesting
- [ ] Real-bond parameters from sim calibration; treasury and endowment wiring
- [ ] Inference v0: vLLM workers + TOPLOC validation + settlement program
- [ ] Arweave checkpoint lineage via zk-lokomotive rail

## Phase 4, scale

- [ ] DanteGPU supply integration
- [ ] 7B+ run planning
- [ ] Wienerpad futarchy market for next-model selection
- [ ] TEE attestation lane for datacenter suppliers (Blackwell CC)
