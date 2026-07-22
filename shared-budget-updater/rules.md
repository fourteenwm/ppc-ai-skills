# Rules - shared-budget-updater

Decision logic for triaging failed rows — and for the judgment calls an
operator owns around a tool that changes live budgets: what number goes in
a row, when a row is safe to run (or run again), and how to work the daily
window. `examples.md` has worked decisions;
[`references/update-contract.md`](references/update-contract.md) has the
exact run mechanics (row lifecycle, parse ladder, alert shape); `SKILL.md`
is the deploy guide.

## Invariants (never break these)

- **The sheet IS the approval gate.** A row's existence with empty column D IS
  the approval. Claude NEVER adds, edits, or deletes rows in the uploader tab -
  budget changes are decided and entered by humans outside Claude.
- **NEVER hand-mark column D.** Only the workflow writes `x`. Hand-marking
  silently cancels an approved change.
- **NEVER widen the mutation surface.** updateMask stays amount_micros - no
  status changes, no pausing, no campaign fields, ever.
- **There is no sanity-check layer.** The workflow never reads the current
  amount — it writes the row's number, absolutely
  ([`references/update-contract.md`](references/update-contract.md) § The
  mutation). Only the $0-or-less guard stands between the sheet and the API;
  a wrong-but-positive number sails through. The approval gate is the entire
  defense — treat the row value with the same care as the budget field in
  the Ads UI.
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
| INVALID_AMOUNT (the $0-or-less guard) | Sheet data | Tell the account owner which row + value; the fix is correcting or removing the row value in the sheet. Never work around by hand-marking D. A $0 row is usually a pause attempt — see the boundary reasoning in `examples.md` #3 |
| NOT_FOUND / invalid-argument class (bad budget ID, CID mismatch, INVALID_CUSTOMER_ID) | Sheet data | Verify CID + shared budget ID with a read-only lookup (an ad-hoc pull via [`google-ads-query`](../google-ads-query/)); report the exact correction needed; the row gets fixed in the sheet |
| Account-level policy block (e.g. EU_POLITICAL_ADVERTISING_DECLARATION_REQUIRED) | Account state | The alert arrives with the fix attached (the hint line). The remedy is an admin action in the Google Ads UI, not a sheet edit — **leave the row pending**; it applies automatically on the first run after the account is unblocked. Deleting the row throws away an approved change; re-dispatching does nothing while the block stands |
| USER_PERMISSION_DENIED / PERMISSION_DENIED / auth class | Access | Escalate to the account owner immediately (MCC link / OAuth health); do not retry-spam |
| UNEXPECTED | Unknown | Read the Actions run log for the traceback, summarize, escalate with the log excerpt. Includes malformed amounts (`abc` in column C lands here — it is not silently skipped) |

## The number in the row — shared-budget math

Column C is the budget's **daily** amount — the number the Ads UI shows in
the budget column, not a monthly target (field semantics:
[`references/update-contract.md`](references/update-contract.md) § The
mutation). The judgment around it:

- **Converting a monthly plan:** monthly ÷ 30.4 is the standard mapping —
  Google caps monthly delivery at ~30.4× the daily amount and may spend up
  to 2× it on any single day. A monthly number entered raw is ~30×
  overspend, approved through the front door; the $0 guard cannot catch it,
  because $3,000 is a perfectly valid *daily* amount for some accounts.
  Nothing downstream will question the number — see the no-sanity-check
  invariant.
- **Sizing is not this tool's judgment.** "What should this budget actually
  be?" routes to
  [`budget-recommendation-calculator`](../budget-recommendation-calculator/);
  "is this pace normal for this book?" routes to
  [`portfolio-pacing-rules`](../portfolio-pacing-rules/). The row records
  the decision's output, never produces it.
- **The pairing interlock:** if you also run
  [`budget-guardian`](../budget-guardian/), remember it reads **monthly**
  budget numbers from its own tab. Pushing a new daily amount here does not
  update the Guardian's monthly number — raise a budget through this tool
  without touching the Guardian's tab and the next 100%/120% alert becomes
  *more* likely, and correct. When a budget decision lands, update both
  surfaces deliberately — or expect the tripwire to fire and triage it as
  the mid-month-edit artifact it is.

## Is this row safe to run — or run again?

The property that makes rerun reasoning tractable: pushes are **absolute
overwrites**. Re-applying an unchanged row rewrites the same number — safe.
The risk is never the rerun itself; it's the row's value having changed
meaning in between. The checks:

- **Crash-mid-run recovery.** A crash between mutations and the batch
  done-mark leaves already-applied rows unmarked
  ([`references/update-contract.md`](references/update-contract.md) § Row
  lifecycle). Compare the crashed run's log (`-> Budget updated` lines)
  against column D. Unmarked-but-applied rows will re-push identical values
  next run — no action needed, **unless someone edits those rows before the
  next run**. Freeze edits on them until the marks catch up; never resolve
  it by hand-marking D.
- **A failed row that has sat pending for days** is a stale decision, not
  just a stuck task. A daily amount sized last Tuesday may be wrong after
  the weekend. Fix the data error AND have the approver re-confirm the
  number is still the intent — leaving it queued is a silent re-approval
  nobody made.
- **Clearing an `x` to re-push** is legitimate when the sheet's number
  should win again — e.g. someone changed the budget in the UI and the
  approved value must be restored (verify who/what first via
  [`change-history-checker`](../change-history-checker/)). It is a live
  mutation: clear deliberately, one row at a time, and say so.
- **Two pending rows for the same CID + budget ID** both push, in row
  order — last wins, and the run log shows both as applied. Resolve to one
  row before the run; afterward, the later row is the one in effect.
- **Editing a PENDING row's amount is a new approval,** held to the same
  bar as adding a row. Editing a FAILED row to fix bad data (transposed
  budget ID, wrong CID) is the normal healing path — the approval already
  happened; the data just didn't match it.

## The daily window — cadence & manual dispatch

- **One scheduled run per day, and the latency is a feature.** The tab
  accumulates the day's decisions, and humans have until the cron fires to
  catch a wrong row. (Contrast the Guardian pair: detection runs every 2
  hours because alerts want speed; mutation runs daily because writes want
  a review window.)
- **There is no draft state.** A complete row IS an approval the moment the
  cron fires. Stage unfinished decisions by leaving a cell blank until
  final (incomplete rows skip silently) or on another tab — never as a
  complete row you intend to "fix before the run."
- **Manual dispatch is legitimate** for a time-sensitive approved change
  that can't wait for tomorrow's window, or to verify a systemic fix after
  a multi-row failure (auth restored, sheet repaired). It is NOT for
  hurrying a transient retry (the invariant: next run heals it) and NOT for
  "seeing if it works" against live rows — that's what the README Step 6
  test-account path is for.
- **Cron placement is a judgment about your pipeline:** after the
  pacing/approval process finishes, before the ad day ramps. If approvals
  land in the evening, move the cron — the default is one author's morning,
  not a recommendation.

## Escalation default

When a row's failure class is ambiguous, report and stop - never guess a
sheet edit. The sheet belongs to humans; the job here is diagnosis, not
repair. Two standing routes for what triage surfaces: "what should this
budget actually be" →
[`budget-recommendation-calculator`](../budget-recommendation-calculator/);
"is this spend pace normal for this book" →
[`portfolio-pacing-rules`](../portfolio-pacing-rules/).
