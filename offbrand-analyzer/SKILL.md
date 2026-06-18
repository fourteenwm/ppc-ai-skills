---
name: offbrand-analyzer
description: Classify search queries as High Intent, Low Intent, Informational, or Off-Brand using OpenAI GPT-4o with brand names and competitor list. Auto-invoke when user says "run offbrand analyzer", "analyze offbrand queries", "offbrand check", "classify search terms", or "categorize queries by intent".
allowed-tools: [Bash, Read]
---

# Off-Brand Analyzer

Analyze search queries to categorize them as High Intent, Low Intent, Informational, or Off-Brand. Uses OpenAI GPT-4o to classify queries based on brand names and a comprehensive competitor list.

---

## Triggers

- `run offbrand analyzer`
- `analyze offbrand queries`
- `offbrand check`

---

## What It Does

1. Reads queries from **"Have Cost"** tab (where Column I = "Waiting")
2. Sends batches to OpenAI GPT-4o for categorization
3. Writes results to **"Have Cost Result"** tab

---

## Configuration

| Setting | Value |
|---------|-------|
| Spreadsheet ID | `YOUR_SHEET_ID` |
| Input Tab | `Have Cost` |
| Output Tab | `Have Cost Result` |
| Default Batch Size | 50 |
| Model | `gpt-4o` |

---

## Usage

### Single batch (50 rows default)
```bash
python .claude/skills/offbrand-analyzer/scripts/analyze.py
```

### Custom batch size
```bash
python .claude/skills/offbrand-analyzer/scripts/analyze.py --batch-size 100
```

### Dry run (no writes)
```bash
python .claude/skills/offbrand-analyzer/scripts/analyze.py --dry-run
```

### Run all pending queries (recommended)
```bash
python .claude/skills/offbrand-analyzer/scripts/analyze.py --run-all
```

### Full pipeline: Stage 1 + Stage 2 (GEO Conflict Analyzer)
```bash
python .claude/skills/offbrand-analyzer/scripts/analyze.py --run-all --chain-geo
```

### Full pipeline with QA gate (recommended for production)
```bash
python .claude/skills/offbrand-analyzer/scripts/analyze.py --run-all --chain-geo --with-qa
```

This runs:
1. **Clear** output tabs (fresh start)
2. **Stage 1** - Off-Brand categorization
3. **Stage 2** - GEO conflict analysis
4. **Stage 3** - QA gate validation

If QA fails (<95% success rate), automatically retries up to 3 times.
After 3 failures, generates an error analysis report.

### QA gate only (validate existing results)
```bash
python .claude/skills/offbrand-analyzer/scripts/qa_gate.py --sheet-id YOUR_SHEET_ID
```

If the `geo-conflict-analyzer` skill is installed as a sibling (with its own
`qa_results.py`), the gate runs unified offbrand + GEO QA. Otherwise it runs
offbrand-only and reports that GEO was skipped.

### Custom QA threshold
```bash
python .claude/skills/offbrand-analyzer/scripts/analyze.py --with-qa --qa-threshold 90
```

---

## Input Format

Reads from "Have Cost" tab:
- **Column A** - CID (Customer ID)
- **Column B** - Account name
- **Column C** - Query (search term)
- **Column H** - Brand Names (approved brands for this account)
- **Column I** - Completed? (filters for "Waiting")

---

## Output Format

Each result row contains:
- **CID** - Customer ID
- **Query** - The search query analyzed
- **Category** - One of: `high intent`, `low intent`, `informational`, `off-brand`

---

## Categories

### High Intent
- Contains approved brand terms (with variations/misspellings)
- Location + apartments/rentals queries
- Bedroom types, property features
- Zip codes + apartments

### Off-Brand
- Competitor property names (from off-brand list)
- Competitor websites/domains
- Non-approved property names
- Includes misspellings and variations

### Informational
- Research queries ("how to", "what is", "best apartments in")
- General information seeking
- Not conversion-focused

### Low Intent
- Generic/vague queries ("apartment near me")
- Too broad to convert
- Not explicitly informational

---

## Prerequisites

1. **OpenAI API Key** — Set `OPENAI_API_KEY` in a `.env` file at project root, or export it as an environment variable
2. **Google Sheets Token** — OAuth credentials at `./token.json` with Sheets read/write scope

### First-time OAuth setup

See the [google-ads-api-setup skill](../google-ads-api-setup/) for the OAuth walkthrough. The same `token.json` can be used here with the Sheets scope added.

---

## Dependencies

- `openai` - OpenAI Python SDK
- `google-auth` - Google authentication
- `google-api-python-client` - Google Sheets API
- `python-dotenv` - Load .env files

Install if needed:
```bash
pip install openai google-auth google-api-python-client python-dotenv
```

---

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | This documentation |
| `prompt.md` | GPT system prompt with categorization rules |
| `offbrand-keywords.txt` | Competitor/off-brand terms (example data) |
| `scripts/analyze.py` | Main execution script |
| `scripts/qa_results.py` | Off-brand QA validation |
| `scripts/qa_gate.py` | Unified QA gate (combines off-brand + GEO QA) |

---

## API Cost Safety

**Safeguards:**
- **Monitor batch count:** Before running `--run-all`, check total pending rows. Each batch of 50 = 1 API call. Budget accordingly.
- **Use `--dry-run` first:** Always preview row count before large runs.
- **OpenAI balance check:** If running 100+ batches, verify API balance before starting.
- **Prefer smaller runs:** For testing new prompt changes, use default batch size (50) not `--run-all`.

---

## Production Method: SQR Pipeline (3-Run Consensus)

**The production SQR classification now uses the `sqr-pipeline` skill**, which runs 3 independent classification passes via Claude Code Task agents and uses consensus (3-3 unanimous / 2-3 majority) for higher confidence — then carries the approved negatives through human review and two-step upload.

**Use `sqr-pipeline` for production runs.** This script (`analyze.py`) remains available for:
- Debugging individual batches
- Testing prompt changes on small sets
- Legacy single-pass runs when the full pipeline is overkill

**See:** `.claude/skills/sqr-pipeline/SKILL.md`

---

## Related

- **SQR Pipeline**: `.claude/skills/sqr-pipeline/` (production method — pull → classify → review → upload)
- **GEO Conflict Analyzer**: `.claude/skills/geo-conflict-analyzer/` (similar pattern)
