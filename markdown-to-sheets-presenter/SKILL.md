---
name: markdown-to-sheets-presenter
description: Transforms markdown reports into professionally formatted Google Sheets for client presentation. Auto-invoke when user wants to make a report presentable, share analysis with clients, convert markdown to Sheets, or export competitive analysis. Triggers include "make this presentable", "create a Google Sheet", "export to sheets", "format for client".
allowed-tools: [Read, Write, Bash, Glob, Grep, WebFetch]
version: "1.0.0"
---

# Markdown to Google Sheets Presenter

Turn a markdown report (competitive analysis, ad recon, performance
review) into a client-ready Google Sheet: multi-tab layout, themed
formatting, conditional colors. The shipped script bootstraps the
spreadsheet; everything the client actually sees is composed by the agent
per [`references/presentation-contract.md`](references/presentation-contract.md)'s
division of labor. Judgment calls — when to present vs hand over a CSV,
theme handling, tab structure — live in [rules.md](rules.md).

## What this skill deliberately does NOT do

- **Never edits report content.** This is a formatting pass: numbers, ad
  copy, and quotes land verbatim, ad copy never truncates (rules,
  invariant 1). Wrong findings get fixed in the source report, not here.
- **Ships no converter.** `create_spreadsheet.py` creates one
  header-formatted tab and exits — parsing, population, and conditional
  formatting are agent-composed API calls, not hidden code (contract).
- **No Drive operations.** Sheets-only scope: the file lands in the Drive
  root of the authorized account and gets moved/shared manually.
- **Not a data pipeline.** Recurring exports and re-import workflows
  belong to raw CSVs ([rules.md](rules.md) § presenter vs raw CSV), not a
  presentation layer.

## Prerequisites

1. **Credentials:** `google-ads.yaml` at project root — see the [google-ads-api-setup skill](../google-ads-api-setup/) if you don't have one. The script reuses this same file's OAuth credentials for the Sheets API — its refresh token must carry the `spreadsheets` scope, which the setup skill's generator grants by default (token predates that? re-run the generator once)
2. **Python packages:** `pip install google-api-python-client google-auth pyyaml`

## Workflow

### Step 1: Identify Input

When triggered, identify the source:
- If path provided: Use that path directly
- If recent analysis in conversation: Use that content
- If ambiguous: Ask user to specify

### Step 2: Parse Markdown Structure

Analyze the markdown to determine:
- Document title and metadata
- Section hierarchy (H1, H2, H3)
- Tables with headers and data
- Lists (bulleted, numbered, checkbox)
- Scoring data (X/45, percentages, etc.)

### Step 3: Determine Tab Structure

**For Competitive Analysis / Ad Recon Reports:**

| Section | Tab Name | Notes |
|---------|----------|-------|
| Executive Summary | `Summary` | First tab, KPIs |
| Strategic Analysis | `Strategic_Scores` | 15-attribute scoring |
| Tactical Scan | `Tactical_Scores` | 7-attribute flags |
| Gap Identification | `Gaps` | Opportunities list |
| Verified Angles | `Recommendations` | Client-ready angles |
| Per Competitor | `Competitor_[Name]` | If multiple competitors |

**For Performance Reports:**

| Section | Tab Name | Notes |
|---------|----------|-------|
| Overview | `Dashboard` | KPI metrics |
| Campaign Data | `Campaigns` | Main data table |
| Recommendations | `Action_Items` | Next steps |

These are the standard maps. When to deviate — merging small sections,
single-table reports, prose-only sources — is
[rules.md](rules.md) § table-structure judgment.

### Step 4: Load the Theme

Every presentation value — colors (with API-ready RGB decimals),
typography tiers, conditional-formatting thresholds, row heights and
column widths — lives in
[`templates/professional-blue-theme.json`](templates/professional-blue-theme.json).
Read it before composing any formatting call; don't improvise values
inline. Client-brand variants are copies of that file
([rules.md](rules.md) § theme judgment). What the file owns, block by
block: [references/presentation-contract.md](references/presentation-contract.md).

### Step 5: Create Google Sheet

Use the create_spreadsheet.py script from your project root (where `google-ads.yaml` lives):

```bash
python .claude/skills/markdown-to-sheets-presenter/scripts/create_spreadsheet.py "Report Name"
```

Pass `--config path/to/google-ads.yaml` if your credentials live elsewhere. The sheet is created in the Drive root of the authorized account — move it into a client folder in Drive afterward if needed. The script returns the spreadsheet ID and URL as JSON; use the ID for the data-population and formatting calls that follow.

**Naming Convention:**
```
[Client Name] - [Report Type] - [YYYY-MM-DD]
Example: "Example Client - Competitive Analysis - 2025-12-16"
```

### Step 6: Populate and Format

The agent-composed pass (no shipped code — contract § division of
labor): rename `Data`/add tabs per the Step 3 plan, write values, then
format from the theme — header/subheader styling, alternating rows,
conditional formatting on scores and status columns, column widths,
number formats. Formatting decisions (truncation ban, currency and
percentage handling, missing data as "—", large tables, chart placement)
are [rules.md](rules.md)'s tables — apply them as you build.

### Step 7: Return Results

Provide user with:
1. **Clickable Google Sheets link**
2. **Summary of tabs created**
3. **Data rows per tab**

## Output Format

```markdown
## Google Sheet Created

**Sheet Name:** [Name]
**Link:** [URL]

### Tabs Created:
| Tab | Rows | Description |
|-----|------|-------------|
| Summary | 15 | Executive overview with KPIs |
| Strategic_Scores | 20 | 15-attribute competitive scoring |
| ... | ... | ... |

---
*Click the link above to open your Google Sheet.*
```

## Error Handling

| Error | Action |
|-------|--------|
| No credentials | Point at the [google-ads-api-setup skill](../google-ads-api-setup/) |
| 403 / PERMISSION_DENIED | Refresh token predates the Sheets scope — re-run the api-setup generator once, paste the new `refresh_token` into `google-ads.yaml` |
| File not found | Ask user to verify path |
| API quota | Suggest waiting or manual copy |
| Parse failure | Fall back to raw text layout |

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | This file — workflow + routing |
| `rules.md` | Judgment layer: presenter vs raw CSV, theme judgment, table structure, false alarms, escalation |
| `examples.md` | Three worked decisions incl. the asks this skill should decline |
| `references/presentation-contract.md` | The script/agent division of labor, exact script behavior, the theme file's contract |
| `SETUP.md` | Credential setup + quick test + troubleshooting |
| `scripts/create_spreadsheet.py` | The bootstrap: one spreadsheet, one formatted header row, JSON on stdout |
| `templates/professional-blue-theme.json` | The theme — single home of every presentation value, consumed by the agent (no script reads it) |
| `README.md` | User-facing overview + install |

## After a Run

The Google Sheet is the artifact; nothing lands on local disk. The
spreadsheet ID and URL print as JSON on stdout (contract) — capture them
if you'll need the sheet programmatically later, because creation is
**never idempotent**: re-running makes a second spreadsheet with the same
name, and Drive allows that.

## When to Load What

| Moment | Load |
|---|---|
| Deciding sheet-vs-CSV, structuring tabs, theming | [rules.md](rules.md) |
| Exact script behavior, stdout/stderr contract, theme file blocks | [references/presentation-contract.md](references/presentation-contract.md) |
| First run, or the ask smells like a decline case | [examples.md](examples.md) |
| The input is a competitive analysis | [competitor-analysis-v2](../competitor-analysis-v2/) produces it — its 15 strategic + 7 tactical scoring is what the Strategic/Tactical tab map was built for |
| The ask is machine-readable data, not presentation | [google-ads-query](../google-ads-query/) — its CSVs are the re-import surface |
| The source skill already writes a Sheet natively | Use it directly — e.g. [account-diagnostic](../account-diagnostic/) with `--sheet-id`; don't re-present a sheet |
| No credentials yet / 403 at the Sheets step | [google-ads-api-setup](../google-ads-api-setup/) (SETUP.md has the short version) |
