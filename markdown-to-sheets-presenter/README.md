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
mkdir -p .claude/skills/markdown-to-sheets-presenter
curl -o .claude/skills/markdown-to-sheets-presenter/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/markdown-to-sheets-presenter/SKILL.md
```

---

## Prerequisites

- Google Sheets API credentials with write access
- OAuth token for the Google account that will own the sheet
- Google Drive folder ID for the target location (optional, for organized storage)

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
