# Genesis dashboard disclosures

Public text for the Genesis / mainnet dashboard. Copy is sentence case per Wiener
Labs UI rules. Do not present economic security as cryptographic proof.

## Required disclosures

### Centralized dispute authority (until Phase 3)

Slash decisions are currently executed by the run main authority recording an
off-chain verifier verdict on chain. A bonded multi-verifier dispute committee
with reporter bounty is planned for Phase 3. Until then, fraud proofs are
transparent on chain, but the final slash transaction is authority-gated.

### Economic security, not cryptographic proof

Leviathan prices lying with bonds, random replay audits, and robust aggregation.
The uncaught-cheat rate, tolerance band width, and bond curve are public metrics.
They are not zero and are not claimed to be zero.

### Operating point

| Metric | Value |
|---|---|
| Audit probability | 0.1 |
| Tolerance band (relative L2) | 0.05 |
| Expected rounds to catch a persistent cheater | 10 |
| Within-band damage budget (5/16 coalition, sim) | +0.019 final loss (~0.9%) |
| Break-even bond | 9 rounds of reward at p=0.1 |

### Randomness limitation

Round seeds are derived from on-chain clock material and are grindable by a
leader at the margin. Hardening (VRF or recent-blockhash commitment) is on the
mainnet Phase 3 ladder.

### Red team

Active bounty program: see `docs/REDTEAM_BOUNTY.md` and `SECURITY.md`.
