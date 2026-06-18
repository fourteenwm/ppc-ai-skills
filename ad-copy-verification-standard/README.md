# Ad Copy Verification Standard

A strict protocol that forces AI to source every ad claim from the actual business website — and stay silent when it can't.

**The pain point:** AI will happily write "Family-Owned Since 1952" for a shop that opened in 2019. It'll add "Free Estimates" that don't exist, cite "5-Star Reviews" that aren't there, and invent ASE certifications the business never had. By the time you notice, the ads are live and the client is angry. This skill makes that impossible.

---

## The Core Principle

> **Empty > Inaccurate**

Better to leave a headline field blank than fill it with an unverified claim. Better to ship 8 headlines you can prove than 15 headlines where half are hallucinations. Better to tell the user "the website doesn't say that" than to guess.

This is the thesis: **engineered AI with guardrails beats raw prompting every time.**

---

## What It Enforces

**Five mandatory rules:**

1. **Website verification is mandatory** — scrape the site first, extract claims, cite sources
2. **Source citation required** — every headline, description, callout, and sitelink must have a "Source: [page] — [exact wording]" attached
3. **Graceful degradation when scraping fails** — state the limitation, don't substitute assumptions
4. **Templates are for formatting only** — never use a template library as a content source
5. **"Free" exclusion** — opinionated rule for premium-positioning brands that attracts the wrong customer avatar

**Code-level enforcement:**

- No fallback values when data is missing — use empty strings
- RSA generation scripts must reference this standard in their header
- `if not social_proof: headlines.append("")` — never `headlines.append("5-Star Reviews")`

---

## What's Inside

- **5 universal verification rules** — applied to all ad copy generation
- **Ad-type-specific requirements** — RSAs, callouts, structured snippets, sitelinks
- **Verification workflow** — 5-step process from discovery to source documentation
- **QA checklist** — 8 pre-submission checks
- **Error handling templates** — what to say when the website is unavailable or partial
- **Real examples** — correct vs incorrect workflows, with verified/excluded claim breakdowns
- **Code implementation rules** — no-fallbacks pattern, header reference requirement

---

## Installation

```bash
mkdir -p .claude/skills/ad-copy-verification-standard
curl -o .claude/skills/ad-copy-verification-standard/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/ad-copy-verification-standard/SKILL.md
```

---

## When It Activates

Auto-invokes when Claude is asked to:
- Create or refresh RSAs
- Generate callouts, structured snippets, or sitelinks
- Audit existing ad copy
- Suggest extension improvements
- Build ad copy for a new campaign

---

## Prerequisites

- A website scraping tool (Firecrawl, Jina Reader, or any scraper returning clean markdown)
- No API keys specific to this skill — bring your own scraper

---

## Pairs With

- **[mutation-safety](../mutation-safety/)** — Prevents unverified copy from being written to live accounts even if it slips through
- **[investigation-methodology](../investigation-methodology/)** — Diagnose why existing ad copy is underperforming before rewriting it

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills. This standard exists because I got tired of manually deleting AI-hallucinated claims from live ads.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
