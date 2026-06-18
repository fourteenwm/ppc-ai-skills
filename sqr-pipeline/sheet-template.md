# Sheet Template

The pipeline uses one Google Sheet with a few tabs. You build the sheet; the
scripts read and write specific tabs by name. Grab the sheet ID from the URL
(`https://docs.google.com/spreadsheets/d/<THIS_IS_THE_ID>/edit`) and pass it as
`--sheet-id` to every script.

Tab names are the script defaults — override with the matching CLI flag
(`--tab-name`, `--input-tab`, `--geo-tab`, `--sqr-tab`) if you name them
differently.

---

## Tab 1: `SQR` — raw search-terms pull (written by step 0)

`mcc_search_query_report.py` writes here. Headers in row 1, data from row 2.

| Column | Header | Notes |
|--------|--------|-------|
| A | Account ID | numeric CID (no dashes) |
| B | Account Name | descriptive name |
| C | Query | the search term |
| D | Clicks | |
| E | Impressions | |
| F | Cost | dollars |
| G | Conversions | |

If you pull with your own scheduled Google Ads Script instead of step 0, just
match these 7 columns.

---

## Tab 2: `Have Cost` — classification queue (read by step 1)

`sqr_prep.py` reads this tab (range `A:I`) and batches every row where col I =
`Waiting`. Build it from the `SQR` tab — typically a QUERY/pivot that dedupes
queries per account — and add the two columns the raw pull doesn't have: your own
brand names (H) and a status (I).

| Column | Header | Notes |
|--------|--------|-------|
| A | CID | customer ID (dashed or not — both work) |
| B | Account | account name |
| C | Query | the search term to classify |
| D–G | *(metrics, optional)* | not read by prep; handy for your own filtering |
| H | Brand Names | **the advertiser's own** brand names, comma-separated (e.g. `Summit Plumbing, Summit Home Services`). Drives brand-match-first classification. |
| I | Status | `Waiting` = not yet processed (prep picks these up). Anything else is skipped unless you run prep with `--all`. |

Rows with no CID or no Query are treated as filler and skipped.

---

## Tab 3: `GEO Source` — geo targets (optional, for step 3)

Only needed if you run the optional geo conflict step. `sqr_prep.py --geo-tab "GEO Source"`
reads range `A:B`.

| Column | Header | Notes |
|--------|--------|-------|
| A | CID | customer ID (dashed or not) |
| B | Geo Targets | the locations this account actively targets, **semicolon-separated** (e.g. `Chula Vista; East Lake; Otay`) |

Omit this tab entirely to skip geo and run the core flow.

---

## Tabs 4 & 5: `3-3 Agree` / `2-3 Agree` — consensus output (written by step 4)

`sqr_compare.py` creates/overwrites these. `3-3 Agree` = all 3 runs agree (negate
candidate); `2-3 Agree` = 2 of 3 agree. Headers in row 1.

| Column | Header | Notes |
|--------|--------|-------|
| A | CID | dashed format |
| B | Query | |
| C | Account | |
| D | Brand Names | |
| E–G | R1 / R2 / R3 Category | the three independent classifications |
| H–J | R1 / R2 / R3 Geo Check | PASS/FAIL if you ran the geo step; blank otherwise |
| K–L | R1 / R2 Conflicting Geo | the colliding geo target, if any |
| **M** | **Include?** | **you mark `x` here** to approve a row for negating |
| N | Count | always 1 (handy for SUM/QUERY formulas) |

**This is the human review gate.** Read the rows, mark `x` in column M for the
queries you want to add as negatives. Mark nothing and nothing uploads.

---

## Tabs 6 & 7: `2-NGram` / `3-NGram` — phrase frequency (optional, written by step 4)

`sqr_ngram_analysis.py` creates these. Same `Include?` review pattern (column I here).

| Column | Header |
|--------|--------|
| A | CID |
| B | NGram |
| C | Account |
| D | Brand Names |
| E | Clicks |
| F | Impressions |
| G | Cost |
| H | Conversions |
| I | Include? *(mark `x`)* |
| J | Count |

---

## Tab 8: `Neg Lists` — your shared-list lookup (you maintain this)

The Uploader needs to know which shared negative keyword list to add each query
to, per account. Maintain a simple lookup mapping each account's CID to its
shared negative keyword list ID. (Find a list's ID in the Google Ads UI under
Tools → Shared library → Negative keyword lists, or query `shared_set`.)

| Column | Header | Notes |
|--------|--------|-------|
| A | Trunc CID | numeric customer ID, no dashes |
| B | Neg List ID | the shared negative keyword list ID for that account |

---

## Tab 9: `Uploader` — pending negatives (read + stamped by step 6)

`sqr_upload_negatives.py` reads range `A:E` (header in row 1) and stamps col E.

| Column | Header | Notes |
|--------|--------|-------|
| A | CID | full format (e.g. `123-456-7890`) — informational only |
| B | Query | the search term to add as a PHRASE negative — **required** |
| C | Neg List ID | shared negative keyword list ID — **required** |
| D | Trunc CID | numeric customer ID (no dashes) — **required** |
| E | Uploaded? | empty = pending; the script writes `X` after a successful upload |

### Wiring the Uploader from the agree tabs

Pull the approved rows (col M = `x`) from both agree tabs, then derive C and D:

```
# A2 — CID + Query for every approved row across both agree tabs
=QUERY({'3-3 Agree'!A2:M; '2-3 Agree'!A2:M}, "select Col1, Col2 where Col13 = 'x'", 0)

# D2 — Trunc CID (strip dashes from col A)
=ARRAYFORMULA(IF(A2:A="","", SUBSTITUTE(A2:A, "-", "")))

# C2 — Neg List ID (look up the account's shared list)
=ARRAYFORMULA(IF(A2:A="","", IFERROR(VLOOKUP(SUBSTITUTE(A2:A,"-",""), 'Neg Lists'!A:B, 2, FALSE), "")))
```

`Col13` is column M (`Include?`). Leave column E empty — the upload script writes
`X` there itself.

> **Before you run the upload:** the QUERY in A2 is a live array, so its rows
> shift if the agree tabs change. Once your review is final, copy columns A:D and
> **Paste special → values only** so the rows are static. Then the `X` the script
> stamps in column E lines up with stable rows and a re-run won't re-upload
> shifted data.
