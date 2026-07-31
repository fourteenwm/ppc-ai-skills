# Geo Conflict Analyzer

Analyzes search queries for geographic targeting conflicts in Google Ads GEO campaigns. Uses OpenAI GPT-4o to decide if a query is **safe to negative** (PASS — doesn't conflict with active geo targets) or **should NOT be negatived** (FAIL — matches an active geo target and negativing would block real traffic).

**The pain point:** Adding negatives from search query reports is how you clean an account, but if you negative "apartments in chula vista" while you're actively bidding on "Chula Vista" as a geo ad group, you just broke your own campaign. Manually checking every query against every geo target across dozens of accounts is tedious and error-prone. This skill catches the conflicts before you add the negative.

---

## What It Prevents

- Negativing a query that matches one of your active geo targets (direct match, abbreviation, preposition variation, typo)
- Negativing a query that's a *more-specific* version of an active geo (e.g., "downtown chula vista apartments" when you actively target "Chula Vista")
- Manually reviewing 500+ queries per account per month

## What It Does

1. Reads queries from a Google Sheet tab (status = "Waiting")
2. Groups by CID, reading each account's active geo targets from the same
   sheet (column H — nothing is fetched from Google Ads)
3. Sends one batch per run (default 50 queries) to GPT-4o with a
   95-example PASS/FAIL ruleset
4. Appends PASS/FAIL + confidence results to an output tab

Pairs with [`sqr-pipeline`](../sqr-pipeline/) — its off-brand classification runs first, then geo-conflict runs on queries that need geographic validation.

Operator docs ship alongside: `rules.md` (how to read verdicts, real
conflicts vs noise), `examples.md` (three worked reads), and
`references/analysis-contract.md` (exact script mechanics, line-cited).

---

## Installation

```bash
mkdir -p .claude/skills/geo-conflict-analyzer/scripts .claude/skills/geo-conflict-analyzer/references
for f in SKILL.md README.md prompt.md rules.md examples.md; do
  curl -o .claude/skills/geo-conflict-analyzer/$f \
    https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/geo-conflict-analyzer/$f
done
curl -o .claude/skills/geo-conflict-analyzer/references/analysis-contract.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/geo-conflict-analyzer/references/analysis-contract.md
curl -o .claude/skills/geo-conflict-analyzer/scripts/analyze.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/geo-conflict-analyzer/scripts/analyze.py
```

`prompt.md` is a **runtime dependency**, not documentation — the script
loads it on every run as the model's system prompt.

---

## Prerequisites

- Python 3.10+
- `pip install openai google-auth google-api-python-client python-dotenv`
- `OPENAI_API_KEY` set in a `.env` file or environment variable
- Google Sheets OAuth token at `./token.json` (see [google-ads-api-setup](../google-ads-api-setup/) skill — the Sheets scope can be added to the same token)

---

## Usage

```bash
# Basic run (50 queries)
python scripts/analyze.py --sheet-id YOUR_SHEET_ID

# Larger batch
python scripts/analyze.py --sheet-id YOUR_SHEET_ID --batch-size 100

# Dry run (no writes)
python scripts/analyze.py --sheet-id YOUR_SHEET_ID --dry-run
```

---

## Input Sheet Format

| Col | Field | Purpose |
|-----|-------|---------|
| A | CID | Customer ID |
| B | Account | Account name |
| C | Query | Search term to analyze |
| H | GEO Names | Comma-separated list of this CID's active geo targets |
| I | Status | Must equal `Waiting` to be processed |

See [SKILL.md](SKILL.md) for full documentation and [prompt.md](prompt.md) for the 95-example PASS/FAIL ruleset.

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
