# RSA Refresh

Refreshes Responsive Search Ad copy by scraping the business website, identifying LOW-performing assets, and generating AI-written replacement headlines and descriptions — verified against actual website content.

**The pain point:** RSA asset performance labels tell you which headlines and descriptions are LOW performers, but replacing them requires visiting the business website, extracting claims, writing new copy, and validating character limits. This skill automates the entire pipeline: pull current assets, scrape the website, generate replacements for LOW assets while preserving BEST and GOOD ones, and write everything to a Google Sheet for review.

---

## What's Inside

- 3-stage workflow: Prepare Context (API + scrape), Generate Copy (AI), Write to Sheet
- Queries existing RSAs with asset performance labels (BEST/GOOD/LOW/LEARNING)
- Website scraping via Firecrawl for verified business features
- Headline structure enforcement (customizer slot + 14 AI-generated headlines)
- Description voice lifting technique for natural, on-brand copy
- Hallucination filter: defense-in-depth against unverified claims ("Empty > Inaccurate")
- Output to Google Sheets with "Original RSAs" and "Refreshed RSAs" tabs for side-by-side review
- Optional pre-refresh baseline snapshot (IWQS, QS components, impression share)

---

## Installation

```bash
mkdir -p .claude/skills/rsa-refresh
curl -o .claude/skills/rsa-refresh/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/rsa-refresh/SKILL.md
```

---

## Prerequisites

- Firecrawl API key (`FIRECRAWL_API_KEY` environment variable) for website scraping
- Google Ads API credentials (YAML config)
- Google Sheets API credentials (for output)

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage 118 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
