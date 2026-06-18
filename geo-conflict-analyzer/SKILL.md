---
name: geo-conflict-analyzer
description: Analyze search queries for geographic targeting conflicts in GEO campaigns. Uses OpenAI GPT-4o to determine if queries should PASS (no conflict - safe to add as negative) or FAIL (conflict detected - do NOT negative). Auto-invoke when user mentions "geo conflict check", "analyze geo conflicts", or after running off-brand analysis.
---

# GEO Conflict Analyzer

Analyze search queries for geographic targeting conflicts in GEO campaigns. Uses OpenAI GPT-4o to determine if queries should PASS (no conflict — safe to add as negative) or FAIL (conflict detected — do NOT negative, we actively target this geo).

---

## Triggers

- `run geo conflict analyzer`
- `analyze geo conflicts`
- `geo conflict check`

---

## What It Does

1. Reads queries from a Google Sheet tab where a status column = "Waiting"
2. Sends batches to OpenAI GPT-4o for geo conflict analysis
3. Writes PASS/FAIL + confidence results to an output tab

Pairs naturally with [`offbrand-analyzer`](../offbrand-analyzer/) — run off-brand classification first, then geo-conflict analysis on queries that need geographic validation before being negatived.

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

---

## Input Format

Reads from the input tab with columns:
- **Column A** — CID (Customer ID)
- **Column B** — Account name
- **Column C** — Query (search term)
- **Column H** — GEO Names (comma-separated list of actively targeted geos for that CID)
- **Column I** — Status (filters for "Waiting")

---

## Output Format

Each result row contains:
- **CID** — Customer ID
- **Query** — The search query analyzed
- **Geo_Check** — PASS or FAIL
- **Conflicting_Geo** — If FAIL, which geo target it conflicts with
- **Confidence** — HIGH / MEDIUM / LOW

---

## PASS/FAIL Logic

### PASS (No Conflict — Safe to Negative)
- Query does NOT match any of the active geo targets
- Safe to add as a negative keyword — won't block our active keywords

### FAIL (Conflict Detected — Do NOT Negative)
- Query DOES match our active geo targets (exact or fuzzy match)
- Includes: abbreviations, typos, prepositions, modifiers of our target geos
- Do NOT negative — would block keywords we're actively bidding on

See `prompt.md` for the full 200+ example ruleset.

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
| `SKILL.md` | This documentation |
| `prompt.md` | GPT system prompt with PASS/FAIL rules (200+ examples) |
| `scripts/analyze.py` | Main execution script |
| `README.md` | User-facing overview |

---

## Related Skills

- [`offbrand-analyzer`](../offbrand-analyzer/) — Stage 1 of the SQR pipeline (classify queries as high-intent/off-brand/informational/low-intent)
- [`sqr-pipeline`](../sqr-pipeline/) — End-to-end SQR negative-keyword pipeline (3-run consensus → review → two-step upload); this geo check is its optional step
