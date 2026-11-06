# External security audit preparation

Issue #4. This package prepares for an independent audit. It is **not** an audit
report and does not claim findings are resolved. Acceptance for #4 remains:
external report with critical and high findings closed.

## In-scope programs (leviathan-net)

| Program | Role | Devnet ID (not for mainnet) |
|---|---|---|
| Coordinator | Rounds, audit lottery, eject/slash counters | `GdHJHiQp7uMv8TanfpaCaKQ8nHm5suvEt9JvjpZFWZ19` |
| Treasurer | Bonds, withdraw challenge, slash settle, bounty bps | `Fq1Mv8osXqHxiiXjm4yhvQGE5wgx9QMueK8n2qwbqovV` |
| Authorizer | Join authorization | `ECEmta24U9WCwh397N4diSc8JnAbyJTG3YiTUVL5umrb` |

Mainnet must use freshly generated program keypairs (see `docs/launch/MAINNET_DEPLOY.md`).

## Economic model in scope

- Bond size law: `reward * (1-p)/p` (`sim/leviathan_sim/economy.py`) is the deterrence floor; the required bond is the larger of that and the verifier-sustainable bond (`docs/COMMITTEE_ECONOMICS.md`)
- Audit probability from `verification_percent`
- Tolerance band 0.05 operating point and within-band damage budget
- `slash_bounty_bps` reporter share on forfeit
- Zero-fraud treasury burn projection (~8.15% of rewards at p=0.1 with 1.35x reward margin)

## Attachments for the auditor

1. `docs/WHITEPAPER.md` security and economics
2. `docs/ARCHITECTURE.md` round lifecycle
3. `docs/CODEMAP.md` file:line inventory and known dead-code history
4. `docs/GAPS.md` known limitations (must not be re-discovered as "surprises")
5. `docs/REDTEAM_BOUNTY.md` break classes A-E
6. Memnet suites in `leviathan-net` (bond, slash, settle, bounty, full epoch)
7. `devnet-conviction-demo` capture notes
8. Sim results under `docs/assets/`

## Self-review checklist (pre-audit)

Run from a clean checkout of both repos:

```
# leviathan (this repo)
cd sim && uv sync && uv run pytest -q

# leviathan-net
cargo test -p psyche-solana-tooling
cargo test -p psyche-verifier
cargo test -p leviathan-indexer
```

Manual review axes (for internal prep, not a substitute for the audit):

| Axis | What to verify |
|---|---|
| Authority | Only intended signers move bonds, slash, config |
| PDA seeds | Run, participant, vault ATAs cannot be confused |
| Settlement math | Slashed points reduce refundable bond; bounty <= forfeit |
| Audit lottery | Assignments deterministic from round seed; no off-by-one |
| Integer overflow | Bond, bounty bps, earned/slashed accumulators |
| Account resize / version | Coordinator zero_copy VERSION constraints |
| Randomness | Document grindability of `sha256(timestamp, slot)` as known Phase 3 item |
| Upgrade path | Mainnet upgrade authority is multisig only |

## Known limitations to disclose in the engagement letter

1. `slash_client` is `main_authority` gated until multi-verifier committee (Phase 3).
2. Round seed is grindable by a leader; VRF hardening is Phase 3.
3. Tolerance band not yet calibrated across GPU classes.
4. Production verifier daemon live `run_slash` path still completing.

## Engagement status

| Item | Status |
|---|---|
| Scope document | This file |
| Budget / auditor selection | Owner + finance (external) |
| Signed engagement | Not started |
| Audit report | Not started |
| Critical/high remediation | N/A until report |

## Acceptance mapping (issue #4)

| Criterion | Status |
|---|---|
| Independent audit | Blocked on budget and scheduling |
| Critical/high resolved | Blocked on audit |
| Prep package | Delivered here |
