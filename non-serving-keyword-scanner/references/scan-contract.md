# Scan Contract — exactly what the scanner selects, writes, and reports

The precise selection criteria, output format, and failure behavior of the
scan. Use this to answer "why is this keyword on the list?" (or "why isn't
it?") without reading the engine.

> **Source of truth:** `scripts/non_serving_keyword_scan.py`. This document
> mirrors the script as of its 2026-07-17 revision. If you change the scan in
> the script, update the matching section here and add a CHANGELOG entry.

---

## Selection criteria — what earns a row

The scan queries `keyword_view` (keywords only, by construction — no explicit
type filter is needed). A keyword appears in the report only if **all** of
these hold:

| Condition | GAQL clause | Why it's there |
|-----------|-------------|----------------|
| Keyword is enabled | `ad_group_criterion.status = 'ENABLED'` | Paused keywords are already handled — the scan reviews live structure only |
| Its ad group is enabled | `ad_group.status = 'ENABLED'` | A keyword in a paused ad group can't serve; flagging it would be noise |
| Its campaign is enabled | `campaign.status = 'ENABLED'` | Same — only keywords that are *eligible right now* are candidates |
| Campaign is Search | `campaign.advertising_channel_type = 'SEARCH'` | PMax/Display/Video don't use this keyword model; a Search-less account legitimately returns zero rows |
| Zero impressions across the window | `metrics.impressions = 0` over `segments.date BETWEEN` the window | The definition of non-serving: not one auction entry in the whole span |

**Window semantics:** the window is the `--days` span ending today (flag and
default: SKILL.md → How to Run). Metrics are summed across the entire span —
one impression anywhere in it removes the keyword from the report.

**The status/window asymmetry — the scan's main blind spot.** Status filters
are evaluated against *current* state; metrics cover the *whole window*. A
campaign or ad group that was paused for part of the window and re-enabled
recently passes every status filter, but its keywords had no chance to serve
while the parent was dark — they'll flag as non-serving even if perfectly
healthy. Same for keywords added mid-window. The false-signal table in
[`rules.md`](../rules.md) exists largely because of this asymmetry.

**What the scan cannot see:**

- Keywords, ad groups, or campaigns that are currently paused or removed —
  this is a live-structure review, not a historical audit.
- Google's keyword statuses (`system_serving_status`, e.g. "Low search
  volume") — the query doesn't pull them; verify in the UI when a row's read
  depends on it.
- *Why* a keyword never served (rank, negatives, volume) — the scan reports
  the fact; diagnosis routes per `rules.md`.

## Post-filter exclusions

After the query, rows are dropped when the ad group's name — lowercased,
compared whole — is `special` or `specials`. These are dynamic-pricing ad
groups where keywords cycle in and out by design; their zero-impression rows
are churn, not rot.

**Exact-name match only.** An ad group named "Spring Specials" or "Weekly
Special Offers" does NOT match and its keywords WILL be scanned. If your
account uses other cycling/dynamic ad groups, their rows land in the report —
treat them per the false-signal table rather than editing the exclusion list.

## Output contract — the review tab

Written to the sheet you pass via `--sheet-id`, in the tab named by
`--tab-name`:

- **Created if missing** (sized 1,000 rows × 15 columns at creation),
  **cleared and rewritten if present**. The tab is a snapshot of this run,
  never an append log.
- **Run stamp:** cell **L1** gets `Last Scan: YYYY-MM-DD HH:MM:SS` — how you
  (or a cold session) tell when the tab was last written.
- **Empty result = sheet untouched.** When the scan finds nothing, no clear,
  no write, no stamp update — the console says
  `No non-serving keywords found. Sheet not updated.` A tab left over from an
  earlier run will still show that earlier run's rows and stamp, so check the
  stamp before trusting old rows.

Columns, A–J:

| Column | Contents |
|--------|----------|
| Account Name | From the API (`customer.descriptive_name`), falling back to the name in your account source |
| CID | Customer ID, digits only |
| Campaign / Ad Group / Keyword | Where the keyword lives, and its text |
| Match Type | `EXACT`, `PHRASE`, or `BROAD` |
| Impressions (Nd) | Always 0 — the header carries the window length |
| Clicks / Conversions | Expected 0 (clicks require impressions on Search) |
| Cost | Expected `$0.00` — formatted as dollars |

Clicks, conversions, and cost are structurally zero for a zero-impression
Search keyword — the columns exist as an instrument check. A nonzero value
there means the read is broken somewhere; report it rather than interpreting
the row.

## Account-source resolution

Four flags, mutually exclusive; with none given the script defaults to
reading `./accounts.md`:

| Source | Behavior |
|--------|----------|
| `--cid` / `--cids` | Digits-only CIDs, taken as given; display names default to `Account <cid>` until the API returns descriptive names |
| `--all` | Walks `customer_client` under the `login_customer_id` in your `google-ads.yaml` — enabled, non-manager accounts only. Exits with an error if the yaml has no `login_customer_id` |
| `--accounts PATH` (and the no-flag default `./accounts.md`) | Parses `### CID:` headers in the **dashed** `123-456-7890` form — a bare 10-digit header will not parse. First `- Name` line under each header is the display name. Copy the shipped [`accounts.example.md`](../accounts.example.md) — the format is documented inside it |

A missing or unparseable accounts file prints the three-mode help and exits —
no traceback.

## Failure & progress contract

- **Per-account API errors don't kill the run.** A failing account is
  reported and the scan continues with the rest.
- **Read the progress lines, not just the summary.** An account whose GAQL
  call fails prints `API Error: <message>` inline and then counts as
  `0 non-serving keywords` in the progress output — a zero next to an API
  error is an unscanned account, not a clean one. Only non-API failures
  (network, auth) land in the end-of-run `Failed accounts` list.
- **Sheet write failures:** a 403 on the write step means the refresh token
  lacks the Sheets scopes — the script prints the fix (re-run the
  [`google-ads-api-setup`](../../google-ads-api-setup/) generator once).
