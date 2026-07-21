# GitHub issues map

Source: https://github.com/wienerlabs/leviathan/issues

| # | Title | Deliverable in repo | Closeable by code alone? |
|---|---|---|---|
| 2 | Red-team bounty program design | `docs/REDTEAM_BOUNTY.md`, `SECURITY.md` | Yes (design). Endowment funding is ops. |
| 3 | Rehearsal and pilot retro | `scripts/analyze_telemetry.py`, `docs/RETRO_REHEARSAL.md` | Partial. Decision is **NO-GO** until 350M/two-GPU gates pass. |
| 4 | External security audit | `docs/AUDIT_PREP.md` | No. Needs auditor + budget. |
| 5 | Legal and regulatory review | `docs/LEGAL_BRIEFING.md` | No. Needs counsel memo. |
| 6 | Tokenomics and TGE design | `docs/TOKENOMICS.md`, `docs/assets/tokenomics.json` | Design yes. Final lock waits on #5. |
| 7 | Mainnet deployment | `docs/launch/MAINNET_DEPLOY.md` | No. Gated on #4 #5 #6 + keys. |
| 8 | Mainnet Genesis Run | `docs/launch/GENESIS_LAUNCH.md` | No. Gated on everything above + #3 GO. |
| 9 | Monitoring, alerting, ops runbook | `docs/ops/`, `scripts/check_killswitches.py`, leviathan-net telemetry rules | Design + offline evaluator yes. Prod deploy is ops. |
| 10 | Finalise name and branding | `docs/BRANDING.md` | No. Owner + trademark decision. |

Honest policy: do not close #4, #5, #7, #8, or #10 with a fake report, fake legal memo,
fake mainnet deploy, or unilateral trademark claim. Ship the real artifacts that
unblocks those gates, then execute the external steps.
