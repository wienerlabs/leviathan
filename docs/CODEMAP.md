# Code map: leviathan-net (nousnet fork)

Distilled from the three-track deep read of 2026-07-19. File:line references are against wienerlabs/leviathan-net at fork point 0bdb13d9. This is the working reference for Phase 1; update it as the fork diverges.

## Layout

- `shared/coordinator` (psyche-coordinator): the pure state machine, no funds, no I/O. Wrapped on-chain by the Anchor coordinator and off-chain by the centralized server. Everything consensus-critical lives in `coordinator.rs` (1292 lines).
- `architectures/decentralized/solana-*`: five Anchor programs (coordinator, authorizer, treasurer, mining-pool, distributor) + solana-client (node CLI) + solana-tooling (memnet test harness).
- `shared/client`: architecture-agnostic trainer state machine. `shared/modeling`: tch trainer + DisTrO. `shared/network`: iroh gossip/blobs/model-sharing.
- `architectures/centralized`: chainless server/client/local-testnet for development.

## State machine

`RunState` at coordinator.rs:47: Uninitialized, WaitingForMembers, Warmup, RoundTrain, RoundWitness, Cooldown, Finished, Paused. Advanced by permissionless `tick(new_clients, unix_timestamp, random_seed)` at coordinator.rs:437. Round ring buffer holds 4 rounds (NUM_STORED_ROUNDS, :237). Epoch rates promote at warmup start (instance_state.rs:119). Rewards and slashes mutate only inside tick's EpochEnd branch (instance_state.rs:130-170).

## Dead code we bring to life (confirmed file:line)

| What | Where | State |
|---|---|---|
| Verifier health dispatch | coordinator.rs:702 `Committee::Verifier => todo!()` (TieBreaker :701 same) | panics if reached |
| Verifier data assignment | data_selection.rs:23 `assert_eq!(config.verification_percent, 0)` | asserts the feature off |
| ClientState::Ejected | defined coordinator.rs:79; compared instance_state.rs:160 | no code path ever sets it |
| slashed increment | instance_state.rs:162, only inside the Ejected branch | unreachable |
| slashed read | nowhere: treasurer participant_claim.rs:79 reads only `earned` | payouts ignore slashing |

Wiring order: implement the Verifier arm in `healthy()`, drop the data_selection assert, add the code path that sets Ejected on conviction, extend the treasurer to read `slashed` at settlement. The `verification_percent` config field (coordinator.rs:261) and the Verifier committee partition (committee_selection.rs:164-172) already exist upstream; the seam was designed and left empty.

## Audit assignment substrate

`CommitteeSelection` (committee_selection.rs): ETH2-style swap-or-not shuffle (shared/core/src/swap_or_not.rs:5, 90 rounds, sha256), salts "witness"/"committee", seeded from `round.random_seed`. `from_coordinator(coordinator, offset)` supports current and previous rounds. Verification helpers `verify_committee_for_client` (:181) are unit-tested. Audit lottery = a third salt and a probability check over the same shuffle.

Round seed source (authoritative, on-chain): `get_random_seed(clock)` = sha256(unix_timestamp, slot) at instance_state.rs:76. Weak randomness: a leader can grind slot timing. Acceptable for Phase 1 devnet; hardening (VRF or recent-blockhash commitment) goes on the mainnet checklist.

## Bond design decision

Coordinator account is zero_copy + Pod + VERSION=1 with strict size checks (lib.rs:69-124): any layout growth is a versioned migration. Custody already lives in the treasurer (Run PDA + run_collateral ATA) and mining pool. Therefore:

- Bond custody goes in the treasurer: new instructions `participant_deposit_bond` (copy lender_deposit.rs:55-87 mechanics), `participant_withdraw_bond` and `participant_settle` (copy participant_claim.rs:102-115 PDA-signed transfer out), new `Participant.bonded_amount` field (Borsh account, cheap to grow), `Run.total_bonded_amount`.
- Settlement is the first code that reads both `earned` and `slashed` (same read path as participant_claim.rs:69-82), reducing the refundable bond by a function of slashed.
- Join-time enforcement: `Client._unused: [u8; 8]` (client.rs:28) becomes `bonded: u64`, the single 8-byte slot that avoids a coordinator account resize; join_run (logic/join_run.rs:49, instance_state.rs:335) gains the bond check next to the existing authorization gate.

## Trainer and commitment path

Assignment: train.rs:155-260 builds CommitteeSelection, extracts client/committee/witness proofs; data via assign_data_for_state (data_selection.rs:8) with deterministic_shuffle by round seed. Compute: shared/modeling/src/trainer.rs (LocalTrainer::train :586). DisTrO: distro.rs (generate :505, DCT top-k compress :345, 1-bit sign :687). Commitment: sha256 over step, batch bounds, sparse idx/val bytes at serialized_distro.rs:33 (method name is misspelled `comptue_hash`: grep accordingly), signed at client.rs:466, broadcast via iroh-gossip with a second SignedMessage layer (network/lib.rs:568), blob via iroh-blobs add_downloadable (lib.rs:635). Peers verify hash equality on download at steps.rs:607-620.

## Determinism inventory (verifier design input)

Deterministic on the decentralized path: on-chain seed (reproducible from chain history), node/data shuffle, ChaCha8 seeded data shuffle (run-level `shuffle_seed` in data.toml), fixed tch::manual_seed(1337) at init.rs:191, no dropout anywhere in models, deterministic DisTrO arithmetic.

Nondeterminism sources to absorb in the tolerance band:
1. GPU kernels, notably decompress `scatter_reduce_("mean")` at distro.rs:392 (atomic, nondeterministic)
2. bf16 casts on model sharing (trainer.rs:362)
3. Data-parallel reduce order (trainer.rs:1169); fp32 grad accumulator (trainer.rs:830) partially mitigates
4. Centralized backend seeds from rand::rng() (server/app.rs:507): not replayable, decentralized path only for audits
5. MPS fallback kernels differ from CUDA/CPU

## Verifier daemon building blocks (already upstream)

- `--write-gradients-dir` CLI (cli.rs:128) dumps per-round results to disk: ready-made offline replay input
- tools/rust-tools/expand-distro: standalone binary reading serialized results and decompressing: precedent and skeleton for the verifier CLI
- tools/rust-tools/observer + shared/event-sourcing: daemon precedent
- Shape: new tools/rust-tools binary or a psyche-client mode subscribing as Committee::Verifier, recomputing an assigned batch from (checkpoint, seed, data_index) with LocalTrainer + Distro, comparing within the band, submitting the fraud proof

## Build, test, run

- cargo check green on this machine: psyche-coordinator, psyche-core (54s cold), solana-coordinator, treasurer, authorizer (18s)
- memnet suite: `cargo test -p psyche-solana-tooling`: 14/14 in 0.93s, in-process, no validator. TDD substrate for our instructions. Reference flow: memnet_coordinator_rewards.rs (240 clients, full epoch, asserts earned split)
- anchor build per program via justfile; Nix path exists but Nix is not installed here; deploy scripts at architectures/decentralized/justfile (localnet/devnet, with or without treasurer)
- Centralized local-testnet needs tmux (not installed yet) and libtorch (LIBTORCH_USE_PYTORCH=1 plus DYLD_LIBRARY_PATH to a venv torch/lib on macOS; sim/.venv has torch 2.13, tch-fork compatibility unverified). Dummy path exists: Checkpoint::Dummy + DummyDataProvider + DummyModel (init.rs:215-291); candidate configs under config/test and config/solana-test
- Anchor pinned to git rev a7a23eea (0.30.1 line); program IDs come from declare_id!, Anchor.toml has no programs map

## Devnet deployment, 2026-07-19

| program | id |
|---|---|
| coordinator | JD9rHTiqBFgHjViWZc7gFZX74LvKKysbLbqFRaFvtmmN |
| authorizer | 2Kg5ERG6ubuzyPmQ24axsws7V2ja2EvWp5CHMKFCrTxv |
| treasurer | 9A1kc8Dr9dFJW9t1npAk7EHrADm6TAyFeVLH27CDdvv8 |

Collateral mint BWLv1Fj5RKJbcr3ZMLVKhviFq1i3tq6afgVS2ngyot3X (0 decimals, 1M minted). Deploy wallet and upgrade authority HYXmvGi8SFn7GdGLA2m7YVUxqqwv3rYy7wYhwZ4EoaYn (devnet-only wallet, keypair at ~/.config/solana/leviathan-devnet.json). Program keypairs backed up at ~/.config/solana/leviathan-program-keys/. Run leviathan-dev created permissionless through the treasurer CPI path (rewards topped up, earning 10 / slashing 10 future epoch rates, light config, resumed) and sits in WaitingForMembers.

Deploy recipe: `RUN_ID=... KEY_FILE=... RPC=https://api.devnet.solana.com WS_RPC=wss://api.devnet.solana.com ./scripts/deploy-solana-test.sh --treasurer` then `TREASURER_ARGS="--treasurer-collateral-mint <mint>" ./scripts/create-permissionless-run.sh --treasurer` with the same env. Builds use --no-idl (anchor idl generation trips over a proc-macro2 toolchain mismatch; host cargo check and memnet tests are unaffected). Mainnet gets freshly generated program IDs; these devnet keypairs live in the private repo history, acceptable for devnet only.

Upstream IDs for reference: coordinator 4SHugWq..., authorizer PsyAUmhp..., treasurer EnU7DRx..., mining-pool CQy5JKR2..., distributor GQEX84La...
