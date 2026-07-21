# Red-team bounty program

Issue #2. Published schedule for paid breaks against the Leviathan trust machine.
Parameters below are derived from the live sim (`sim/leviathan_sim/economy.py`),
on-chain treasurer fields (`slash_bounty_bps`), and the Phase 0 results in
`docs/assets/`. This is the program design; treasury funding and public
publication are operational steps, not design gaps.

## Scope of a break

A paid break is a reproducible procedure that, against a live or memnet-equivalent
run with the published operating point, achieves one of:

| Class | Definition | Evidence required |
|---|---|---|
| A. Undetected fraud past the band | Submit work that is not the honest replay of `(checkpoint, seed, shard)`, with relative L2 distance strictly greater than the published band, and receive reward without conviction for more than `2 / p` rounds | Trace of commitments, replay distances, chain settlement, and the audit lottery seed that failed to convict |
| B. Bond recovery without exposure | Recover bonded collateral after conviction, or withdraw without surviving the challenge window, or finalise a withdraw that should have forfeited | On-chain transaction sequence against the treasurer |
| C. Aggregation poisoning past excision | With a coalition strictly smaller than the excision threshold, move final validation loss by more than the published within-band budget for the operating band | Swarm config, coalition size, loss curves vs honest reference, aggregator keep-mask |
| D. Lottery grind | Bias `get_random_seed` or audit assignment so that a persistent cheater's catch time is statistically worse than `1/p` at p < 0.05 under the published shuffle | Seed sequence, assignment logs, hypothesis test |
| E. Economic free lunch | Positive expected value for fraud at the published `(p, bond, slash, reward)` operating point | Closed-form or Monte Carlo against the published ledger rules |

Out of scope: DoS against public RPCs, social engineering of the run authority keys,
breaks that require the authority's own keys, and items already listed as known
limitations in `docs/GAPS.md` unless the report sharpens a limitation into a
concrete, paid-tier exploit.

## Operating point under test

From `genesis_parameters()` at the 1B preset (see `docs/assets/results.json` and
`sim/leviathan_sim/economy.py`):

| Parameter | Value |
|---|---|
| Audit probability `p` | 0.1 (`verification_percent = 10`) |
| Tolerance band | 0.05 relative L2 |
| Round reward (H100-anchored) | ~$0.288 |
| Break-even bond | ~$2.59 (9 rounds of reward) |
| Expected rounds to catch | 10 |
| Within-band damage budget (5/16 coalition) | +0.019 final loss (~0.9% of 2.173 reference) |
| On-chain reporter share | `Run.slash_bounty_bps` (default design: 5000 = 50%) |

Sim anchors used for severity calibration:

- Honest mean final loss: 2.175
- Sign-flip vs mean: diverges to 12.0
- Sign-flip vs clip+excision: 2.203, malicious acceptance ~3%
- ALIE vs clip+audit p=0.1: all 5 cheaters caught, mean catch 9.8 rounds
- Verifier at band 0.05: 0 honest false positives, 3/3 cheater classes caught

## Reward tiers

Tiers are denominated in USDC (or the collateral mint before TGE) and funded from
the run treasury plus a standing red-team endowment. Amounts scale with how much
economic security the break destroys.

| Tier | Break class | Payout | Cap per report |
|---|---|---|---|
| Critical | B (bond theft / free withdraw), E with EV > reward per round | $25,000 | $50,000 |
| High | A with uncaught fraud beyond `2/p` rounds, D with p-value < 0.01 | $10,000 | $25,000 |
| Medium | C above published band damage, A caught late but after `1/p` | $3,000 | $10,000 |
| Low | Hardening of known limitations, sim claim errors, band calibration misses | $500 | $2,000 |
| In-protocol | Live conviction via fraud proof on a funded run | `slash_bounty_bps` of forfeited bond | per event |

In-protocol bounties are paid automatically by the treasurer on
`participant_bond_finalize_withdraw` when `slash_bounty_bps > 0` and a reporter
ATA is supplied. Off-protocol tiers are paid after triage.

Recommended default before the 1B public run: set `slash_bounty_bps = 5000`
(50% to reporter, 50% retained in the run vault), matching
`EconomyConfig.slash_bounty_fraction = 0.5`.

## Disclosure process

1. Report via GitHub private vulnerability reporting on `wienerlabs/leviathan`
   (and `wienerlabs/leviathan-net` for substrate bugs). Do not open a public issue
   for exploitable findings.
2. Acknowledgement within 72 hours. Severity assignment within 7 days using the
   table above.
3. Fix or public mitigation target: Critical 14 days, High 30 days, Medium 60 days.
4. Coordinated disclosure: reporter may publish 7 days after the fix ships, or
   90 days after report if no fix, whichever comes first, unless both sides agree
   to extend.
5. Credit in release notes and in this document's hall of fame, unless the
   reporter opts out.
6. Duplicate reports: first clear reproduction wins. Partial credit for
   independent parallel reports at maintainer discretion.

## Eligibility

- Anyone not currently employed by Wiener Labs or holding upgrade authority keys
  for the programs under test.
- No legal action against good-faith research that stays inside this policy and
  does not target third-party infrastructure.
- Testnet and memnet first. Mainnet red-teaming requires written approval after
  Phase 4 programs are live, and must use designated runs only.

## Publication gate for the 1B run

The 1B public run does not start until:

1. This document is linked from `SECURITY.md` and the public site.
2. Treasury endowment for at least one Critical + one High payout is reserved.
3. `slash_bounty_bps` is set non-zero on the flagship run.
4. The centralized `main_authority` slash path is disclosed on the dashboard
   (see `docs/GAPS.md` and `docs/launch/GENESIS_DISCLOSURES.md`).

## Acceptance mapping (issue #2)

| Acceptance criterion | Status |
|---|---|
| Published red-team brief | This document |
| Bounty schedule before 1B run | Tiers table above |
| Break definitions | Classes A-E |
| Disclosure process | Section above |
| Funded endowment | Operational (ops), tracked in `docs/ops/OPS_RUNBOOK.md` |
