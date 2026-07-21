# Tokenomics and TGE design

Issue #6. Design consistent with the economic model already coded in
`sim/leviathan_sim/economy.py` and the whitepaper economics section. This is an
engineering and product design document. It is not a legal opinion. Issue #5
(counsel review) gates any public token offer.

## Design goals

1. Pay for accepted learning work (Proof of Gradient), not for raw hash power.
2. Keep fraud expected-negative at the published `(p, bond, reward)` point.
3. Fund continuous audit pressure even in the zero-fraud equilibrium.
4. Avoid yield promises. Utility is access to training rewards, governance of
   run selection, and (later) inference settlement.
5. Stay compatible with a compliant launch structure after legal review.

## Units

| Unit | Role | Issued by |
|---|---|---|
| Collateral (mainnet mint, TBD) | Bond deposits, slash forfeiture, optional reward redemption | External mint or network stable collateral |
| PoG points | Per-epoch earned counter on the coordinator, already live on devnet | Coordinator epoch settlement |
| Network token (symbol TBD, working name LEV) | Long-term reward and governance unit after TGE | Mint authority under multisig |

Before TGE, testnet and genesis rehearsal pay only in the testnet collateral mint
(`BWLv1Fj5RKJbcr3ZMLVKhviFq1i3tq6afgVS2ngyot3X` on devnet). PoG points convert
to collateral through the treasurer claim path already deployed.

## Operating economics (coded, not invented)

From `genesis_parameters()` and `calibration_table()`:

| Preset | Round cost (H100) | Round reward (1.2x) | Bond at p=0.1 | Expected catch rounds |
|---|---|---|---|---|
| 125M proof | $0.0120 | $0.0144 | $0.129 | 10 |
| 1B genesis | $0.240 | $0.288 | $2.59 | 10 |
| 7B scale | $3.36 | $4.03 | $36.25 | 10 |

Break-even law (implemented in `break_even_bond`):

```
bond = reward * (1 - p) / p
```

Zero-fraud audit burn (`audit_burn_projection`, fee = 1.1x H100 cost):

| Preset at p=0.1, 100 workers | Audit fee / contribution | Treasury burn / round | Burn share of rewards |
|---|---|---|---|
| 1B genesis | $0.264 | $2.64 | 9.17% |

This is the sustained cost of security when nobody is cheating. The treasury must
be sized for it.

## Supply sketch (pre-legal, adjustable)

Working totals for modelling only. Counsel may require structural change.

| Allocation | Share | Vesting | Purpose |
|---|---|---|---|
| Training rewards endowment | 35% | Emission over multi-year PoG schedule | Pay accepted work |
| Audit / security treasury | 15% | Continuous draw for audit fees + red-team bounties | Fund p=0.1 pressure and issue #2 bounties |
| Ecosystem / grants | 10% | Multisig, milestone grants | Tooling, relays, research |
| Team | 25% | 1y cliff, 3y linear | Build and operate |
| Early contributors / community | 10% | TGE unlock + short vest | Genesis participants, bug bounties |
| Liquidity / market making | 5% | At TGE under multisig policy | CEX/DEX depth if pursued |

Emission is not a fixed block subsidy. Each run configures epoch earning rates on
the coordinator; the treasury tops up the run vault. Unused endowment stays
unminted or locked, never inflated ad hoc.

## PoG to token conversion

1. Trainer stays Healthy through an epoch and accrues `earned` points (existing
   coordinator behaviour).
2. Treasurer `participant_claim` redeems points for collateral while the run is
   collateral-denominated.
3. After TGE, a conversion rate is fixed per run at run-create time:
   `tokens_per_point = run_reward_budget / expected_total_points`.
4. Slashed points reduce redeemable balance (already wired:
   bond finalize forfeits into the vault; claim path must continue to respect
   `slashed`).
5. No retroactive reprice of settled claims.

## Bond, slash, bounty

| Mechanism | Parameter | Source of truth |
|---|---|---|
| Bond size | >= break-even at published p | `Run` bond config + sim table |
| Audit probability | `verification_percent / 100` | Coordinator config |
| Slash on conviction | Earned points + bond forfeit path | Coordinator eject + treasurer settle |
| Reporter bounty | `slash_bounty_bps` of forfeited bond | Treasurer, default design 5000 |
| Challenge window | Withdraw delay on bond request | Treasurer withdraw instructions |

## TGE plan

Phases, each gated:

1. **Legal structure lock** (issue #5). Entity, jurisdiction, token
   classification, KYC/AML posture for any custodial surface.
2. **Audit complete** (issue #4). Critical/high findings closed on coordinator,
   treasurer, authorizer.
3. **Mainnet programs** (issue #7). Fresh program IDs, Squads multisig
   authorities, upgrade keys offline.
4. **Genesis run complete** on testnet with published metrics (issue #3 go).
5. **TGE event** via Wiener Launchpad rails (or equivalent):
   - Mint under multisig
   - Distributor program for airdrop / vesting schedules
   - Public tokenomics page linking this document and the legal summary
   - No APY marketing copy
6. **Post-TGE**: inference revenue (later) routes to treasury; futarchy for next
   model selection remains Phase 4.

## What is deliberately not claimed

- The token is not marketed as equity, debt, or a guaranteed return.
- Security is economic, not cryptographic. Uncaught rate, band width, and bond
  curve remain public metrics forever.
- Supply shares above are a planning sketch until counsel and governance lock them.

## Acceptance mapping (issue #6)

| Acceptance criterion | Artifact |
|---|---|
| Tokenomics doc | This file |
| TGE plan consistent with legal review | Plan section; final numbers wait on #5 |
| Emission tied to PoG | Conversion section |
| Treasury for rewards and bounties | Allocation + burn projection |
| Point conversion | PoG to token section |

Reproduce numbers:

```
cd sim && uv run python -c "from leviathan_sim.economy import genesis_parameters, calibration_table, audit_burn_projection; print(genesis_parameters()); print(calibration_table([0.1])); print(audit_burn_projection([0.1]))"
```
