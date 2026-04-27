---
name: sqr-3run
description: Production search query classification using 3 independent runs for consensus-based confidence. Uses Sonnet 4.6 Task agents (no external API costs). Auto-invoke when user says "run SQR pipeline", "run SQR 3 run", "SQR consensus", "classify search queries", or "search query consensus pipeline".
allowed-tools: [Bash, Read, Task]
---

# SQR 3-Run Consistency Pipeline

Production search query classification using 3 independent runs for consensus-based confidence. Uses Sonnet 4.6 Task agents (no external API costs).

---

## Triggers

- `run SQR pipeline`
- `run SQR 3 run`
- `classify search queries`
- `SQR 3 run`

---

## Overview

Three independent classification runs using the off-brand prompt. Only queries where 2+ runs agree on off-brand are surfaced for human review. No GEO conflict stage (add separately if needed for your vertical).

**Pipeline:**
```
sqr_prep.py -> [this skill: 3-run classification] -> sqr_compare.py
```

**Key principle:** No separate API calls. All classification runs through Claude Code Task agents (Sonnet 4.6) using the Claude AI subscription.

---

## Prerequisites

Before running this skill, the prep step must be complete:

```bash
python scripts/sqr_prep.py --sheet-id YOUR_SHEET_ID
```

This creates:
- `data/sqr-pipeline/ob_batches/ob_001.json` ... `ob_NNN.json`
- `data/sqr-pipeline/manifest.json`
- `data/sqr-pipeline/run{1,2,3}/step1/` directories
- `data/sqr-pipeline/account_lookup.json`, `brand_lookup.json`

Requires `token.json` at project root with the Google Sheets scope, and the
`offbrand-keywords.txt` file from the sibling `offbrand-analyzer` skill.

---

## Orchestration Workflow

When this skill is triggered, follow these steps exactly:

### Phase 1: Verify Prep

1. Read `data/sqr-pipeline/manifest.json`
2. Verify status is "prepared"
3. Count batch files in `data/sqr-pipeline/ob_batches/`
4. Report: "Found N batches with M total queries. Starting 3-run classification."

### Phase 2: Off-Brand Classification (3 runs in parallel)

Spawn **3 Task agents** (one per run), all running in parallel. Each agent processes all batches sequentially for its run.

**Agent spawn pattern:**
```
For run in [1, 2, 3]:
  Task agent (subagent_type: "general-purpose", model: "sonnet", run_in_background: true):
    - Run number: {run}
    - Processes all ob_batches sequentially
    - Saves results to data/sqr-pipeline/run{run}/step1/
```

**Agent prompt template:**

> You are processing SQR off-brand classification Run {RUN_NUMBER} of 3.
>
> **Your task:** For each batch file in `data/sqr-pipeline/ob_batches/`, classify the search queries using the off-brand classification prompt.
>
> **Classification prompt:** Read the full prompt from `.claude/skills/offbrand-analyzer/prompt.md`
>
> **For each batch file** (ob_001.json through ob_{TOTAL_BATCHES:03d}.json):
>
> 1. Read the batch file from `data/sqr-pipeline/ob_batches/ob_{NNN}.json`
> 2. The file contains: queries, brand_names, off_brand_keywords
> 3. Classify each query according to the prompt rules. Return ONLY the CSV arrays.
> 4. Parse the CSV output into a JSON array of objects: `[{"CID": "...", "Query": "...", "Category": "..."}]`
> 5. Write the result to `data/sqr-pipeline/run{RUN_NUMBER}/step1/ob_{NNN}.json`
>
> **CRITICAL -- YOU must be the classifier:**
> - Do NOT write a Python script, regex rules, or any deterministic code to classify queries.
> - YOU must read each batch and classify each query yourself using your own LLM judgment.
> - The entire point of running 3 independent classification runs is to get 3 independent LLM opinions. If you codify the rules into code, all 3 runs produce the same deterministic output, and the consensus mechanism is meaningless.
> - Process each batch by: reading it, reasoning about each query against the prompt rules, then writing your classifications as JSON output.
>
> **Important:**
> - Process ALL batches from 001 to {TOTAL_BATCHES:03d}
> - Each batch has ~50 queries
> - Categories must be lowercase: `high intent`, `low intent`, `informational`, `off-brand`
> - Save results as JSON arrays of {"CID", "Query", "Category"} objects
> - If you encounter an error on a batch, log it and continue to the next batch
> - Report progress every 25 batches
>
> **Max batches flag:** If `--max-batches N` was specified, only process batches 1 through N.

Wait for all 3 agents to complete. Check results:
- Each run directory should have the same number of result files as batch files
- Report any missing batches

### Phase 3: Report Results

After all runs complete, report:
- Total batches processed per run
- Any missing or failed batches

Then instruct:
```
Next step: python scripts/sqr_compare.py
```

---

## Testing with Limited Batches

For testing, you can limit the number of batches:

When the user says "run SQR 3 run --max-batches 2":
- Only process batches 1-2 in each agent
- All other logic stays the same
- Good for verifying the pipeline end-to-end before a full run

---

## File Locations

| File | Purpose |
|------|---------|
| `scripts/sqr_prep.py` | Step A: Read sheet, create batches |
| `SKILL.md` (this file) | Orchestration instructions for the 3 Task agents |
| `scripts/sqr_compare.py` | Step C: Merge results, write to sheet |
| `../offbrand-analyzer/prompt.md` | Classification prompt (uses the offbrand-analyzer skill's prompt) |
| `../offbrand-analyzer/offbrand-keywords.txt` | Competitor terms |
| `data/sqr-pipeline/` | Runtime data (batches, results, manifest) — created by `sqr_prep.py` |

**Credentials:** Uses `./token.json` at project root for Google Sheets access (Sheets scope required). Override via `SHEETS_TOKEN_PATH` env var.

---

## Full Pipeline (User Experience)

```bash
# Step 1: Prep batches from sheet
python scripts/sqr_prep.py --sheet-id YOUR_SHEET_ID

# Step 2: Run classification (this skill)
# Say: "run SQR 3 run"

# Step 3: Compare and write to sheet
python scripts/sqr_compare.py --sheet-id YOUR_SHEET_ID

# Step 4: Human review in Google Sheets
# Mark 'x' in Column M on "3-3 Agree" and "2-3 Agree" tabs

# Step 5: Upload negatives via the sqr-upload skill
python ../sqr-upload/scripts/sqr_upload_negatives.py --sheet-id YOUR_SHEET_ID
```

---

## Output Tabs (in SQR Sheet)

| Tab | Content | Column M |
|-----|---------|----------|
| 3-3 Agree | Unanimous off-brand (all 3 runs agree) | Include? |
| 2-3 Agree | Majority off-brand (2 of 3 runs agree) | Include? |

Column schema (A-M):
```
A: CID
B: Account
C: Query
D: Brand Names
E: R1 Category
F: R2 Category
G: R3 Category
H-L: (empty - reserved)
M: Include? (human marks 'x')
```

---

## Related

- **Off-Brand Analyzer**: `.claude/skills/offbrand-analyzer/` (legacy single-pass)
- **SQR Upload**: see [sqr-upload skill](../sqr-upload/) for negative upload to Google Ads
