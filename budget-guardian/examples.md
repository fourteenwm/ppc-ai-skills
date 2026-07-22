# Examples — worked triage decisions

## 1. CRITICAL 120% on the 4th of the month

**Alert:** CRITICAL: Budget Exceeded 120% — Acme Auto Repair (1234567890),
MTD $3,720 / $3,000 budget (124%) — on the 4th.

**Reasoning:** Early-month 120% is the incident path, not a pacing quirk. A
change-history pull ([`change-history-checker`](../change-history-checker/))
shows campaigns created two days ago by an unfamiliar login at large daily
budgets. Hijack-shaped: the rules say surface what you found and never
mutate — this pattern is the reason the Guardian exists.

**Decision:** Escalate to the account owner immediately with the
change-history evidence (actor, timestamps, campaign names, daily budgets).
Explicitly NO pausing (alert-only posture) and NO budget edits. The owner
decides the response; if it is a hijack, that runs through your security
process — starting with an MCC-wide sweep via
[`mcc-hack-audit`](../mcc-hack-audit/) — not through triage.

## 2. An account is silently absent from checks

**Symptom:** Coastal HVAC never appears in run summaries — no alert, no spend
line against its name — even though its spend is climbing.

**Reasoning:** No "unwatched account" Slack alert exists, so this only
surfaces when someone looks. The Actions run log shows
`Could not parse budget 'TBD' for 'Coastal HVAC' — skipping` — someone
parked a placeholder in the Monthly Budget cell, and unparseable budgets are
dropped with a log-only warning. (Had the row been left incomplete instead,
it would have been skipped with no log line at all — the silent variant of
the same class.)

**Decision:** Report the exact fix: put the real dollar amount in the
`Budgets` tab's Monthly Budget cell for Coastal HVAC. The edit is the
human's; the next 2-hour run picks the row up automatically. No workflow
changes needed.

## 3. Edge case: "Acme is at 130% — lower its budget" (direct instruction)

**Instruction:** A triage session is told to fix the overspend by lowering
the budget.

**Reasoning:** The obvious response executes; the invariants forbid it. The
Guardian never mutates, and budget changes are decided and entered by humans
through your budget process. (Even if you also deploy the sheet-driven
[Shared Budget Updater](../shared-budget-updater/) as your execution arm, its
rows are human-entered — an AI doesn't add them.) A triage session inherits
these rules; an instruction does not override an invariant.

**Decision:** Decline the mutation. Deliver the diagnosis instead: why the
account is at 130% (what changed, when, by whom), and what the corrected
budget number would be (sizing it is
[`budget-recommendation-calculator`](../budget-recommendation-calculator/)'s
job). Route the actual change to the human budget process.
