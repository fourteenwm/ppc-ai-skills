# RSA Refresh

Refreshes Responsive Search Ad copy by scraping the business website, identifying LOW-performing assets, and generating AI-written replacement headlines and descriptions — verified against actual website content.

**The pain point:** RSA asset performance labels tell you which headlines and descriptions are LOW performers, but replacing them requires visiting the business website, extracting claims, writing new copy, and validating character limits. This skill automates the pipeline: pull current assets and labels, scrape the website, generate verified replacements for the weak slots (carrying strong performers forward per the refresh-vs-rebuild call in `rules.md`), and write everything to a Google Sheet for review before a Google Ads Editor import.

---

## What's Inside

- 3-stage workflow: Prepare Context (API + scrape), Generate Copy (AI), Write to Sheet
- Queries existing RSAs with asset performance labels (BEST/GOOD/LOW/LEARNING)
- Website scraping via Firecrawl for verified business features (requests + Playwright fallbacks)
- Headline structure enforcement (customizer slot + 14 AI-generated headlines)
- Description voice lifting technique for natural, on-brand copy
- Hallucination filter: defense-in-depth against unverified claims ("Empty > Inaccurate")
- Output to Google Sheets with "Original RSAs" and "Refreshed RSAs" tabs for side-by-side review
- Optional pre-refresh baseline snapshot (IWQS, QS components, impression share)
- Operator docs: `rules.md` (refresh-vs-rebuild call, baseline reading, false alarms), `examples.md` (worked reads including two edge cases), `references/refresh-contract.md` (exact selection/merge/sheet mechanics)

---

## Installation

```bash
mkdir -p .claude/skills/rsa-refresh/scripts .claude/skills/rsa-refresh/references
curl -o .claude/skills/rsa-refresh/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/rsa-refresh/SKILL.md
curl -o .claude/skills/rsa-refresh/rules.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/rsa-refresh/rules.md
curl -o .claude/skills/rsa-refresh/examples.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/rsa-refresh/examples.md
curl -o .claude/skills/rsa-refresh/scripts/rsa_refresh_generator.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/rsa-refresh/scripts/rsa_refresh_generator.py
curl -o .claude/skills/rsa-refresh/scripts/rsa_baseline_snapshot.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/rsa-refresh/scripts/rsa_baseline_snapshot.py
curl -o .claude/skills/rsa-refresh/references/refresh-contract.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/rsa-refresh/references/refresh-contract.md
curl -o .claude/skills/rsa-refresh/references/pm-headline-structure.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/rsa-refresh/references/pm-headline-structure.md
curl -o .claude/skills/rsa-refresh/references/description-voice-lifting.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/rsa-refresh/references/description-voice-lifting.md
curl -o .claude/skills/rsa-refresh/references/hallucination-filter.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/rsa-refresh/references/hallucination-filter.md
```

The `references/` files are required, not optional reading — Stage 1 embeds
the headline and description standards into the context JSON and errors if
they're missing.

---

## Prerequisites

- Firecrawl API key (`FIRECRAWL_API_KEY` environment variable) for website scraping
- Google Ads API credentials (`google-ads.yaml` at project root) — see [google-ads-api-setup](../google-ads-api-setup/) if you don't have one
- Sheets output uses `token-sheets.json` OR that same `google-ads.yaml` OAuth token — its refresh token needs the `spreadsheets` scope, which the setup skill's generator grants by default (token predates that? re-run the generator once)

---

## After a run

The sheet is a review queue, not a deployment. Before any Editor import,
read the Refreshed tab against `rules.md` — it owns the refresh-vs-rebuild
call, the baseline misreads (standalone zeros, all-N/A rows), and the
false-alarm table (error rows on a resume, doubled append rows, the
wrong-site scrape). `examples.md` shows three full reads.

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
