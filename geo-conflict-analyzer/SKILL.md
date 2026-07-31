---
name: geo-conflict-analyzer
description: Analyze search queries for geographic targeting conflicts in GEO campaigns. Uses OpenAI GPT-4o to determine if queries should PASS (no conflict - safe to add as negative) or FAIL (conflict detected - do NOT negative). Auto-invoke when user mentions "geo conflict check", "analyze geo conflicts", or after running off-brand analysis.
---

# GEO Conflict Analyzer

The last safety gate before a negative-keyword upload: checks each
candidate query against the geos an account actively targets, so you
never negative your own live traffic. Verdicts are PASS (no conflict —
geo-safe to negative) or FAIL (conflict — do NOT negative). How to read
the verdicts is [rules.md](rules.md); exact script mechanics are
[`references/analysis-contract.md`](references/analysis-contract.md);
the classification ruleset itself is [prompt.md](prompt.md).

---

## What It Does

1. Reads queries from a Google Sheet tab where a status column =
   "Waiting", with each row carrying its account's active geo targets
   (column H)
2. Sends **one batch per run** (default 50) to OpenAI GPT-4o with the
   prompt.md ruleset
3. Appends PASS/FAIL + confidence results to an output tab

Pairs with [`sqr-pipeline`](../sqr-pipeline/) — its off-brand
classification runs first; this check protects active geo targets before
anything is negatived.

---

## What this skill deliberately does NOT do

- **Doesn't pull queries or geo targets from Google Ads.** The input
  sheet is upstream's product; column H is the ground truth the model
  sees, current or not. No Google Ads API anywhere — Sheets + OpenAI
  only.
- **Doesn't upload or remove negatives.** PASS rows flow back to your
  upload workflow (sqr-pipeline or Editor); FAIL rows come off the list.
- **Never updates the input tab.** Status stays "Waiting" after every
  run — flipping it is your step, and skipping it duplicates work and
  spend (contract).
- **Never creates tabs.** Both tabs must exist; a mistyped output tab
  fails *after* the OpenAI call is paid for.
- **Doesn't decide query intent.** Whether a query is junk was upstream's
  call; this skill only answers "does negativing it break active geo
  targeting?"

---

## Configuration

All configuration is passed via CLI args or environment variables. No hardcoded IDs.

| Setting | Default | How to set |
|---------|---------|------------|
| Spreadsheet ID | *(required)* | `--sheet-id` arg or `GEO_SHEET_ID` env var |
| Input Tab | `Have Cost - GEO` | `--input-tab` arg |
| Output Tab | `Have Cost Result - GEO` | `--output-tab` arg |
| Batch size | 50 | `--batch-size` arg |
| Model | `gpt-4o` | `--model` arg |
| OpenAI key | *(required)* | `OPENAI_API_KEY` env var (from `.env`) |
| Sheets token | `./token.json` | `--token` arg |

---

## Usage

### Basic (50 rows default)
```bash
python scripts/analyze.py --sheet-id YOUR_SHEET_ID
```

### Custom batch size
```bash
python scripts/analyze.py --sheet-id YOUR_SHEET_ID --batch-size 100
```

### Dry run (no writes)
```bash
python scripts/analyze.py --sheet-id YOUR_SHEET_ID --dry-run
```

Batch size is a cost/reliability dial — one run is one model call, and
oversized batches truncate ([rules.md](rules.md) § operational rules).

---

## Input Format

Reads from the input tab with columns:
- **Column A** — CID (Customer ID)
- **Column B** — Account name
- **Column C** — Query (search term)
- **Column H** — GEO Names (comma-separated list of actively targeted geos for that CID)
- **Column I** — Status (filters for "Waiting")

A Waiting row with an empty column H is skipped silently, forever — the
first thing to check when a row never processes (contract).

---

## Output Format

Each result row contains:
- **CID** — Customer ID
- **Query** — The search query analyzed
- **Geo_Check** — PASS or FAIL
- **Conflicting_Geo** — If FAIL, which geo target it conflicts with
- **Confidence** — HIGH / MEDIUM / LOW

Results **append** to the output tab (nothing is cleared, no headers are
written, no run-date column exists) — history accumulates and position is
the only ordering (contract).

---

## PASS/FAIL Logic

### PASS (No Conflict — Safe to Negative)
- Query does NOT match any of the active geo targets
- Safe to add as a negative keyword — won't block our active keywords

### FAIL (Conflict Detected — Do NOT Negative)
- Query DOES match our active geo targets (exact or fuzzy match)
- Includes: abbreviations, typos, prepositions, modifiers of our target geos
- Do NOT negative — would block keywords we're actively bidding on

See `prompt.md` for the full ruleset — the specificity ladder, the
default-to-FAIL rule, and 95 worked verdict examples. Reading the output
(confidence triage, real-conflict-vs-noise classes) is
[rules.md](rules.md).

---

## Prerequisites

1. **OpenAI API Key** — Set `OPENAI_API_KEY` in a `.env` file at project root, or export it as an environment variable
2. **Google Sheets Token** — OAuth credentials at `./token.json` (or pass a custom path via `--token`)
3. **Input sheet** — A Google Sheet with the expected column structure (see Input Format above)

### First-time OAuth setup

You'll need Google Sheets API credentials. See the [Google Ads API Setup skill](../google-ads-api-setup/) for the OAuth walkthrough — the same `token.json` can be used here with the Sheets scope added.

---

## Dependencies

```bash
pip install openai google-auth google-api-python-client python-dotenv
```

---

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | This file — workflow + routing |
| `rules.md` | Judgment layer: verdict+confidence triage, conflict-vs-noise classes, operational rules, escalation |
| `examples.md` | Three worked reads incl. the property-name call and the duplicate-append trap |
| `prompt.md` | The classification ruleset (95 worked examples). **Runtime dependency:** `analyze.py` loads this file from the skill folder on every run and sends it as the system prompt — missing file is a hard error, and edits change verdicts on the next run |
| `references/analysis-contract.md` | Line-derived script mechanics: selection, batching, parsing, append semantics, the never-flips-status invariant |
| `scripts/analyze.py` | Main execution script |
| `README.md` | User-facing overview + install |

---

## After a Run

New verdict rows sit at the **bottom** of the output tab (append-only,
contract). The input tab is untouched — **flip Status on accepted rows
now**, or the next run re-analyzes and duplicates them. `token.json` may
show a fresh mtime (refresh side effect, expected). Console output isn't
persisted; the output tab is the only record that the run happened.

---

## When to Load What

| Moment | Load |
|---|---|
| Reading any output — FAIL triage, LOW-confidence rows, noise classes | [rules.md](rules.md) |
| Exact selection/parsing/append mechanics, cost/truncation questions | [references/analysis-contract.md](references/analysis-contract.md) |
| First read, or output rows outnumber input queries | [examples.md](examples.md) |
| Why a specific verdict — the ladder, the fuzzy rules | [prompt.md](prompt.md) |
| The full pipeline this gates (classification → review → upload) | [sqr-pipeline](../sqr-pipeline/) — its optional step 3 runs this same check in-pipeline with its own inline prompt; this skill is the standalone sheet-driven variant |
| Quick intent classification without the pipeline | [sqr-classifier](../sqr-classifier/) |
| Sheets OAuth setup | [google-ads-api-setup](../google-ads-api-setup/) |
