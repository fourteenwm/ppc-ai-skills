# Update Contract — exactly what a run reads, writes, and reports

The precise mutation surface, row lifecycle, parse rules, alert shape, and
failure behavior of the Shared Budget Updater. Use this to answer "why did
the run do that?" — or "is this row safe to run again?" — without reading
the engine.

> **Source of truth:** the workflow code —
> `workflows/shared_budget_updater/main.py` (row loop, the $0 guard,
> dollars→micros), `sheets_io.py` (tab read/parse, done marks), `ads_api.py`
> (the mutation, retries, error taxonomy), `slack.py` (alert shape). This
> document mirrors the code as of its 2026-07-22 revision. If you change the
> workflow, update the matching section here and add a CHANGELOG entry.

---

## The mutation — the only write to Google Ads

One REST call per row: `POST customers/{CID}/campaignBudgets:mutate` with a
single `update` operation on `customers/{CID}/campaignBudgets/{budget_id}`
and `updateMask: amount_micros`. **The amount is the only field this tool
can ever change** — no statuses, no bidding, no campaign fields.

- **The amount is the budget's *daily* amount** — the same number the Ads
  UI shows in the budget column. That is what `amount_micros` means on a
  campaign budget: Google caps monthly delivery at ~30.4× it and may spend
  up to 2× it on any single day. What number *belongs* in a row is judgment
  — [`rules.md`](../rules.md) § the shared-budget math.
- **Dollars → micros:** `$` and commas stripped, then Decimal-rounded to
  cents (half-up) and ×1,000,000. `$1,234.565` becomes `1234.57` →
  `1234570000` micros.
- **Blind overwrite:** the workflow never reads the current amount — no
  diff, no floor, no sanity check. The row's number IS the new budget.
  Re-pushing an unchanged row therefore rewrites the same value (a no-op in
  effect) — the property that makes rerun reasoning tractable.
- **The $0-or-less guard:** if the converted amount is ≤ 0 micros ($0,
  negative, or sub-cent values that round to zero, like `0.004`), the row
  fails with `INVALID_AMOUNT` **before any API call**, alerts, and stays
  pending.

## Row lifecycle — column D is the state store

| Row state | Meaning | Who wrote it |
|-----------|---------|--------------|
| A+B+C filled, D empty | Approved, pending — pushed on the next run | A human (the approval) |
| D contains `x` | Processed — never touched again | The workflow, after a successful mutate |
| D contains *anything* non-blank | Treated exactly like `x` — skipped | Whoever put it there (which is why hand-marking cancels a change) |
| Mutation failed, D still empty | Retries automatically next run | Nobody — failure leaves no mark |

Mechanics that matter for rerun reasoning:

- Done marks are written in **one batch after the whole row loop**, not
  per-row. A crash mid-loop (or a Sheets failure at the batch write) leaves
  every already-mutated row still unmarked — the next run re-pushes them
  with identical values (benign, per the blind-overwrite property above).
  The only exposure is a human editing such a row between the crash and the
  retry.
- End-of-run order: done marks are written **before** the Slack alert is
  attempted. A Slack failure never unmarks or re-queues anything.
- Clearing an `x` re-arms that row — it pushes again next run. Judgment for
  when that's legitimate: [`rules.md`](../rules.md). Layout and column
  semantics: [`sheet-template.md`](../sheet-template.md).

## Tab ingestion — what makes a row count

The run reads full columns `A:D` of the tab (`SHEET_TAB`, default
`Shared Budget Uploader`) — the whole column, so rows never fall off the
bottom of a fixed range. Row 1 is always treated as the header. Cells are
trimmed; short rows are padded.

| Row condition | Result | Visible where? |
|---------------|--------|----------------|
| Any of A / B / C blank after trimming | Skipped | Nowhere — silent (a half-filled row is not an approval) |
| D non-blank (any value) | Skipped as already processed | Nowhere — silent by design |
| A+B+C filled, D blank | Processed this run | Run log: `Row N: CID=…, Budget=…, Amount=$…` |

Tolerated formats: CIDs may contain dashes (stripped); amounts may contain
`$` and commas (stripped at conversion).

- **A malformed amount is NOT silent.** `abc` in column C survives
  ingestion (it's a non-blank cell) and fails at conversion inside the row
  loop → alerted as `UNEXPECTED` with the parse error, row stays pending.
  Malformed data alerts; *missing* data doesn't.
- **No dedupe.** Two pending rows naming the same CID + budget ID both
  push, in row order — last write wins. Queue hygiene is human-owned
  ([`rules.md`](../rules.md)).

## The alert shape

One consolidated Slack (Block Kit) alert per run, sent **only when at least
one row failed**:

- **Header (exact):** `Shared Budget Updater: {N} row(s) skipped`
- **Body:** one bullet per failed row — row number, CID, budget ID, amount,
  then `error_code: message`, plus the offending value as `(trigger: …)`
  when the API supplied one. Truncated at 2,900 characters.
- **Hint line:** for known account-level policy blocks
  (`workflows/_shared/mutate_error_hints.py` — currently the EU political
  advertising declaration), a 👉 remediation hint is appended under the row
  so the fix arrives with the error.
- **Context line:** the optional `SLACK_USER_MENTION`, then
  `{M} other row(s) processed OK. Skipped rows still have empty Col D —
  they'll retry on the next run.`

Missing/empty `SLACK_WEBHOOK_URL` skips the alert with a run-log warning —
the run still exits 0. A failed Slack post is logged and never crashes the
run.

Separately, the workflow yml's `failure()` step posts a red-circle crash
alert with a link to the run — it fires **only when the job itself fails**
(a crash before or outside the row loop: auth, sheet read, startup). Row
failures never trigger it.

## Error taxonomy & retry envelope

Per-mutate retries in `ads_api.py`: up to **3 attempts**, waits of 2s/4s
between them. Retried: network timeouts/connection errors and HTTP 5xx.
Not retried: any 4xx — those fail straight to the alert. Each attempt has a
90s request timeout.

| `error_code` | Source | Meaning |
|--------------|--------|---------|
| `INVALID_AMOUNT` | The guard — no API call made | Amount ≤ $0 after conversion |
| `TIMEOUT` / `CONNECTION_ERROR` | Network layer, after retries | Transient — next run retries the row |
| Google Ads codes (`NOT_FOUND`, `INVALID_CUSTOMER_ID`, `USER_PERMISSION_DENIED`, `EU_POLITICAL_ADVERTISING_DECLARATION_REQUIRED`, …) | Parsed from the API error body (first error code value; `trigger` and `requestId` captured when present) | Whatever the API said — triage classes in [`rules.md`](../rules.md) |
| `UNKNOWN` | API error body unparseable | Raw response excerpt in the message |
| `UNEXPECTED` | Any non-API exception in the row loop | First 500 chars of the exception (includes malformed amounts) |

Every Sheets call (the read and the done-mark batch) goes through
`workflows/_shared/sheets_retry.py`: transient errors (HTTP 5xx and 429
rate-limit) retried up to 4 attempts with 2/4/8s waits between them.

## Run & failure contract

- **Schedule:** GitHub Actions cron `15 14 * * *` (daily, 14:15 UTC) plus
  manual `workflow_dispatch`; 5-minute job timeout.
- **Startup guards:** a missing `UPDATER_SHEET_ID` raises at import; missing
  `GOOGLE_TOKEN_PATH` / `GOOGLE_ADS_YAML_PATH` raise inside the auth
  helpers. All three crash the run before any row is touched → the yml
  `failure()` alert.
- **Empty queue:** "Nothing to process" — the run exits 0 without touching
  Google Ads, writing the sheet, or posting to Slack.
- **Per-row isolation:** each row's failure (structured API error or
  unexpected exception) is caught and recorded; the loop continues with the
  next row.
- **Exit 0 on partial failure is the contract.** The consolidated alert
  carries the failures; the run only exits non-zero on a crash.
- **There is no kill switch.** An empty queue is the idle state. To stop
  the tool entirely, disable the workflow in the GitHub UI (Actions →
  Shared Budget Updater → ⋯ → Disable workflow).
- **Credentials hygiene:** secrets are written to runner-local temp files
  at step start and deleted in an `always()` cleanup step, success or
  failure.

## Reading run state cold

The sheet tab is both the queue and the receipt; two surfaces tell a fresh
session everything, without Slack history:

1. **The tab itself** — `x` in column D = that row was applied. Filled
   A/B/C with an empty D after a green run = the row failed (or was added
   after the run) — the log distinguishes which.
2. **The Actions run log** (Actions → Shared Budget Updater → latest run) —
   every processed row logs `Row N: CID=…, Budget=…, Amount=$…` followed by
   `-> Budget updated` or `SKIPPED row N … [code] message`, then
   `Marked N row(s) done in sheet` and a closing `SUMMARY` block
   (total / processed / errors).

The Ads-side receipt, when you want one, is the budget's change history —
routed via [`SKILL.md`](../SKILL.md). Slack absence proves nothing: a
missing webhook and a failed post are both log-only.

## Environment variables

All identity-bearing configuration. The GitHub-secrets mapping (what to
paste where) is `README.md` Step 5; this is what the code reads at runtime:

| Env var | Required | Purpose / behavior when missing |
|---------|----------|--------------------------------|
| `UPDATER_SHEET_ID` | Yes | Sheet ID where the uploader tab lives. Missing = crash at startup (yml crash alert) |
| `SHEET_TAB` | No (default `Shared Budget Uploader`) | Tab name; an empty string falls back to the default |
| `GOOGLE_TOKEN_PATH` | Yes | Path to the Google Sheets OAuth user token JSON. Missing = crash |
| `GOOGLE_ADS_YAML_PATH` | Yes | Path to the Google Ads API YAML config. Missing = crash |
| `SLACK_WEBHOOK_URL` | Effectively yes | Failure alerts. The one variable whose absence does NOT crash — alerts are silently skipped (log-only), so treat it as required |
| `SLACK_USER_MENTION` | No | Slack user/group to @-mention on alerts (e.g. `<@U12345>`) |

## Parity with the production twins

This bundle is the generic replica of **two** production installs of the
same architecture (two separate account books, one codebase pattern). They
stay in **behavioral sync** on the parity set, which is exactly the
contract above:

- Mutation surface: `updateMask: amount_micros` only, blind overwrite,
  dollars→micros conversion (§ The mutation)
- The $0-or-less guard (§ The mutation)
- Row lifecycle: empty-D retry semantics, batch-mark-after-loop,
  marks-before-alert order (§ Row lifecycle)
- Ingestion ladder and tolerated formats (§ Tab ingestion)
- Consolidated alert shape + remediation hints (§ The alert shape)
- Error taxonomy and both retry envelopes (§ Error taxonomy)
- Exit-0-on-partial-failure (§ Run & failure contract)

**Different by design — never synced:** environment-variable names and
sheet wiring (the production twins pin their own pacing sheets with
hardcoded fallbacks; this bundle is env-only with no fallbacks), Slack
headers/branding and the twins' hardcoded fallback @-mention (this bundle
is env-only), and module docstrings. Drift between the copies is reviewed
against the parity set, hunk by hunk — never byte-synced.

**If you deploy this:** the parity set binds the author's twins, not your
install. Your copy is yours to adapt — the boundary that should survive any
fork is the mutation surface: amount only, ever.
