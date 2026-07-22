---
name: non-serving-keyword-scanner
description: "Scans your accounts for enabled Search keywords with zero impressions over a window (default 180 days) and writes one review tab to a Google Sheet — every row then gets a Pause/Keep/Investigate verdict per rules.md. Report-only, never pauses. Auto-invoke when user says 'scan non-serving keywords', 'find dead keywords', 'keyword cleanup report', or 'non-serving keyword scan'."
allowed-tools: [Bash, Read]
---

# Non-Serving Keyword Scanner

Finds the keywords nobody knows exist: enabled, eligible, and silent — zero
impressions across the whole scan window. Across a large portfolio these
accumulate into hundreds of rows of clutter and false coverage ("we're
covering that term" — except it never serves). One run scans every account
you point it at and produces a single review tab.

One operator owns the workflow end to end: run the scan → triage the tab
(`rules.md` — clusters before rows) → give every row a Pause / Keep /
Investigate verdict → route what needs routing. The scanner itself never
pauses anything; it is a hygiene instrument, not a savings instrument —
every flagged keyword spent $0.00 by definition.

---

## Invocation Triggers

Auto-invoke when user says:

- "Scan non-serving keywords"
- "Find dead keywords"
- "Keyword cleanup report"
- "Non-serving keyword scan"

---

## How to Run

```bash
# Scan a single account — fastest first run
python scripts/non_serving_keyword_scan.py --cid 1234567890 --sheet-id YOUR_SHEET_ID

# Scan multiple accounts
python scripts/non_serving_keyword_scan.py --cids "1234567890,2345678901" --sheet-id YOUR_SHEET_ID

# Scan all enabled accounts under your MCC (walks customer_client)
python scripts/non_serving_keyword_scan.py --all --sheet-id YOUR_SHEET_ID

# Scan a curated account list (copy accounts.example.md to accounts.md and edit)
python scripts/non_serving_keyword_scan.py --accounts accounts.md --sheet-id YOUR_SHEET_ID
```

**Required:** `--sheet-id` (any Google Sheet you own — the ID between `/d/`
and `/edit` in its URL).

**Account selection — three modes, mutually exclusive** (no account flag =
the script defaults to `--accounts accounts.md`):

- `--cid CID` / `--cids CID1,CID2,...` — explicit accounts, digits only
- `--all` — every enabled account under your MCC's `login_customer_id`
- `--accounts PATH` — curated markdown list; a starter template ships as
  [`accounts.example.md`](accounts.example.md) with the format documented
  inside it — copy to `accounts.md` and edit

Run with no usable account source and the script prints the mode list above
instead of a traceback.

**Optional flags:**

- `--days N` — zero-impression window (default: 180)
- `--tab-name NAME` — sheet tab (default: `"Non-Serving Keywords"`); use
  dated names for run-over-run history, since the tab is rewritten each run
- `--config PATH` — `google-ads.yaml` location (default: `./google-ads.yaml`)

**Runtime:** ~3–5 seconds per account; plan ~3–5 minutes for a ~50-account
MCC.

---

## After the run — operator duties

The script writing the tab is the midpoint of this skill, not the end. On
every run:

1. **Present the summary** — accounts scanned, accounts with findings, total
   flagged keywords, and any failed accounts (an inline `API Error` next to
   a zero means *unscanned*, not clean — see
   [`references/scan-contract.md`](references/scan-contract.md)).
2. **Read [`rules.md`](rules.md) before any verdict** — triage clusters
   before rows (a whole account flagged is an outage, not keyword rot), and
   rule out the false signals: re-enabled or newly launched campaigns,
   keywords added mid-window, seasonal terms, low-search-volume suppression.
3. **Give every surviving row one of the three verdicts** — Pause / Keep /
   Investigate, defined in `rules.md`. Ambiguous rows default to
   Keep + Investigate, never Pause.
4. **Route what needs routing:**
   - Dense clusters (whole account or campaign flagged) →
     [`account-diagnostic`](../account-diagnostic/) for the upstream
     diagnosis; auction-side campaign questions →
     [`impression-share-diagnostics`](../impression-share-diagnostics/)
   - A keyword that *should* serve but doesn't → suspect a blocking
     negative first: [`neg-conflict-finder`](../neg-conflict-finder/)
   - A query being absorbed by a broader keyword elsewhere → confirm with
     an ad-hoc pull ([`google-ads-query`](../google-ads-query/)), steer
     with negatives via the [`sqr-pipeline`](../sqr-pipeline/) review gate
   - Pause verdicts → a human executes them in the Google Ads UI or Editor
5. When asked *why* a row is (or isn't) on the list, answer from
   [`references/scan-contract.md`](references/scan-contract.md) — exact
   selection criteria, not paraphrase. [`examples.md`](examples.md) shows
   the expected shape of a full triage read.

---

## What this skill deliberately does NOT do

- **No pausing, ever.** Report-only by design — the human review step IS the
  product. Pause execution happens in the UI/Editor; if pausing ever gets
  scripted, that script is a separate tool behind the
  [`mutation-safety`](../mutation-safety/) approval flow.
- **No savings claims.** Flagged keywords have zero impressions, therefore
  zero clicks and zero spend. The payoff is structural hygiene — never
  present the tab as recoverable budget.
- **No root-cause diagnosis.** The scan says *which* keywords never served,
  not *why*. Why routes per `rules.md`: [`account-diagnostic`](../account-diagnostic/),
  [`neg-conflict-finder`](../neg-conflict-finder/),
  [`impression-share-diagnostics`](../impression-share-diagnostics/).
- **No archaeology.** Current-state review only — keywords, ad groups, and
  campaigns that are already paused are invisible to it (which is also why
  a row vanishing between runs is not proof of recovery — `rules.md`).
- **No non-Search coverage.** Search campaigns only; PMax/Display/Video
  don't use this keyword model. An account with no Search campaigns
  legitimately returns zero rows.

---

## Files in this skill

| File | Purpose |
|------|---------|
| `SKILL.md` | This file — how to run + what the operator does with the tab |
| `README.md` | Zero-context setup guide: install, prerequisites, first run |
| `rules.md` | Triage decision logic — read after every run, before any verdict |
| `examples.md` | Worked reads: routine triage, an account-level outage, a false recovery |
| `references/scan-contract.md` | Exact selection criteria, output columns, failure behavior |
| `accounts.example.md` | Copyable starter for the curated account-list mode |
| `scripts/non_serving_keyword_scan.py` | The scan engine (read-only GAQL + one sheet write) |
| `diagrams/` | Workflow diagrams used by the README |

---

## Output

One review tab in the sheet you passed (`--tab-name`, default
`"Non-Serving Keywords"`), stamped with the run time — created if missing,
**cleared and rewritten** on every run with findings, and left untouched on
a clean run (a stale tab keeps its old stamp — check it). Columns and exact
write behavior: [`references/scan-contract.md`](references/scan-contract.md).

---

## Prerequisites

- **Credentials:** `google-ads.yaml` at project root — see the
  [google-ads-api-setup](../google-ads-api-setup/) skill if you don't have
  one. The sheet-writing step reuses this same file's OAuth credentials for
  the Sheets API — its refresh token must carry the `spreadsheets` +
  `drive.readonly` scopes, which the setup skill's generator grants by
  default (token predates that? re-run the generator once — a 403 on the
  write step is this)
- **Output sheet:** any Google Sheet you own — you pass its ID via
  `--sheet-id`
- **Python packages:** `pip install google-ads gspread google-auth pyyaml`

---

## Safety

Read-only against Google Ads — the scan runs GAQL SELECT queries exclusively
and never mutates an account. Its only write is the review tab, into a sheet
you own. Acting on the findings is a separate, human-executed step (see the
boundary above and [`mutation-safety`](../mutation-safety/)).
