# Competitor Analysis v2

An 8-phase competitive analysis workflow that combines website intelligence, ad copy evaluation, and visual documentation to produce either a strategic Client Gift (PDF) or tactical Ads Angle Brief (markdown).

**The pain point:** Competitor analysis is usually either superficial (just looking at their ads) or so time-consuming nobody does it properly. This skill runs a structured 8-phase pipeline — screenshots, website extraction, ad scoring, gap identification, client verification — and produces two distinct outputs: a strategic report for the client and a tactical brief for the practitioner.

---

## What's Inside

- 8-phase workflow: Gather Inputs, Capture Screenshots, Extract Website Content, Analyze Ads, Gap Identification, Client Verification, Generate Outputs, PDF Generation
- Parallel website extraction using Task agents (6 sites in ~1 minute)
- 22-attribute ad copy scoring framework (15 strategic + 7 tactical)
- Messaging matrix and 2x2 positioning map generation
- Gap analysis: table stakes vs. differentiators vs. whitespace
- Mandatory client verification phase — no recommendations without website evidence
- Two output formats: Client Gift (10-15 page PDF) and Ads Angle Brief (1 page tactical)
- Playwright-based screenshot capture script

---

## Installation

```bash
mkdir -p .claude/skills/competitor-analysis-v2
curl -o .claude/skills/competitor-analysis-v2/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/competitor-analysis-v2/SKILL.md
```

---

## Prerequisites

- Playwright (`npm install playwright`) for automated screenshots and PDF generation
- Google Ads API credentials (if analyzing competitor ads)
- Web scraping capability (Firecrawl or WebFetch) for website content extraction

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage 118 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
