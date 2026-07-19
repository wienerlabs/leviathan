# Decision log

Locked 2026-07-19 after a three-track prior-art sweep (Psyche deep dive, framework survey, verification landscape). Each decision names the alternative it rejects and the evidence behind it.

## D1: Fork PsycheFoundation/nousnet as the network substrate

The Psyche monorepo (renamed nousnet, Apache-2.0, no CLA) already contains the production shape of this project: Anchor programs for coordinator, authorizer, treasurer, mining pool and distributor, a Rust node daemon, iroh P2P (ed25519 NodeIds, ~90% direct connection rate via hole punching, iroh-gossip metadata, iroh-blobs transfers), a licensed Rust DisTrO implementation (DCT top-k + 1-bit sign), and a chainless centralized backend for local development. It is proven in production: Hermes 4.3 (36B) was post-trained end to end on Psyche at 144k tok/s across 24 nodes and beat the centrally trained control run.

Rejected alternatives: building from scratch (months of undifferentiated work), hivemind (libp2p ~70% NAT success vs iroh ~90%, packaging-only maintenance since 2023), prime-diloco (frozen since April 2025, no chain layer). From prime-diloco we still lift two patterns where Psyche is thin: ElasticDeviceMesh fault-tolerant process groups and peer checkpoint recovery.

Risk priced in: upstream has been quiet since 2026-03-24. We own the fork; we do not ride upstream.

## D2: The security layer is ours: bonded contributions, random replay audits, slashing

This is the differentiation, verified against the Psyche codebase itself:

- `Committee::Verifier => todo!()` in `shared/coordinator/src/coordinator.rs`
- `data_selection.rs` asserts `verification_percent == 0`
- witnesses attest participation via bloom filters, not correctness
- the `slashed` counter is dead code: no path sets `ClientState::Ejected`, and `participant_claim` never reads `slashed`
- sybil resistance in practice is a whitelist held by the run authority

Psyche's own docs call gradient verification an open problem. OVIG (arXiv 2606.21045, June 2026) closes it academically with exactly our loop: bonded commitments, sampled replay with calibrated tolerance bands that survive heterogeneous-hardware drift, slashing, at 1.143x total overhead and 0% attack success in evaluation. Condorcet (wienerlabs/condorcet) supplies the other two layers: centered clipping with far-outlier excision as the damage bound between audits, and the break-even bond economics bond = reward x (1-p)/p. BTARD (Secure Distributed Training at Scale) is the precedent for CenterClip-style defense in real swarm pretraining; HIDRA is the caveat that high-dimensional shortcuts reopen the arms race, which is why audits and bonds back the aggregator instead of trusting it alone.

Nobody runs this combination live today. Bittensor subnets chose economics without verification guarantees (Templar Gauntlet admits undetected-malice and first-strike gaps; IOTA spot-checks but only withholds emissions). Gensyn chose verification without live economics (Verde needs bitwise determinism via RepOps at 30-130% overhead, FP32, single GPU, pre-mainnet). Psyche chose neither.

## D3: Compression recipe: DiLoCo outer loop + SparseLoCo

SparseLoCo (MIT, one-covenant/SparseLoCo) layers chunked top-k at 1-2% density with 2-bit quantization and error feedback on top of DiLoCo outer steps. At 1B scale this takes a sync payload to roughly 15-40 MB, under 1 Mbps sustained on home broadband, which is what makes a volunteer swarm real. Covenant-72B (Templar) and Consilience-40B prove the transport math holds at 40B to 72B.

Do not vendor bloc97/DeMo: the repo has no license file. Psyche's Apache-2.0 Rust DisTrO is the licensed equivalent and ships in the fork.

## D4: Inference network: vLLM workers + TOPLOC + Solana settlement, not Petals

Petals is unmaintained (last commit August 2024, public swarm monitor down). The 2026 production pattern is whole-model vLLM workers with TOPLOC activation commitments (MIT, actively maintained validator, <1% prover overhead, ~100x cheaper validation than re-inference) settling through our Solana programs. Petals' MIT layer-sharding ideas remain salvage material if models ever exceed single-volunteer capacity.

## D5: Chain posture: Solana mainnet, permissionless, bond as the price of sybil

Psyche stayed on devnet with a whitelist; its mainnet footprint is a USDC mining pool. Our thesis is economic permissionlessness: anyone joins by posting a bond sized so that expected slashing exceeds expected cheating gain at audit rate p, and a slashed identity cannot re-enter free because the bond is the identity cost. Solana is the only L1 where round-level commitments plus instant micro-rewards are economically sane (400ms slots, sub-cent fees), and it composes with the existing Wiener stack (DanteGPU supply, Wienerpad futarchy, zk-lokomotive Arweave rail).

## D6: Honest claims policy

We claim economic security, never cryptographic proof. The published dashboard carries the uncaught-cheat rate implied by the audit probability, the tolerance band width (which is the adversary's safe cheating margin), and the bond break-even curve. Marketing follows the same rule: the goal of the first runs is not a frontier model, it is the People's path to one, proven at 125M then 1B then 7B.
