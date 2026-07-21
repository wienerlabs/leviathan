# Counsel briefing: bond and token classification

Issue #5. This is a **fact packet for counsel**, not a legal memo and not legal
advice. Acceptance for #5 is a memo from qualified counsel describing a compliant
launch structure.

## Product facts counsel must assume

1. Participants post a **bond** (collateral tokens) to join a training run.
2. Accepted work earns **Proof of Gradient** points redeemable for rewards.
3. Detected fraud leads to **slashing** (forfeit of bond / reduction of claim).
4. A fraction of forfeited bond can pay a **reporter bounty** (`slash_bounty_bps`).
5. After TGE, a **network token** may fund rewards, treasury, and governance of
   which model the network trains next (see `docs/TOKENOMICS.md`).
6. The chain (Solana) settles commitments, audits, and money. Gradients stay off-chain.
7. The team operates programs with upgrade authority (planned: Squads multisig).

## Questions for counsel (do not answer in-repo)

1. Is the bond a security deposit / performance collateral, or does any structure
   risk classification as a financial instrument in target jurisdictions?
2. Does the reward token, under the planned utility (PoG redemption, run
   selection governance, later inference settlement), fit a compliant path in
   the team's jurisdiction of incorporation and primary user geographies?
3. What KYC/AML obligations attach if any path is custodial vs fully
   self-custodial wallet + permissionless join?
4. Can red-team bounty payouts (USDC) be made without creating a regulated
   prize/contest problem?
5. What disclosures are required on the public dashboard and docs site?
6. Recommended entity stack for: program upgrade authority, treasury, token mint,
   and grant distributions.

## Materials to send with the engagement

- `docs/WHITEPAPER.md`
- `docs/TOKENOMICS.md`
- `docs/REDTEAM_BOUNTY.md`
- `docs/ARCHITECTURE.md`
- `DEVNET.md` from leviathan-net (as-built on-chain behaviour)
- This briefing

## Non-claims (engineering policy until counsel says otherwise)

- No APY, yield, or "guaranteed returns" copy in product or marketing.
- No implication that bonds are insured or risk-free.
- No public TGE until counsel memo exists and #4 audit gate clears.
- Tokenomics allocation table remains a planning sketch.

## Engagement status

| Item | Status |
|---|---|
| Fact packet | This file |
| Counsel engaged | Owner action |
| Legal memo | Not started |
| Compliant launch structure | Blocked on memo |

## Acceptance mapping (issue #5)

| Criterion | Status |
|---|---|
| Legal memo with compliant structure | Blocked on counsel |
| Briefing packet | Delivered |
