# Task list

## Phase 0, proof (this repo, done except where marked)

- [x] Prior-art sweep: Psyche/nousnet deep dive, framework survey, verification landscape
- [x] Decision log locked (docs/DECISIONS.md)
- [x] Sim: Condorcet aggregation, attacks and stake ledger ported to real transformer gradients
- [x] Sim scenarios: honest baseline, sign-flip vs mean, sign-flip vs clip, ALIE vs clip, ALIE vs clip plus audit, non-IID honest FPR
- [x] Economy calibration: break-even bond vs audit rate on H100 market cost, 125M/1B/7B presets
- [ ] Landing page with manifesto and live sim charts (next session)
- [~] Name lock: checklist in `docs/BRANDING.md`; final lock is owner decision

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
- [x] 1.9 Training swarm smoke on live devnet: the psyche-solana-client builds against the NousResearch tch fork (PyTorch 2.9.1 in a dedicated venv, LIBTORCH_USE_PYTORCH) and runs on MPS. A verified run: the client joined on-chain, downloaded Nano-Llama, trained a full epoch (17 rounds, loss descending from the ln(30) init baseline, 15 DisTrO-compressed gradients over iroh, 1 Join + 17 Witness + 33 Tick transactions coordinated by our devnet coordinator). Multi-epoch re-join resilience is Phase 2; the trainer, toolchain and on-chain coordination are proven end to end (docs-swarm-smoke.md in leviathan-net)
- [x] 1.10 Live devnet conviction: devnet-conviction-demo runs the whole security economics on live devnet through the toolbox RPC endpoint (run create, bond deposit read on-chain, real-time epoch driven by sleeps, treasurer run_slash CPI conviction, slashed counter read on-chain, bond finalize forfeiting the slashed amount into the run vault); the memnet suite proves the same loop deterministically (17/17). Two-GPU replay reproducibility folds into 1.9's swarm bring-up
- [ ] 1.p Parallel track: manifesto landing page, name finalization with domain and handle check

## Phase 2, Genesis Run

- [ ] Tolerance band calibration harness across hardware classes (4090, 3090, A100, H100)
- [ ] Two-GPU tolerance-band replay reproduction (Phase 1 exit criterion carried forward; folded into 1.9 but never run on two distinct GPUs)
- [x] Sim: within-band adversary budget scenario — `--band-sweep` runs a 5/16 coalition that biases against the honest mean at 0.9x the published band; explicit replay evidence shows the audit passes by construction (distance = 0.9 x band, fraud=false) at every band width, so aggregation is the only layer that pushes back. Measured over 30 rounds vs the 2.173 honest reference: +0.012 loss at band 0.02, +0.019 at 0.05 (the operating point, ~0.9%), +0.032 at 0.1, +0.063 at 0.2 — roughly linear in band width, coalition accepted 100% throughout (docs/assets/band_sweep.png)
- [~] Production verifier daemon: the decision core now lives in the substrate as the psyche-verifier crate (shared/verifier in leviathan-net): relative L2 distance, band verdicts, per-hardware calibration, sha256 fraud proofs matching the on-chain commitment, and a ReplayEngine trait with an audit_round orchestrator that convicts only the cheater in a mixed round, 13 tests. Remaining: plug the trainer in as the ReplayEngine (shares the 1.9 libtorch toolchain), read Committee::Verifier assignments from the coordinator, and submit run_slash
- [ ] Multi-epoch re-join resilience (deferred out of 1.9; prerequisite for any churn run)
- [x] Verifier economics: economy.py gains the zero-fraud projection (audit fee = 1.1x per-contribution H100 cost; treasury burn ~9.2% of rewards at p=0.1, preset-independent) and genesis_parameters() publishing the Genesis operating point (1B preset, p=0.1, band 0.05, bond = 9 rounds of reward); both emitted into results.json
- [x] Publish the centralized-dispute limitation copy (`docs/launch/GENESIS_DISCLOSURES.md`); dashboard wiring still open
- [ ] One-line installer + wallet flow + bond funding UX
- [ ] Public site: live loss curve, node map, leaderboard, audit/slash feed
- [ ] Relay infrastructure for non-hole-punchable nodes
- [x] SECURITY.md responsible-disclosure channel (GitHub private vulnerability reporting; economic-security breaks explicitly in scope)
- [x] Red-team bounty program design (`docs/REDTEAM_BOUNTY.md`, SECURITY.md linked; endowment funding is ops)
- [x] CI + tests: .github/workflows/ci.yml runs the sim suite on CPU torch; CONTRIBUTING.md documents setup
- [x] Rehearsal retro tooling: `scripts/analyze_telemetry.py` + `docs/RETRO_REHEARSAL.md` (current decision NO-GO for 1B)
- [x] Kill-switch monitoring design: `docs/ops/OPS_RUNBOOK.md`, `docs/ops/alerts/leviathan-killswitch.rules.yml`, `scripts/check_killswitches.py`
- [ ] LICENSE decision (owner call; blocks going public)
- [ ] 350M run rehearsal with internal nodes, then 1B public run
- [ ] Name lock: domains and branding (`docs/BRANDING.md` checklist; owner decision)

## Phase 3, mainnet

- [x] Legal review briefing packet for counsel (`docs/LEGAL_BRIEFING.md`); memo itself is counsel-gated
- [x] Audit prep package (`docs/AUDIT_PREP.md`); external report is budget/schedule-gated
- [x] Tokenomics and TGE design (`docs/TOKENOMICS.md`, `docs/assets/tokenomics.json` from economy.py); final numbers wait on counsel
- [x] Mainnet deploy runbook (`docs/launch/MAINNET_DEPLOY.md`); execution gated on audit + legal + tokenomics
- [x] Genesis launch checklist and disclosures (`docs/launch/GENESIS_LAUNCH.md`, `GENESIS_DISCLOSURES.md`)
- [ ] Round randomness hardening: VRF or recent-blockhash commitment replacing sha256(unix_timestamp, slot) (grindable, flagged in CODEMAP.md)
- [ ] Bonded multi-verifier dispute committee with reporter bounty and treasury remainder, replacing the main_authority resolver (evolution locked in 1.6)
- [ ] Regenerate program keypairs for mainnet (devnet keypairs live in private repo history, devnet-only per CODEMAP.md)
- [ ] TGE directly on Solana rails; distributor program for airdrop and vesting
- [ ] Real-bond parameters from sim calibration; treasury and endowment wiring
- [ ] Inference v0: vLLM workers + TOPLOC validation + settlement program
- [ ] Arweave checkpoint lineage via zk-lokomotive rail

## Phase 4, scale

- [ ] DanteGPU supply integration
- [ ] 7B+ run planning
- [ ] Wienerpad futarchy market for next-model selection
- [ ] TEE attestation lane for datacenter suppliers (Blackwell CC)
- [ ] Monitoring stack production deploy and on-call rotation (design in docs/ops)
