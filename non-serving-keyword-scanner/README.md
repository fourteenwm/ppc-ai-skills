# Non-Serving Keyword Scanner

Scans all accounts in a portfolio for keywords with zero impressions in the last 180 days, outputting results to a Google Sheet for human review.

**The pain point:** Dead keywords silently clutter accounts — they've received zero impressions for 6+ months but nobody pauses them because nobody knows they exist. Across a portfolio of 80+ accounts, these accumulate into hundreds of wasted entries. This skill scans every account in one run and produces a clean review list.

---

## What's Inside

- Portfolio-wide scan across all accounts under your MCC
- Filters to Search campaigns only, with enabled campaigns/ad groups/keywords
- Excludes known exceptions (dynamic pricing ad groups like "special"/"specials")
- Outputs to Google Sheet with account name, CID, campaign, ad group, keyword, and match type
- Human-in-the-loop design: generates report only, never auto-pauses keywords
- Progress output showing per-account results as the scan runs

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
