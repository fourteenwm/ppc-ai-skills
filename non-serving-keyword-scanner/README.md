# Non-Serving Keyword Scanner

Scans all accounts in a portfolio for keywords with zero impressions in the last 180 days, outputting results to a Google Sheet for human review.

**The pain point:** Dead keywords silently clutter accounts — they've received zero impressions for 6+ months but nobody pauses them because nobody knows they exist. Across a portfolio of 80+ accounts, these accumulate into hundreds of wasted entries. This skill scans every account in one run and produces a clean review list.

![Sequence diagram: a PPC manager runs the scanner with one command; it builds the account list from a file, CID flags, or by walking the MCC, then queries each account for enabled Search keywords with zero impressions in 180 days — one account erroring never kills the run — and writes a single review tab to a Google Sheet; the manager reviews each row and decides what to pause, keep, or investigate, because the scanner never pauses anything itself](diagrams/workflow-hero.svg)

---

## What's Inside

- Portfolio-wide scan across all accounts under your MCC
- Filters to Search campaigns only, with enabled campaigns/ad groups/keywords
- Excludes known exceptions (dynamic pricing ad groups like "special"/"specials")
- Outputs to Google Sheet with account name, CID, campaign, ad group, keyword, and match type
- Human-in-the-loop design: generates report only, never auto-pauses keywords
- Progress output showing per-account results as the scan runs

The run logic, gate by gate:

![Flowchart of the scan's run logic in three phases: setup (one command with flags picking the scope, load API and Sheets credentials from one file, build the account list from one CID, a list, the accounts file, or the whole MCC, and exit early if it's empty), scan each account (query enabled Search keywords with zero impressions across the window, drop known-exception ad groups, record per-account failures and keep scanning the other accounts), and report (exit with the sheet untouched when nothing is found, otherwise write one fresh timestamped review tab and print a summary — a human reviews, nothing auto-pauses)](diagrams/run-logic.svg)

The `.mmd` sources for both diagrams live in `diagrams/` — they're
[Mermaid](https://mermaid.js.org/) diagram-as-code, rendered with the included
`theme.json`.

---

## Installation

```bash
mkdir -p .claude/skills/non-serving-keyword-scanner
curl -o .claude/skills/non-serving-keyword-scanner/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/non-serving-keyword-scanner/SKILL.md
```

---

## Prerequisites

- Google Ads API credentials (YAML config) with MCC access
- Google Sheets API credentials (`gspread` authentication)
- Python with `google-ads` and `gspread` packages

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
