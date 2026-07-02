# Rules - shared-budget-updater

## Invariants (never break these)

- **The sheet IS the approval gate.** A row's existence with empty column D IS
  the approval. Claude NEVER adds, edits, or deletes rows in the uploader tab -
  budget changes are decided and entered by humans outside Claude.
- **NEVER hand-mark column D.** Only the workflow writes `x`. Hand-marking
  silently cancels an approved change.
- **NEVER widen the mutation surface.** updateMask stays amount_micros - no
  status changes, no pausing, no campaign fields, ever.
- **Exit 0 on partial failure is BY DESIGN; do not "fix" it.** The consolidated
  Slack alert is the failure signal; the yml failure() alert covers crashes
  that happen before the row loop.
- **Do not re-dispatch the workflow to force a retry before diagnosing.** The
  next scheduled run retries failed rows automatically (their column D is
  empty).

## Triage table

| error_code | Class | Action |
|---|---|---|
| TIMEOUT, CONNECTION_ERROR, any HTTP 5xx / INTERNAL_ERROR | Transient | Nothing. Empty column D self-retries on the next scheduled run. Same row transient 2 consecutive runs = systemic - escalate to the account owner |
| INVALID_AMOUNT (the $0-or-less guard) | Sheet data | Tell the account owner which row + value; the fix is correcting or removing the row value in the sheet. Never work around by hand-marking D |
| NOT_FOUND / invalid-argument class (bad budget ID, CID mismatch, INVALID_CUSTOMER_ID) | Sheet data | Verify CID + shared budget ID with a read-only lookup; report the exact correction needed; the row gets fixed in the sheet |
| USER_PERMISSION_DENIED / PERMISSION_DENIED / auth class | Access | Escalate to the account owner immediately (MCC link / OAuth health); do not retry-spam |
| UNEXPECTED | Unknown | Read the Actions run log for the traceback, summarize, escalate with the log excerpt |

## Escalation default

When a row's failure class is ambiguous, report and stop - never guess a sheet
edit. The sheet belongs to humans; the job here is diagnosis, not repair.
