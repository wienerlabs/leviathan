# Gap analysis

Snapshot 2026-07-20, after Phase 1 closed on devnet. A self-audit of what the docs promise
against what the code and task ladder actually deliver. Ordered by how much each gap can hurt.
Items marked (T) were folded into docs/TASKS.md.

Status update, same day: the gaps closable in this repo were closed — the within-band damage
scenario (`--band-sweep`: +0.019 loss at the 0.05 operating band for a 5/16 coalition, ~0.9%,
roughly linear in band width, with explicit replay evidence that audits pass by construction), the
zero-fraud verifier burn projection and Genesis operating point in economy.py, a 28-test sim
suite with CI, SECURITY.md, CONTRIBUTING.md, and the doc-drift fixes (PRD as-built note, README
privacy line). Still open: the LICENSE decision (owner call), and everything that lives in
leviathan-net or requires hardware — band calibration across GPU classes, two-GPU replay, the
production verifier daemon, multi-epoch re-join, randomness hardening, the dispute committee.

## 1. Security-model gaps

### Tolerance band is uncalibrated
The band is the core security parameter — its width is, by our own definition, the adversary's
safe cheating margin — and it has only ever been exercised at 0.05 on one machine against a
synthetic 1% drift. The cross-hardware calibration harness (4090, 3090, A100, H100) is a Phase 2
task that nothing else may ship before: a band set too tight slashes honest nodes and violates
the PRD's "zero honest-node slashes" metric; too loose and it hands stealth coalitions a budget.
(T: already in Phase 2.)

### No within-band damage scenario in the sim
ARCHITECTURE.md claims "sim/ tracks how much loss damage fits inside a given band so the
parameter is chosen with eyes open." No scenario in run.py does this: the seven scenarios cover
sign-flip, ALIE and non-IID FPR, but none measures the maximum training bias an adversary can
inflict while staying inside the published band. The whitepaper's honest-limitations section
admits the weakness; the sim does not yet quantify it. Docs and code disagree. (T: Phase 2.)

### Dispute resolution is a single authority
`slash_client` is main_authority gated. The bonded multi-verifier vote with reporter bounty is
deferred to Phase 3, which means the entire Genesis Run — 50+ external nodes with real bonded
value at (testnet) stake — runs with a centralized slash decision. That may be acceptable, but
it must be published as a limitation on the Genesis dashboard, with the scope and the timeline
for decentralizing it. (T: Phase 2 disclosure, Phase 3 mechanism.)

### Weak round randomness is not on the task ladder
`get_random_seed(clock)` = sha256(unix_timestamp, slot) is grindable by a leader. CODEMAP.md
acknowledges this and says hardening "goes on the mainnet checklist" — but TASKS.md Phase 3 has
no such entry. A checklist item that is not on the checklist is a lost item. (T: Phase 3.)

### Two-GPU replay reproduction was skipped, not done
PRD Phase 1 acceptance requires the replay verifier to reproduce a sampled contribution within
the band on two different GPUs. It was folded into 1.9's swarm bring-up and then the swarm ran
on a single MPS machine. Phase 1 is declared complete with this criterion unmet. Carry it
forward explicitly rather than letting the fold hide it. (T: Phase 2.)

### No production verifier daemon
The decision core exists twice — Python sim (verifier.py) and the 1.8 replay experiment — but
the daemon that subscribes as Committee::Verifier, replays real gradients and calls run_slash
does not. It shares the libtorch prerequisite that 1.9 already solved, so the path is open.
(T: Phase 2.)

### Multi-epoch re-join resilience
Deferred out of 1.9. A 7-day churn run cannot pass without it. (T: already implied by Phase 2
rehearsal; now explicit.)

## 2. Economics gaps

### Verifier income has no zero-fraud sustainability story
The whitepaper says slashed stake pays the verifiers hunting it. In the equilibrium we actually
want — no fraud — verifier income is purely the audit_fee drawn from the treasury. Who funds
sustained audit pressure, at what burn rate, and for how long, is unmodeled. The economy sim has
the ledger; add the projection. (T: Phase 2.)

### Genesis bond parameters are undefined
Real-bond calibration is Phase 3, but Phase 2 Genesis Run needs concrete (testnet) bond values,
and the choice communicates the economics to the first external cohort. Decide and publish them
with the same (1-p)/p discipline. (T: Phase 2.)

## 3. Repository hygiene

- **No LICENSE.** A project whose thesis is "the model belongs to the network" currently
  reserves all rights by default. The fork substrate is Apache-2.0; this repo needs an explicit
  choice before anything is made public. Owner decision, not picked unilaterally here.
- **No tests, no CI.** The README's headline numbers (2.175 honest loss, 9.8-round mean catch
  time) are reproducible only by hand. A CI job that runs a short-horizon sim and asserts the
  qualitative outcomes (clip neutralizes sign-flip, audit catches ALIE, zero honest FP) would
  keep the claims honest as the sim evolves. (T: Phase 2.)
- **No SECURITY.md.** The red-team bounty is a Phase 2 design task, but a responsible-disclosure
  channel should exist from the first day the repo is public. (T: Phase 2.)
- **No CONTRIBUTING.md.** Low priority while private; required before Genesis opens the doors.

## 4. Doc drift

- README still says "Private under wienerlabs while Phase 1 lands" — Phase 1 has landed; the
  sentence and the publicity decision need refreshing.
- PRD Phase 1 acceptance said "4-process local swarm trains the 826k-parameter sim model through
  the real chain path"; what actually ran was a single-client Nano-Llama epoch on devnet. The
  substitution is defensible (live chain beats local processes) but the PRD should record it
  instead of silently diverging.
- CODEMAP inherits the upstream `comptue_hash` misspelling; cheap to fix in the fork, and the
  note in CODEMAP should flip from "grep accordingly" to "fixed at <commit>" when it is.
- Devnet program keypairs live in the private repo history. CODEMAP already rules them
  devnet-only; the mainnet key regeneration must be a task, not a footnote. (T: Phase 3.)

## 5. What is explicitly not a gap

Scope discipline the docs already get right, listed so nobody re-litigates it: no on-chain
tensors, no Windows nodes, no generic compute marketplace, no frontier-quality claims, no
cryptographic-proof claims. The honest-claims policy (D6) is the standard this file holds the
rest of the project to.
