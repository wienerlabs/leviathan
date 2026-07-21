# Mainnet Genesis Run and public launch

Issue #8. End-state: a public model trained by a permissionless bonded swarm on
mainnet with money at stake. This document is the launch checklist. It does not
assert that launch has occurred.

## Dependencies (all required)

| Gate | Issue / artifact |
|---|---|
| Security audit closed | #4 / `docs/AUDIT_PREP.md` |
| Legal structure | #5 / counsel memo |
| Tokenomics lock | #6 / `docs/TOKENOMICS.md` |
| Mainnet deploy | #7 / `docs/launch/MAINNET_DEPLOY.md` |
| Monitoring on-call | #9 / `docs/ops/OPS_RUNBOOK.md` |
| 1B go decision | #3 / `docs/RETRO_REHEARSAL.md` must be GO |
| Red-team program live | #2 / `docs/REDTEAM_BOUNTY.md` + funded endowment |
| Name / branding lock | #10 / `docs/BRANDING.md` |

Current retro decision is **NO-GO** until Phase 2 structural gates pass
(two-GPU calibration, 350M rehearsal, verifier daemon live slash, etc.).

## Public launch surface

1. **Permissionless bonded join**: one-line installer, wallet, bond deposit,
   client join against mainnet coordinator.
2. **Live dashboard**: loss curve, node map, leaderboard, audit/slash feed,
   disclosures from `docs/launch/GENESIS_DISCLOSURES.md`.
3. **Real payouts**: treasurer claims in collateral or post-TGE token per legal.
4. **Active red team**: public bounty brief + non-zero `slash_bounty_bps`.

## Launch day sequence

1. Confirm all gates green in a written go memo signed by eng + ops + counsel.
2. Unpause flagship mainnet run.
3. Open join docs and dashboard.
4. Seed 3+ internal bonded nodes and 1 verifier for liveness.
5. Announce red-team program.
6. On-call rotation starts (see ops runbook).
7. First 24h: no parameter changes except emergency pause.

## Kill criteria (immediate pause)

- Uncaught fraud class A confirmed (see red-team classes)
- Treasury drain alert without corresponding legitimate claims
- Mesh partition lasting beyond SLA with progressing epochs still paying
- Honest-node mass slash (FPR failure)
- Multisig or upgrade key compromise

## Acceptance mapping (issue #8)

| Criterion | Status |
|---|---|
| Public model trained by bonded swarm on mainnet | Blocked on all gates |
| Money at stake | Blocked |
| Checklist | This file |
