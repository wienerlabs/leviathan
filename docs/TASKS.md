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

Exit criteria: recorded end-to-end conviction demo, anchor test suite green, two-GPU tolerance-band replay reproduced.

- [x] 1.1 Fork bootstrap: private mirror wienerlabs/leviathan-net live, upstream remote wired, chain-side crates compile clean, memnet suite 14/14 in 0.93s (libtorch-dependent centralized smoke folded into the 1.9 prerequisite)
- [x] 1.2 Code map: docs/CODEMAP.md distills the three-track deep read; dead-code inventory confirmed at file:line, bond attach decision locked (treasurer custody + Client._unused slot)
- [x] 1.3 Devnet deploy under our own program IDs: coordinator JD9rHTiqBFgHjViWZc7gFZX74LvKKysbLbqFRaFvtmmN, authorizer 2Kg5ERG6ubuzyPmQ24axsws7V2ja2EvWp5CHMKFCrTxv, treasurer 9A1kc8Dr9dFJW9t1npAk7EHrADm6TAyFeVLH27CDdvv8, collateral mint BWLv1Fj5RKJbcr3ZMLVKhviFq1i3tq6afgVS2ngyot3X; permissionless run leviathan-dev live in WaitingForMembers via the treasurer CPI path
- [x] 1.4 Bond custody in the treasurer: Participant.bond_amount plus withdraw pending state and settled slashed points, Run bond totals plus withdraw delay; run_bond_config_update, participant_bond_deposit, participant_bond_request_withdraw, participant_bond_finalize_withdraw; finalize settles coordinator slashed points against the bond (forfeits stay in the run vault); memnet_treasurer_bond green, tooling suite 15/15 (devnet redeploy of the treasurer folds into the next deploy batch since account layouts grew)
- [x] 1.5 Audit lottery: shared/coordinator/audit_selection derives verifier-to-target assignments from the round seed via a third salt over the existing swap-or-not shuffle; audit pressure scales with verification_percent (the Verifier committee partition upstream already computed), each verifier draws one target from the round's data assignment, deterministic and replayable; verification_percent==0 assert dropped, Verifier arm in healthy() unblocked; 20/20 coordinator tests, memnet still 15/15
- [x] 1.6 Dispute and slash: coordinator core eject(index) sets Ejected (Healthy/Dropped -> Ejected), carried into exited_clients where the epoch-end slashing rate finally applies; on-chain slash_client is main_authority gated (the dispute resolver records the off-chain verifier verdict, Phase 3 evolves it into a bonded multi-verifier vote with reporter bounty and treasury remainder) and logs the committed-vs-replayed fraud proof; memnet_coordinator_slash proves the loop end to end (stranger rejected, cheater slashed and earns nothing, honest clients untouched); the slashed counter now has a live producer feeding the treasurer settlement from 1.4. Tooling 16/16, coordinator 20/20
- [x] 1.7 Aggregation adaptation: sim gains chunked top-k + 1-bit-sign compression (2% density); dense vs sparse re-run shows the sign-flip coalition rejected even harder under compression (malicious selection 0.03 -> 0.00) and ALIE still passed to the audit layer in both, at ~0.7 loss cost for a ~50x bandwidth cut. Clip+excision holds in the transport domain
- [x] 1.8 Verifier core: verifier.py replays a contribution from (checkpoint, seed, shard) and scores relative L2 distance; the --verify experiment separates 1% cross-hardware drift (0.010, passes) from sign-flip (6.0), gaussian (1.35) and lazy (1.0), all caught, zero honest false positives at band 0.05. This is the daemon's decision core; the production daemon (subscribe as Verifier, replay real gradients, call run_slash) shares the libtorch prerequisite with 1.9
- [ ] 1.9 Four-process local swarm against devnet with a fabricated-delta malicious mode (prereq: tmux install plus libtorch env, LIBTORCH_USE_PYTORCH=1 with DYLD_LIBRARY_PATH to a venv torch/lib, tch-fork compatibility check, dummy-config smoke first)
- [x] 1.10 Live devnet conviction: devnet-conviction-demo runs the whole security economics on live devnet through the toolbox RPC endpoint (run create, bond deposit read on-chain, real-time epoch driven by sleeps, treasurer run_slash CPI conviction, slashed counter read on-chain, bond finalize forfeiting the slashed amount into the run vault); the memnet suite proves the same loop deterministically (17/17). Two-GPU replay reproducibility folds into 1.9's swarm bring-up
- [ ] 1.p Parallel track: manifesto landing page, name finalization with domain and handle check

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
