# Mainnet deployment runbook

Issue #7. Procedure for deploying audited programs to Solana mainnet.
**Do not execute** until issues #4 (audit), #5 (legal), and #6 (tokenomics lock
with counsel) clear. Devnet keypairs must never be reused.

## Prerequisites

- [ ] External audit report with critical/high closed (`docs/AUDIT_PREP.md`)
- [ ] Legal memo on bond and token (`docs/LEGAL_BRIEFING.md` engagement complete)
- [ ] Tokenomics parameters locked post-counsel (`docs/TOKENOMICS.md`)
- [ ] Fresh program keypairs generated offline (never the devnet keys in CODEMAP)
- [ ] Squads (or equivalent) multisig created for:
  - Upgrade authority of each program
  - Run `main_authority`
  - Mint authority / treasury if applicable
- [ ] Collateral mint chosen (stable or network token per legal structure)
- [ ] Dedicated mainnet RPC + websocket (not public free endpoints)
- [ ] Monitoring stack live (`docs/ops/OPS_RUNBOOK.md`)

## Program set

| Program | declare_id source | Mainnet ID |
|---|---|---|
| Coordinator | regenerate | TBD at deploy |
| Authorizer | regenerate | TBD at deploy |
| Treasurer | regenerate | TBD at deploy |

Record final IDs in `docs/launch/MAINNET_ADDRESSES.md` (create at deploy time).

## Key ceremony

1. Air-gapped or offline machine generates three program keypairs.
2. Backup encrypted to two geographic locations; paper backup of seeds optional
   per security policy.
3. Deploy wallet is a temporary hot key funded only for deploy rent + fees.
4. Immediately after successful deploy + IDL publish (if used), set upgrade
   authority to the Squads multisig vault.
5. Destroy or cold-store the temporary deploy key after authority transfer.
6. Never commit key material to git.

## Deploy sequence

Commands assume the leviathan-net tree and Anchor toolchain used on devnet
(`anchor build --no-idl` if IDL generation remains broken on the pin).

```
export CLUSTER=mainnet-beta
export RPC=https://<dedicated-mainnet-rpc>
export WS_RPC=wss://<dedicated-mainnet-ws>
export KEY_FILE=~/.config/solana/leviathan-mainnet-deploy.json

# 1. Build with mainnet program IDs written into declare_id! / Anchor.toml
anchor build --no-idl

# 2. Deploy each program (order: authorizer, coordinator, treasurer)
# Use the project scripts once MAINNET mode is wired; until then:
solana program deploy --url "$RPC" --keypair "$KEY_FILE" target/deploy/psyche_solana_authorizer.so
solana program deploy --url "$RPC" --keypair "$KEY_FILE" target/deploy/psyche_solana_coordinator.so
solana program deploy --url "$RPC" --keypair "$KEY_FILE" target/deploy/psyche_solana_treasurer.so

# 3. Transfer upgrade authorities to Squads
# 4. Create permissionless run with treasurer path
# 5. Fund rewards vault and set bond config from genesis_parameters()
# 6. Set slash_bounty_bps = 5000
# 7. verification_percent = 10, band published on dashboard
```

Bond parameters for the first mainnet run must match the published table at the
chosen scale (default design: 1B preset, p=0.1, bond ~9 rounds of reward).

## Post-deploy verification

- [ ] Program data accounts match expected binaries (hash compare)
- [ ] Upgrade authority is multisig only (not the deploy key)
- [ ] Dry-run join with a dust bond on a canary wallet
- [ ] Indexer points at mainnet program IDs
- [ ] Alerts fire on synthetic kill-switch test (see ops runbook)
- [ ] Pause / resume path tested

## Rollback

If a critical bug is found before public bonds:

1. Pause the run via authority.
2. Multisig votes upgrade or close path per incident severity.
3. Do not leave unpaused runs with real collateral while upgrading.

## Acceptance mapping (issue #7)

| Criterion | Status |
|---|---|
| Programs live on mainnet | Blocked on #4 #5 #6 |
| Authorities in multisig | Procedure above |
| Upgrade keys secured | Procedure above |
| Deploy runbook | This file |
