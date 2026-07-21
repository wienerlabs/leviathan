# Monitoring, alerting, and ops runbook

Issue #9. Makes a mainnet (or public testnet) run on-call-able. Alert rules live
in `docs/ops/alerts/` and are intended to be loaded into the Prometheus stack
that already exists under `leviathan-net/telemetry/`.

## Architecture

```
Solana RPC  -->  leviathan-indexer  -->  metrics / JSON telemetry
Clients     -->  OTel / Prometheus  -->  Grafana
Alerts      -->  Alertmanager / Pager  -->  on-call
```

Indexer security assessment (`assess_security` in leviathan-indexer) encodes the
break-even bond law. Dashboard must show `economically_secure` per run.

## Kill-switch signals

| Signal | Meaning | Severity | First response |
|---|---|---|---|
| Uncaught fraud | Fraud proof exists or red-team class A confirmed without slash within 2 epochs | Critical | Pause run; freeze joins; incident channel |
| Economic insecurity | `expected_fraud_value_per_round > 0` for active run | Critical | Pause reward accrual; retune bond/p |
| Mesh partition | Active clients drop >50% while epochs still advance | High | Check relays, RPC, iroh; pause if attestations fail |
| Treasury drain | Vault balance drop not explained by claims/bounties in window | Critical | Pause claims; audit vault txs |
| Honest FPR | Honest client slashed | Critical | Pause; investigate verifier/band |
| Indexer lag | `chain_slot - indexed_slot` above threshold | High | Scale indexer; do not trust dashboard |
| Authority anomaly | Unexpected upgrade or authority change | Critical | Multisig emergency; pause |

## Alert rules

See:

- `docs/ops/alerts/leviathan-killswitch.rules.yml` (Prometheus)
- `scripts/check_killswitches.py` (offline / CI-friendly evaluation from JSON)

## On-call rotation

1. Primary engineer (24h window during public runs)
2. Secondary (backup)
3. Multisig signer available within 1h for pause/upgrade votes

Handoff checklist: open incidents, run state, vault balances, last slash event,
dashboard URL, RPC status.

## Incident process

1. **Detect**: alert or human report.
2. **Triage** (15 min): severity, kill-switch class, blast radius.
3. **Contain**: pause run if Critical; disable joins; snapshot vault and
   coordinator accounts.
4. **Communicate**: status page + X/Discord as appropriate; no speculation.
5. **Diagnose**: chain txs, indexer logs, client logs, verifier fraud proofs.
6. **Recover**: fix, multisig upgrade if needed, resume only with written go.
7. **Retro**: within 72h; update GAPS and this runbook.

## Runbook playbooks

### Uncaught fraud

1. Confirm fraud class with independent replay (`leviathan-verifier`).
2. If proof valid and no slash: authority executes `run_slash` with proof hashes.
3. If authority path compromised: pause via remaining multisig controls.
4. Open Critical red-team payout track if external reporter.

### Mesh partition

1. Compare `active_clients` vs `registered_clients` from indexer telemetry.
2. Check iroh relay reachability and client versions.
3. If epochs advance with <50% mesh and rewards still accruing: pause.

### Treasury drain

1. List vault token account signatures since alert.
2. Classify: legitimate claims, bounties, unknown.
3. Unknown transfers: pause claims and escalate as Critical.

### Indexer lag

1. Restart indexer; verify program IDs.
2. Mark dashboard banner "data delayed".
3. Do not make economic decisions from a lagged board.

## Pre-launch readiness

- [ ] Prometheus + Grafana + Alertmanager deployed
- [ ] Kill-switch rules loaded and test-fired
- [ ] On-call schedule published
- [ ] Pause path rehearsed on devnet
- [ ] Red-team endowment funded
- [ ] Status communication channel ready

## Acceptance mapping (issue #9)

| Criterion | Status |
|---|---|
| Indexer-fed monitoring | Rules + existing telemetry stack |
| Alerts on kill-switch signals | `leviathan-killswitch.rules.yml` + checker |
| Incident runbook | This file |
| On-call-able before public launch | Ready when stack is deployed in prod |
