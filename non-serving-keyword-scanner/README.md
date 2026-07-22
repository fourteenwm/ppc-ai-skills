# Non-Serving Keyword Scanner

Scans all accounts in a portfolio for keywords with zero impressions in the last 180 days, outputting results to a Google Sheet for human review.

**The pain point:** Dead keywords silently clutter accounts — they've received zero impressions for 6+ months but nobody pauses them because nobody knows they exist. Across a portfolio of 80+ accounts, these accumulate into hundreds of wasted entries. This skill scans every account in one run and produces a clean review list.

![Sequence diagram: a PPC manager runs the scanner with one command; it builds the account list from a file, CID flags, or by walking the MCC, then queries each account for enabled Search keywords with zero impressions in 180 days — one account erroring never kills the run — and writes a single review tab to a Google Sheet; the manager reviews each row and decides what to pause, keep, or investigate, because the scanner never pauses anything itself](diagrams/workflow-hero.svg)

---

## What's Inside

- Three account-source modes: explicit CIDs (`--cid`/`--cids`), whole-MCC walk (`--all`), or a curated accounts file (starter template ships as `accounts.example.md`)
- Filters to Search campaigns only, with enabled campaigns/ad groups/keywords
- Excludes known exceptions (dynamic pricing ad groups like "special"/"specials")
- Outputs to any Google Sheet you own, with account name, CID, campaign, ad group, keyword, and match type
- Human-in-the-loop design: generates report only, never auto-pauses keywords
- Progress output showing per-account results as the scan runs
- A judgment layer for reading the results: `rules.md` (when zero impressions is expected vs. actionable — triage order, false signals, and the three verdicts), `examples.md` (worked triage reads), and `references/scan-contract.md` (the exact selection and output contract)

The run logic, gate by gate:

![Flowchart of the scan's run logic in three phases: setup (one command with flags picking the scope, load API and Sheets credentials from one file, build the account list from one CID, a list, the accounts file, or the whole MCC, and exit early if it's empty), scan each account (query enabled Search keywords with zero impressions across the window, drop known-exception ad groups, record per-account failures and keep scanning the other accounts), and report (exit with the sheet untouched when nothing is found, otherwise write one fresh timestamped review tab and print a summary — a human reviews, nothing auto-pauses)](diagrams/run-logic.svg)

The `.mmd` sources for both diagrams live in `diagrams/` — they're
[Mermaid](https://mermaid.js.org/) diagram-as-code, rendered with the included
`theme.json`.

---

## Installation

```bash
mkdir -p .claude/skills/non-serving-keyword-scanner/scripts .claude/skills/non-serving-keyword-scanner/references
curl -o .claude/skills/non-serving-keyword-scanner/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/non-serving-keyword-scanner/SKILL.md
curl -o .claude/skills/non-serving-keyword-scanner/scripts/non_serving_keyword_scan.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/non-serving-keyword-scanner/scripts/non_serving_keyword_scan.py
curl -o .claude/skills/non-serving-keyword-scanner/accounts.example.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/non-serving-keyword-scanner/accounts.example.md
curl -o .claude/skills/non-serving-keyword-scanner/rules.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/non-serving-keyword-scanner/rules.md
curl -o .claude/skills/non-serving-keyword-scanner/examples.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/non-serving-keyword-scanner/examples.md
curl -o .claude/skills/non-serving-keyword-scanner/references/scan-contract.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/non-serving-keyword-scanner/references/scan-contract.md
```

First run (single account, no other files needed beyond your credentials):

```bash
python .claude/skills/non-serving-keyword-scanner/scripts/non_serving_keyword_scan.py \
  --cid 1234567890 --sheet-id YOUR_SHEET_ID
```

To scan a curated list instead, copy `accounts.example.md` to `./accounts.md` and edit — one `### CID: 123-456-7890` header per account with one or more `- Name` lines under it (first name is the display name). `--all` walks every enabled account under your MCC. Run with no usable account source and the script prints the three modes instead of a traceback.

---

## Prerequisites

- Google Ads API credentials (`google-ads.yaml` at project root) — see [google-ads-api-setup](../google-ads-api-setup/) if you don't have one; MCC access required for `--all`
- The sheet-writing step reuses that same `google-ads.yaml` OAuth token — its refresh token needs the `spreadsheets` + `drive.readonly` scopes, which the setup skill's generator grants by default (token predates that? re-run the generator once)
- Python with `google-ads`, `gspread`, `google-auth`, and `pyyaml` packages

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
