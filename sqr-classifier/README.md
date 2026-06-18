# SQR Classifier

Paste your search terms, get them classified by intent. No API keys required — Claude does the classification using structured PPC judgment.

**The pain point:** Reviewing search terms is the most time-consuming task in PPC. A 30-account portfolio can generate 3,000+ unique search terms per month. Most managers either skip the review entirely or spend hours eyeballing terms in a spreadsheet. This skill classifies terms into actionable categories in minutes.

---

## What It Does

You provide search terms (paste from Google Ads, CSV, or any format). The skill classifies each term into one of four categories:

| Category | Meaning | Action |
|----------|---------|--------|
| **High Intent** | Searcher is likely looking for your service/product | Keep — these are your money terms |
| **Low Intent** | Related to your industry but unlikely to convert | Monitor — may need negatives if spend is high |
| **Informational** | Research/educational queries, not purchase intent | Usually negative — unless you're targeting top-of-funnel |
| **Off-Brand** | Completely unrelated to your business | Negative immediately |

---

## Usage

### With Claude Code (Recommended)

Install the skill:
```bash
mkdir -p .claude/skills/sqr-classifier
cp SKILL.md .claude/skills/sqr-classifier/SKILL.md
```

Then just ask:
```
"Classify these search terms for a [business type] account:
[paste your terms here]"
```

Or provide a CSV:
```
"Classify the search terms in this file: search_terms.csv
The business is a [business type] in [location]."
```

### Without Claude Code

The classification framework in `SKILL.md` can be used as a prompt with any LLM. Copy the classification rules and provide them as context along with your search terms.

---

## Example

**Input:**
```
Business: Residential property management in Austin, TX

Search terms:
apartments for rent austin
how to break a lease in texas
luxury apartments downtown austin
property management software
2 bedroom apartment near UT
average rent in austin
best apartments austin reddit
commercial property management austin
```

**Output:**

| Search Term | Category | Reasoning |
|-------------|----------|-----------|
| apartments for rent austin | High Intent | Direct apartment search with location |
| how to break a lease in texas | Low Intent | Current tenant, not prospect |
| luxury apartments downtown austin | High Intent | Specific apartment search with qualifiers |
| property management software | Off-Brand | Looking for software, not an apartment |
| 2 bedroom apartment near UT | High Intent | Specific unit search with location |
| average rent in austin | Informational | Research phase, not ready to rent |
| best apartments austin reddit | Low Intent | Research phase, review-seeking |
| commercial property management austin | Off-Brand | Commercial, not residential |

---

## Prerequisites

- Claude Code installed (or any LLM that can follow structured prompts)
- Your search terms in any format (paste, CSV, spreadsheet export)
- Knowledge of what your business does (so the classifier knows what's "on-brand")

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
