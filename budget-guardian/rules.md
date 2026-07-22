# Rules — Budget Guardian alert triage

Decision logic for triaging Guardian alerts — and for the three judgment
calls an operator owns: tuning thresholds, using the kill switch, and
keeping the budget roster honest. `examples.md` has worked decisions;
`references/alert-contract.md` has the exact thresholds, alert shapes, and
state mechanics; `SKILL.md` is the deploy guide.

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
| Warning: Budget Hit 100% | Day of month, then the false-alarm classes below. Then: the budget value in the `Budgets` tab (stale/wrong number?), recent budget changes (pull via [`change-history-checker`](../change-history-checker/)), campaigns with end dates that front-load delivery | Usually monitor + report context. Escalate to the account owner with evidence if early-month or the budget number looks wrong. No writes anywhere |
| CRITICAL: Budget Exceeded 120% | Treat as incident. Change history for campaigns/budgets nobody created — pull it via [`change-history-checker`](../change-history-checker/); if the actors or campaigns look unauthorized, sweep the MCC with [`mcc-hack-audit`](../mcc-hack-audit/). Budget-source errors — **several accounts alerting at once = suspect your budget source FIRST** (false-alarm classes below); then genuine overdelivery | Escalate to the account owner immediately with findings. Never pause, never lower a budget — surface what you found, let the human judge |
| Budget Guardian: Script Error | The Actions run log traceback. Classify: auth (OAuth/API access health) vs transient (5xx/timeout) vs code | Auth → escalate immediately, don't retry-spam. Transient → the next 2h run self-heals; 2+ consecutive failures = systemic, escalate. Code → summarize the traceback + escalate with the log excerpt |
| Account seems unwatched | Bad rows in the `Budgets` tab never alert — some skips leave a **log-only** warning, some are **silent** (exact parse ladder: [`references/alert-contract.md`](references/alert-contract.md)). Check the Actions run log, then the tab's cells (CID digits-only, budget numeric, all three columns filled) | Report the exact cell to fix — the fix itself is a human edit. The next run picks the row up automatically |
| Silence (nothing firing) | Silence ≠ healthy. Kill switch ENABLED? Last Actions run green? `Guardian State` tab plausible for the month? (What each surface proves: [`references/alert-contract.md`](references/alert-contract.md) § Reading run state cold) | Only after those three checks call it all-clear. Remember accounts with zero MTD spend never alert by design |

## False-alarm classes — rule these out before treating an alert as real

A firing alert is always *correct math* — MTD spend really did cross the
threshold against the budget number in the sheet. The false-alarm question
is whether the **budget number or the calendar** made correct math into a
misleading signal. Rule these out before escalating:

| Signal | Benign cause to rule out | Verify by | If benign |
|--------|--------------------------|-----------|-----------|
| Alert right after someone edited the `Budgets` tab | Mid-month budget change: MTD spend accrued against the OLD number, but the ratio compares it to the NEW one. Lowering a budget mid-month can trip 100%+ instantly | The sheet's version history for the budget cell, vs the alert timestamp | An artifact of the edit, not a spend event. If the budget was *raised* mid-month, note the opposite trap: this month's alert may already be consumed at the old number — delete the account's state row to re-arm at the new one |
| Alert in the first days of the month for an account that also alerted late last month | Month-boundary reset: state rows clear and MTD restarts, so a still-hot account re-alerts fresh in the new month | `Guardian State` shows only current-month rows (by design) | Not noise exactly — it's a NEW month's signal. But read it with day-of-month context, not as "alerting twice" |
| 100% landing in the last ~3 days of the month | Google's own delivery model: daily overdelivery up to 2× the daily budget, capped monthly at daily × 30.4 per campaign. If the sheet number sits below what the enabled daily budgets imply, Google will sail past it with nothing wrong | Sum of enabled campaigns' daily budgets × 30.4 vs the sheet's Monthly Budget | Expected delivery against a sheet number that doesn't reflect the real cap. The fix (if any) is the sheet number — a human decision about intent, not an Ads change |
| Early-month 100% on a small-budget account | Small denominators: 2× daily overdelivery on day 2-3 of a low monthly budget moves the ratio double digits in one day | Daily-budget-to-monthly ratio, day of month | Day-of-month context is the read: the same percentage means different things on the 3rd vs the 28th. Usually monitor, note it, and expect the 120% question to resolve within days either way |
| **Several accounts alerting in the same run** | One budget-source error — a formula, a bad paste, a stale import — pushed wrong numbers across many rows at once. The alerts are correct math on wrong budgets | The `Budgets` tab itself FIRST (recent edits, formulas, obviously-uniform or truncated values) — before any per-account investigation | Fix the sheet, then decide which state rows to delete so corrected budgets re-arm. Do NOT burn an hour per account investigating spend that was never wrong |

Day-of-month is the cross-cutting lens: late-month 100% is often just a
month concluding; early-month 100% is the incident-shaped read that
justifies the full triage-table path.

## Threshold tuning — which knob, and when

The thresholds are **two constants hardcoded in your copy of
`workflows/budget_guardian/main.py`** (`THRESHOLD_WARNING`,
`THRESHOLD_CRITICAL`) — deliberately not env vars. Exact values and
comparison semantics: [`references/alert-contract.md`](references/alert-contract.md).
Tuning is an edit to your fork, and the decision logic is mostly about NOT
reaching for it:

- **The per-account knob is the `Budgets` tab, not the constants.** One
  account alerting wrongly means its budget number is wrong — fix the cell.
  Never move a global threshold to quiet one account; that trades one
  account's noise for every account's detection latency.
- **What should this budget actually be?** That's a sizing question, not a
  Guardian question — route it to
  [`budget-recommendation-calculator`](../budget-recommendation-calculator/)
  and put its answer in the sheet.
- **Tune the constants only for portfolio-wide posture**: e.g. a book that
  routinely and acceptably runs a few percent over plan (warning at 1.05
  cuts habitual-noise pings), or a high-risk MCC where you want the critical
  page earlier than 120%. Keep warning < critical, always.
- **If you change a constant, change the labels with it.** The Slack headers
  and the state-tab threshold strings say "100%"/"120%" literally — they do
  not follow the constants (where each string lives:
  [`references/alert-contract.md`](references/alert-contract.md)). Dedupe
  keeps working either way; the labels just lie until updated.
- Changes take effect on the next 2-hour run. No state migration needed.

## Kill switch — what it's for (and the trap it sets)

Mechanics are fail-closed and exact
([`references/alert-contract.md`](references/alert-contract.md)); this is
the judgment:

- **Legitimate flips to DISABLED:** a planned restructuring of the budget
  sheet (mass edits would fire artifact alerts), migrating the sheet or
  credentials, or an incident *in the budget source itself* where every
  alert would be the same false alarm.
- **Wrong flips:** silencing one noisy account (that's a `Budgets`-tab fix),
  or muting a correct-but-uncomfortable alert. Per the invariants, every
  DISABLED recommendation ships with a reason and a re-enable condition.
- **The trap:** a disabled run exits green. The Actions history looks
  perfectly healthy while monitoring is off — nothing will remind you.
  Treat DISABLED as a parked state with an owner and a re-enable date, and
  make the switch cell the first check in any "why no alerts?" read.
- **Per-account alternatives, from scalpel to hammer:** fix the account's
  budget number → blank/zero its budget cell (deliberately unwatched, row
  preserved) → delete its row. The global switch is the hammer — it stops
  watching everything.

## The `Budgets` tab is the roster

The Guardian watches exactly what the tab lists — direct CIDs, no MCC
discovery. That model has judgment consequences (parse mechanics:
[`references/alert-contract.md`](references/alert-contract.md)):

- **New accounts are invisible until a human adds the row.** Adding to the
  MCC does nothing; adding the row is the onboarding step. Make it part of
  your account-launch checklist — the Guardian can't miss what it was never
  told to watch, and a hijacked *unlisted* account alerts nobody.
- **A blank or zero budget is the deliberate-unwatch idiom** — the row
  stays, the account is skipped. Use it for paused/parked accounts; leave a
  note in the row so a future reader knows it's intentional, because the
  Guardian won't distinguish parked from forgotten.
- **Coverage is an operator duty, not a Guardian feature.** Nothing alerts
  on "account exists in the MCC but not in the sheet." Periodically diff the
  tab against your MCC's account list (an ad-hoc pull via
  [`google-ads-query`](../google-ads-query/) works) and reconcile.
- **Bad rows degrade silently by design** — the run never fails because one
  row is malformed. The cost of that resilience is that a typo'd row is an
  unwatched account until someone reads the run log ("Account seems
  unwatched" in the triage table is the reactive path; the coverage diff
  above is the proactive one).

## Escalation default

When an alert's class is ambiguous, report and stop — never guess a sheet
edit or an Ads change. The budgets belong to humans; the job here is
diagnosis, not repair. Two standing routes for what triage surfaces: "what
should this budget be" →
[`budget-recommendation-calculator`](../budget-recommendation-calculator/);
"is this spend pace normal for this book" →
[`portfolio-pacing-rules`](../portfolio-pacing-rules/).
