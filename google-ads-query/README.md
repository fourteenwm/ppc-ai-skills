# Google Ads Query

Query Google Ads API data with natural language commands and save results to CSV — keeping raw data out of the conversation context for efficient analysis.

**The pain point:** Pulling Google Ads data through the API means writing GAQL queries, handling authentication, and parsing responses every time. This skill wraps it all into simple commands like "Get search terms for Acme Plumbing 60d" and saves results to CSV, so you can analyze millions of rows without blowing up your context window.

---

## What's Inside

- Natural language command parsing: "Get [resource] for [account] [days]d"
- 8 pre-built GAQL templates: search terms, campaigns, keywords, ad groups, conversions, budgets, assets, geo performance
- CSV-first pattern: data saves to file, only path and row count return to conversation
- Account name resolution with fuzzy matching and suggestions
- Profile lock enforcement — must select credentials before any query runs
- Standard file naming convention for organized data exports

---

## Installation

```bash
mkdir -p .claude/skills/google-ads-query
curl -o .claude/skills/google-ads-query/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/google-ads-query/SKILL.md
```

---

## Prerequisites

- Google Ads API credentials (YAML config)
- Python with `google-ads` package
- Account list file (JSON) mapping account names/aliases to CIDs

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage 118 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
