# Markdown to Sheets Presenter

Transforms markdown reports (competitive analysis, performance reviews, ad recon) into professionally formatted Google Sheets with color-coded headers, conditional formatting, and multi-tab layouts ready for client presentation.

**The pain point:** You've done the analysis and written the report, but sharing a markdown file with a client doesn't fly. Manually formatting a Google Sheet with proper colors, tab structure, and conditional formatting takes almost as long as the analysis itself. This skill automates the entire transformation.

---

## What's Inside

- Automatic markdown parsing: detects section hierarchy, tables, lists, and scoring data
- Multi-tab layout generation with intelligent section-to-tab mapping
- Professional color palette (Google Blue theme) with alternating row colors
- Conditional formatting for scores, threat levels, and status indicators
- Support for competitive analysis, performance reports, and custom report types
- Executive presentation rules: no text truncation, 550px+ description columns, charts below data
- Handles large tables (100+ rows), currency values, percentages, and missing data
- Returns clickable Google Sheets link with tab summary

---

## Installation

```bash
mkdir -p .claude/skills/markdown-to-sheets-presenter/scripts .claude/skills/markdown-to-sheets-presenter/templates
curl -o .claude/skills/markdown-to-sheets-presenter/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/markdown-to-sheets-presenter/SKILL.md
curl -o .claude/skills/markdown-to-sheets-presenter/SETUP.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/markdown-to-sheets-presenter/SETUP.md
curl -o .claude/skills/markdown-to-sheets-presenter/scripts/create_spreadsheet.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/markdown-to-sheets-presenter/scripts/create_spreadsheet.py
curl -o .claude/skills/markdown-to-sheets-presenter/templates/professional-blue-theme.json \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/markdown-to-sheets-presenter/templates/professional-blue-theme.json
```

---

## Prerequisites

- `google-ads.yaml` at project root — see [google-ads-api-setup](../google-ads-api-setup/) if you don't have one; the script reuses that same file's OAuth token for the Sheets API (refresh token needs the `spreadsheets` scope, which the setup skill's generator grants by default — token predates that? re-run the generator once)
- Python with `google-api-python-client`, `google-auth`, and `pyyaml` packages
- Sheets are created in the Drive root of the authorized account — move them into client folders in Drive afterward if you organize that way

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
