# Scan Contract — tree walk, classification, outputs, API limitations

> **Source of truth:** `scripts/mcc_hack_audit.py` — the script wins over
> this document. Mirrors the shipped revision as of 2026-07-23. Any behavior
> change in the script must update this contract and the CHANGELOG in the
> same commit.

Exactly what the scan queries, how links are classified, and what lands where.
Judgment about *reading* the results lives in [`rules.md`](../rules.md).

## Tree walk

- One `customer_client` query from your `login_customer_id` (read from your
  credentials YAML — the `--config` path, default `google-ads.yaml`; unset →
  hard exit). **No status filter** — every
  node comes back: ENABLED, CANCELED, SUSPENDED, CLOSED, managers and
  clients, **including your root MCC itself** (so the scan also surfaces who
  manages YOUR tree — see rules on reading rows where the account is your
  own login CID).
- Internal-manager set = every walked node with `manager = true`, plus the
  login CID itself. This is what INTERNAL classification checks against —
  auto-detected, never configured.
- The walk selects `customer_client.hidden` and `customer_client.test_account`
  but the script never stores or uses them — fetched-unused fields, not a
  behavior lever.

## Per-account link query

- Each walked account gets its own `customer_manager_link` query
  (`manager_customer`, `manager_link_id`, `status`) on a thread pool
  (`--workers`, default 20).
- **No link-status filter** — ACTIVE, INACTIVE, PENDING, REFUSED, and
  CANCELED links all return. A REFUSED or CANCELED row is not live access;
  it's an *attempt record*, and attempt records are security data
  (`rules.md`).
- **Error isolation:** an account whose query throws contributes **zero
  rows** — it is entirely absent from both CSVs. The error is counted on the
  console (first line of the exception, truncated to 120 chars) but **never
  listed per-account and never persisted**. Absence from the CSV therefore
  means "query failed" (typically CANCELED/CLOSED permission errors), never
  "no managers."

## Classification — precedence order

Each (account, manager) row is classified by the manager CID, first match
wins:

1. **HOSTILE** — CID present in your `--hostile-list` JSON. Checked FIRST:
   a hostile entry beats everything, so a compromised MCC *inside* your own
   tree still shows HOSTILE if you've listed it.
2. **INTERNAL** — CID in the walked internal-manager set.
3. **TRUSTED** — CID in `--trusted-cids`. Label is always
   `user-marked trusted (re-audit on a cadence)`.
4. **EXTERNAL** — everything else. No other input can make a link EXTERNAL
   "legitimate" — there is no allowlist concept beyond the explicit TRUSTED
   suppression.

Input hygiene: hostile-list keys, trusted CIDs, and the login CID are all
dash-stripped before comparison.

## CSV contract (always written)

`--output-dir` (default `output/`), filenames **datestamped to the day**:

- `mcc_link_scan_YYYYMMDD.csv` — every (account, manager) pair, sorted by
  account CID then link_id descending. Columns: `account_cid`,
  `account_name`, `account_status`, `manager_cid`, `manager_link_id`,
  `link_status`, `classification`, `label`.
- `mcc_link_scan_YYYYMMDD_SUSPICIOUS.csv` — **HOSTILE + EXTERNAL rows only**
  (TRUSTED rows are excluded here — that's exactly the visibility
  `--trusted-cids` suppresses), HOSTILE first, then by link_id descending
  (newest links first).

**A same-day re-run overwrites both files; runs on different days
accumulate.** That accumulation is the substrate for the manual watchdog
pattern: diff today's CSV against the last run's to see new links
(`rules.md`, cadence).

No row carries a time — the filename's date is the only stamp.

## Google Sheets upload (optional, `--sheet-id`)

- Auth is `gspread.service_account()` — service-account JSON at gspread's
  default location, sheet shared with that service account. gspread missing →
  warning + skip, never fatal.
- Four tabs, each **cleared and fully rewritten** (created if missing):
  `All Manager Links`, `Suspicious Links` (same populations/sorts as the two
  CSVs), `Managers and Their Accounts` (one row per distinct manager with
  account count, sorted HOSTILE → EXTERNAL → rest, then by count), and
  `Internal Managers` (your detected tree MCCs, by level then name).

## Console output

Startup echoes the config (`Logged in via MCC:`, `Workers:`, hostile/trusted
counts), the walk reports
`Found N total accounts (M are internal managers)`, progress prints every
250 completions (and once at the end) with rate/ETA/error count, and the
summary block ends the run:

```
======================================================================
MCC HACK AUDIT — SUMMARY
======================================================================
Total manager links: 231
Errors (CANCELED/CLOSED accounts): 7 (expected)
Distinct managers seen: 12
```

then a classification breakdown (fixed order HOSTILE / EXTERNAL / TRUSTED /
INTERNAL) and, if any HOSTILE rows exist, a per-row
`WARNING: HOSTILE MCCs ACTIVELY LINKED` block. That block's header overstates:
it prints for every HOSTILE-*classified* row with **no `link_status` check** —
a revoked (CANCELED) link to a convicted CID still triggers it. Live access
is what the `link_status` column says, not what the banner says.

**The error line's label is an assumption, not a diagnosis** — the script
counts every exception under "CANCELED/CLOSED accounts (expected)" without
checking the cause. The healthy signature and the unhealthy one are a rules
call (`rules.md`, false-alarm table).

## Hostile list format (`--hostile-list`)

JSON dict of CID → one-line context; authoritative shape (also shown in
`SKILL.md` at the run surface):

```json
{
  "1234567890": "label or context for this hostile MCC",
  "0987654321": "another known-bad CID with a one-line note"
}
```

Missing file path → hard exit. No file shipped, no central registry — start
empty, populate as incidents occur.

## API limitations (hard-won; do not regress)

Field-verified against a ~10,000-account production tree:

1. **`customer.descriptive_name` is not exposed for external MCCs.** Direct
   lookup on a non-internal CID returns permission denied — the UI's Account
   Access page is the only way to put a name on a suspicious CID.
2. **`customer_manager_link.start_time` is documented but rejected**
   (`UNRECOGNIZED_FIELD`). `manager_link_id` is the chronological proxy —
   IDs increase monotonically, so higher = more recent. Both CSVs sort by it.
3. **`change_event` does not record manager-link acceptances.** Post-link
   mutations show; the link event itself never does. "Who clicked accept" is
   UI Change History / Google Support territory.
4. **CANCELED/CLOSED accounts still hold manager-link history** — which is
   why the walk keeps them. Their queries often error fast (that's the
   expected error population), but when they answer, the data matters most.
5. **20 workers is the tested sweet spot.** Higher rates risk
   `RESOURCE_EXHAUSTED` throttling; drop to `--workers 10` when throttled.

## Reading run state cold

The datestamped CSVs in `output/` are the run record — a directory listing
tells a cold session which days were scanned; diffing two days' full CSVs
shows link churn. What the files can't tell you: **which accounts errored out
of the scan** (console-only, gone with the scrollback) — so a cold read of an
old CSV should treat missing accounts as unknowns, not as manager-free.
