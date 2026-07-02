# Rules — Budget Guardian alert triage

Decision logic for triaging Guardian alerts. `examples.md` has worked
decisions; `SKILL.md` is the deploy guide.

## Invariants (never break these)

- **Budget changes are NEVER executed by the AI** — not in Google Ads, not in
  the budget sheet. Alerts are signals to humans; triage output is diagnosis +
  recommendation, full stop.
- **Alert-only is BY DESIGN — never add pausing** or any Google Ads write to
  this workflow or its triage. "Investigate immediately" never means "mutate
  immediately."
- **Guardian State is workflow-owned.** Deleting a state row forces a re-alert —
  a legitimate human op; the AI recommends it, never performs it.
- **Kill switch = pause of monitoring, not a fix.** Only ENABLED
  (case-insensitive) enables; an empty cell reads DISABLED (fail-closed).
  Recommending DISABLED always comes paired with a reason and a re-enable
  condition. Never disable to silence a noisy-but-correct alert.
- **Do not re-run the workflow to "re-send" a deduped alert.** One alert per
  account per threshold per month is the design; the `Guardian State` tab is
  the answer to "why no second alert."

## Triage table

| Alert | Check first | Action |
|---|---|---|
| Warning: Budget Hit 100% | Day of month. Late-month 100% is often normal pacing; early/mid-month is not. Then: the budget value in the `Budgets` tab (stale/wrong number?), recent budget changes, campaigns with end dates that front-load delivery | Usually monitor + report context. Escalate to the account owner with evidence if early-month or the budget number looks wrong. No writes anywhere |
| CRITICAL: Budget Exceeded 120% | Treat as incident. Change history for campaigns/budgets nobody created (hijack pattern); budget-source errors — **several accounts alerting at once = suspect your budget source FIRST** (a single formula error once pushed wrong numbers across many accounts at once); then genuine overdelivery | Escalate to the account owner immediately with findings. Never pause, never lower a budget — surface what you found, let the human judge |
| Budget Guardian: Script Error | The Actions run log traceback. Classify: auth (OAuth/API access health) vs transient (5xx/timeout) vs code | Auth → escalate immediately, don't retry-spam. Transient → the next 2h run self-heals; 2+ consecutive failures = systemic, escalate. Code → summarize the traceback + escalate with the log excerpt |
| Account seems unwatched | Bad rows in the `Budgets` tab never alert: an unparseable budget cell is dropped with a **log-only** warning ("Could not parse budget..."); an incomplete row (missing name, CID, or budget) is skipped **silently**. Check the Actions run log, then the tab's cells (CID digits-only, budget numeric, all three columns filled) | Report the exact cell to fix — the fix itself is a human edit. The next run picks the row up automatically |
| Silence (nothing firing) | Silence ≠ healthy. Kill switch ENABLED? Last Actions run green? `Guardian State` tab plausible for the month? | Only after those three checks call it all-clear. Remember accounts with zero MTD spend never alert by design |

## Escalation default

When an alert's class is ambiguous, report and stop — never guess a sheet
edit or an Ads change. The budgets belong to humans; the job here is
diagnosis, not repair.
