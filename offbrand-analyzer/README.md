# Off-Brand Analyzer

Classifies search queries as High Intent, Low Intent, Informational, or Off-Brand using GPT-4o, reading from a Google Sheet and writing categorized results back — with optional QA gate validation and GEO conflict chaining.

**The pain point:** Search query reports with thousands of rows can't be reviewed manually at scale. Deciding which queries are off-brand (competitor names, wrong properties) versus legitimately high-intent requires understanding brand names, competitor lists, and misspelling variations. This skill automates that classification with LLM judgment, not brittle regex rules.

---

## What's Inside

- Batch classification of search queries using GPT-4o with configurable batch sizes
- 4 categories: High Intent (brand + location queries), Low Intent (too generic), Informational (research queries), Off-Brand (competitor names and variations)
- Reads from Google Sheet "Have Cost" tab, writes to "Have Cost Result" tab
- Dry-run mode for previewing without writes
- `--run-all` flag for processing all pending queries
- `--chain-geo` flag for full pipeline (Off-Brand + GEO Conflict analysis)
- `--with-qa` flag for QA gate validation with automatic retry on failure
- API cost safeguards: monitor batch count, preview before large runs

---

## Installation

```bash
mkdir -p .claude/skills/offbrand-analyzer
curl -o .claude/skills/offbrand-analyzer/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/offbrand-analyzer/SKILL.md
```

---

## Prerequisites

- OpenAI API key (for GPT-4o classification)
- Google Sheets API credentials with read/write access
- Python with `openai`, `google-auth`, `google-api-python-client`, and `python-dotenv` packages

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage 118 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
