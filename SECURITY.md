# Security policy

Leviathan's product is a trust machine; a vulnerability report is a contribution to the core
product, not an embarrassment. The honest-claims policy (docs/DECISIONS.md, D6) applies here
first: we would rather publish a weakness than pretend it does not exist.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting on this repository (Security tab → "Report a
vulnerability"). Reports go to the wienerlabs maintainers privately; do not open a public issue
for anything exploitable.

In scope, in rough order of how much we care:

1. Economic-security breaks: any way to cheat the bond/audit/slash loop with positive expected
   value — grinding the round seed, dodging the audit lottery, submitting work that survives
   replay without doing it, draining or freezing bonds in the treasurer.
2. Aggregation breaks: attacks that get more damage past centered-clip + excision than the
   published within-band budget implies, at coalition sizes below the excision threshold.
3. Sim errors that would make a published number wrong (loss tables, catch times, bond curve).
4. Classic vulnerabilities in the Anchor programs or daemons (leviathan-net) once public.

Out of scope: volume/DoS against public devnet endpoints, findings that require the run
authority's own keys, and anything already listed as a known limitation in docs/GAPS.md or the
whitepaper's honest-limitations section — though sharpening a known limitation into a concrete
exploit is very much in scope.

## Paid red-team program

The red-team bounty design is published in `docs/REDTEAM_BOUNTY.md`. Break classes A-E,
severity tiers, disclosure timeline, and the default on-chain reporter share
(`slash_bounty_bps = 5000`) are defined there. Off-protocol Critical/High/Medium/Low
payouts become active when the treasury endowment is reserved (ops checklist in
`docs/ops/OPS_RUNBOOK.md`). In-protocol bounties pay automatically on bond forfeit when
the run has non-zero `slash_bounty_bps` and a reporter account.

## What to expect

Acknowledgement within 72 hours, a severity assessment within a week, credit in the fix's
release notes unless you prefer otherwise. Severity maps to the tiers in
`docs/REDTEAM_BOUNTY.md`.

Good-faith research within this policy will not be met with legal action.
