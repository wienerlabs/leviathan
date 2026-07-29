# Tokenomics and TGE design

Issue #6. Design consistent with the economic model already coded in
`sim/leviathan_sim/economy.py` and the whitepaper economics section. This is an
engineering and product design document. It is not a legal opinion. Issue #5
(counsel review) gates any public token offer.

On-chain facts below were read from Solana mainnet on 29 July 2026. Where a
row names a mint, account or Streamflow contract, a reader can re-check the
number without trusting this document.

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
| Collateral (mainnet mint, TBD for run bonds) | Bond deposits, slash forfeiture, optional reward redemption | External mint or network stable collateral |
| PoG points | Per-epoch earned counter on the coordinator, already live on devnet | Coordinator epoch settlement |
| Network token ($LEVI) | Long-term reward and governance unit | Mint `LeViePUwqFYuKzA5sDXHkU2Jec1xwDn8Tdk55ecSqvv` (Token-2022) |

$LEVI is live on Solana mainnet:

- Mint: `LeViePUwqFYuKzA5sDXHkU2Jec1xwDn8Tdk55ecSqvv`
- Token-2022, 9 decimals, total supply 1,000,000,000
- Mint authority: revoked. Freeze authority: revoked.
- Extensions: metadataPointer and tokenMetadata only. No transfer fee.

Before TGE-style product claims, testnet and genesis rehearsal still pay only in
the testnet collateral mint
(`BWLv1Fj5RKJbcr3ZMLVKhviFq1i3tq6afgVS2ngyot3X` on devnet). PoG points convert
to collateral through the treasurer claim path already deployed on devnet.

## Operating economics (coded, not invented)

From `genesis_parameters()` and `calibration_table()`:

| Preset | Round cost (H100) | Round reward (1.35x) | Bond at p=0.1 | Expected catch rounds |
|---|---|---|---|---|
| 125M proof | $0.0120 | $0.0162 | $0.15 | 10 |
| 1B genesis | $0.240 | $0.324 | $2.91 | 10 |
| 7B scale | $3.36 | $4.53 | $40.79 | 10 |

Break-even law (implemented in `break_even_bond`):

```
bond = reward * (1 - p) / p
```

This is a floor against the cheater, not the whole story. A bonded verifier
committee adds a second, independent floor: the forfeited bond must also pay the
verifiers who did the auditing, split across the quorum. At genesis scale that
second constraint dominates, so a three-verifier committee needs roughly $10.55
rather than the $2.91 above, and the bond the network requires is the larger of
the two. See [COMMITTEE_ECONOMICS.md](COMMITTEE_ECONOMICS.md).

Zero-fraud audit burn (`audit_burn_projection`, fee = 1.1x H100 cost):

| Preset at p=0.1, 100 workers | Audit fee / contribution | Treasury burn / round | Burn share of rewards |
|---|---|---|---|
| 1B genesis | $0.264 | $2.64 | 8.15% |

This is the sustained cost of security when nobody is cheating. The treasury must
be sized for it.

## Supply allocation

Six planning buckets remain the product map. Three of them are now enforced on
chain (team lock, ecosystem lock, live DEX pool balance). Three remain
intentions held or funded through the treasury multisig until separate
contracts or run emission schedules exist.

In the table below, a named contract or vault address is a commitment a reader
can verify. A row without an address is an intention only.

| Allocation | Share (plan) | On-chain status | Vesting / control | Address |
|---|---|---|---|---|
| Training rewards endowment | 35% | Intention | Multi-year PoG emission from treasury-funded run vaults; not a separate Streamflow stream | (no dedicated contract; funds sit under treasury policy until emitted) |
| Audit / security treasury | 15% | Intention | Continuous draw for audit fees and red-team bounties under treasury policy | (no dedicated contract; same treasury) |
| Ecosystem / grants | 10% | Settled | Streamflow, immutable, non-cancellable. Linear over 24 months from 29 July 2026. Recipient is the treasury multisig, not a personal wallet | `J1L8QzmHGChv3YKduRi2DN6bvtmev2tnjL51W7DnmDHZ` |
| Team | 25% | Settled | Streamflow, immutable, non-cancellable. Nothing unlocks before 29 July 2027, then 36 monthly releases of 6,944,444 LEVI. Cannot be cancelled by the team | `8imUz6edAWFfPzsyrJqYwvF1UP54rtFTe5asNu1zqyfX` |
| Early contributors / community | 10% | Intention | TGE unlock plus short vest when that path ships | (no dedicated contract yet) |
| Liquidity / market making | plan 5%; contributed ~8.08% | Settled as pool balance, not as an LP lock | LEVI and SOL sit in the Raydium CPMM pool. Reserves move with trading, so the share is not constant. The extra above 5% was funded from the treasury to deepen the book before the first unlocks arrive. The LP position is not locked | Pool `wauDNp6gNoDayfPEUd675p9ouXYULknr3EQmSgVAMne` |

Total plan shares sum to 100%. The historical note still holds for the
intention map: team rose from 15% to 25% by reducing the training rewards
endowment from 45% to 35%. Training rewards remain the largest single planned
bucket (35% > 25%).

Emission is not a fixed block subsidy. Each run configures epoch earning rates on
the coordinator; the treasury tops up the run vault. Unused endowment stays
unminted or locked, never inflated ad hoc.

### Team lock (settled)

Contract `8imUz6edAWFfPzsyrJqYwvF1UP54rtFTe5asNu1zqyfX` holds 250,000,000 LEVI
(25% of supply) on Streamflow. The stream is immutable and cannot be cancelled.
Nothing unlocks until 29 July 2027. After that cliff, unlocks run monthly across
36 months at 6,944,444 LEVI per month. Recipient:
`GvS6K2HCyW42Lgtg3a4Te53uM3EMXwAwyb4m6ftPBC6K`.

### Ecosystem and grants lock (settled)

Contract `J1L8QzmHGChv3YKduRi2DN6bvtmev2tnjL51W7DnmDHZ` holds 100,000,000 LEVI
(10% of supply) on Streamflow. The stream is immutable and cannot be cancelled.
Unlock is linear across 24 months starting 29 July 2026. Recipient is the
treasury multisig `ALxuDYPT5BYE5jWW5zF4BK8o1KXAwPcrt7SGdUspjNNr`, not a personal
wallet. That differs from the earlier sketch (delayed start and non-treasury
recipient).

### Liquidity (settled as open pool, not locked)

Raydium CPMM pool `wauDNp6gNoDayfPEUd675p9ouXYULknr3EQmSgVAMne` held, at the
29 July 2026 mainnet read, 80,751,548 LEVI and 67.19 SOL (about 9,948 USD).
Cumulative LEVI contributed to liquidity is about 8.08% of supply against a
planned 5%. The increase was funded from the treasury to deepen the book before
the first unlocks arrive. Pool reserves change with every trade, so the
percentage is not a constant.

The liquidity provider position is not locked. Do not treat liquidity as locked
or burned until a lock transaction exists, and then cite it by signature.

### Intentions still under treasury policy

Training rewards (35%), audit and security (15%), and early contributors /
community (10%) do not each have a separate vesting contract yet. Their
working capital sits in or is paid from the Squads treasury until emission,
grants or future streams are created. Those rows are intentions, not
Streamflow commitments.

## Where the supply actually is

Balances below were read on Solana mainnet on 29 July 2026 against the named
addresses. Re-check each line on-chain; pool and unlocked stream balances move.

| Location | Address | Amount (LEVI) | Share of 1B | Control |
|---|---|---|---|---|
| Treasury multisig (Squads, 2 of 3) | `ALxuDYPT5BYE5jWW5zF4BK8o1KXAwPcrt7SGdUspjNNr` | 500,160,070 | 50.02% | Program-derived Squads vault. No private key exists for this address |
| Team Streamflow lock | `8imUz6edAWFfPzsyrJqYwvF1UP54rtFTe5asNu1zqyfX` | 250,000,000 | 25.00% | Immutable stream. Recipient `GvS6K2HCyW42Lgtg3a4Te53uM3EMXwAwyb4m6ftPBC6K`. No unlock before 29 July 2027 |
| Ecosystem Streamflow lock | `J1L8QzmHGChv3YKduRi2DN6bvtmev2tnjL51W7DnmDHZ` | 100,000,000 | 10.00% | Immutable stream. Recipient is the treasury multisig. Linear 24 months from 29 July 2026 |
| Raydium CPMM pool | `wauDNp6gNoDayfPEUd675p9ouXYULknr3EQmSgVAMne` | 80,751,548 (pool reserve at read) | ~8.08% contributed; reserve share moves with trading | Open market pool. LP position not locked |
| Remaining float | various | residual to 1,000,000,000 after the rows above | residual | Circulating and other accounts. Founder wallet `DePfNY9tn3E7pTMP8arSV16PdrfmUDTdQnfs8FnUiWEM` holds essentially zero LEVI and is not a custody surface |

Mint authority and freeze authority on
`LeViePUwqFYuKzA5sDXHkU2Jec1xwDn8Tdk55ecSqvv` are both revoked. Further supply
cannot be minted by any key.

## PoG to token conversion

1. Trainer stays Healthy through an epoch and accrues `earned` points (existing
   coordinator behaviour).
2. Treasurer `participant_claim` redeems points for collateral while the run is
   collateral-denominated.
3. After TGE-style mainnet reward runs, a conversion rate is fixed per run at
   run-create time:
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
3. **Mainnet programs** (issue #7). Fresh program IDs for training programs,
   Squads treasury already live at
   `ALxuDYPT5BYE5jWW5zF4BK8o1KXAwPcrt7SGdUspjNNr`, upgrade keys offline.
4. **Genesis run complete** on testnet with published metrics (issue #3 go).
5. **Public launch hygiene** on Solana rails (no launchpad dependency):
   - Mint already live with revoked mint and freeze authority
   - Team and ecosystem Streamflow locks already live (see addresses above)
   - Distributor program for any remaining airdrop or community vest
   - Public tokenomics page linking this document and the legal summary
   - No APY marketing copy
6. **Post-launch**: inference revenue (later) routes to treasury; futarchy for
   next model selection remains Phase 4.

## What is deliberately not claimed

- The token is not marketed as equity, debt, or a guaranteed return.
- Security is economic, not cryptographic. Uncaught rate, band width, and bond
  curve remain public metrics forever.
- Liquidity is not locked and not burned. The Raydium pool is an open market
  position until a lock transaction is published by signature.
- Training rewards, audit treasury spend, and community vest are still
  intentions under multisig policy until each has its own enforceable schedule
  or emission path. Team (25%), ecosystem (10%) and the live pool balance are
  settled on-chain and named above.

## Acceptance mapping (issue #6)

| Acceptance criterion | Artifact |
|---|---|
| Tokenomics doc | This file |
| TGE plan consistent with legal review | Plan section; final legal posture waits on #5 |
| Emission tied to PoG | Conversion section |
| Treasury for rewards and bounties | Allocation + burn projection + treasury address |
| Point conversion | PoG to token section |
| On-chain team and ecosystem locks | Streamflow contracts named in allocation and supply tables |

Reproduce economics numbers:

```
cd sim && uv run python -c "from leviathan_sim.economy import genesis_parameters, calibration_table, audit_burn_projection; print(genesis_parameters()); print(calibration_table([0.1])); print(audit_burn_projection([0.1]))"
```

Re-check supply on mainnet against the addresses in "Where the supply actually
is". Pool and stream unlock figures will drift after 29 July 2026; the
addresses do not.
