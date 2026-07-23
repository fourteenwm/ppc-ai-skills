# Google Ads Query

Query Google Ads API data with natural language commands and save results to CSV — keeping raw data out of the conversation context for efficient analysis.

**The pain point:** Pulling Google Ads data through the API means writing GAQL queries, handling authentication, and parsing responses every time. This skill wraps it all into simple commands like "Get search terms for Acme Plumbing 60d" and saves results to CSV, so you can analyze millions of rows without blowing up your context window.

---

## What's Inside

- Natural language command parsing: "Get [resource] for [account] [days]d"
- 8 pre-built GAQL templates: search terms, campaigns, keywords, ad groups, conversions, budgets, assets, geo performance — plus drop-in support for your own `.gaql` files
- CSV-first pattern: data saves to file, only path and row count return to conversation
- Works with bare CIDs out of the box; optional `accounts.json` registry adds name/alias resolution with fuzzy matching and suggestions (starter template ships as `accounts.example.json`)
- Read-only by design: SELECT queries only, never mutations
- Standard file naming convention for organized data exports
- Operator docs: `rules.md` (template-vs-custom and registry-vs-CID calls, CSV-reading judgment, false-alarm table), `examples.md` (three worked reads), and `references/query-contract.md` (exact resolution/date/CSV mechanics + each template's scope filters)

---

## Installation

```bash
mkdir -p .claude/skills/google-ads-query/scripts .claude/skills/google-ads-query/references
for f in SKILL.md rules.md examples.md accounts.example.json; do
  curl -o .claude/skills/google-ads-query/$f \
    https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/google-ads-query/$f
done
curl -o .claude/skills/google-ads-query/scripts/query.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/google-ads-query/scripts/query.py
for r in resources.md query-contract.md; do
  curl -o .claude/skills/google-ads-query/references/$r \
    https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/google-ads-query/references/$r
done
for t in search-terms campaigns keywords ad-groups conversions budgets assets geo; do
  curl -o .claude/skills/google-ads-query/references/$t.gaql \
    https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/google-ads-query/references/$t.gaql
done
```

First run (no other files needed beyond your credentials):

```bash
python .claude/skills/google-ads-query/scripts/query.py \
  --cid 1234567890 --resource campaigns --days 30
```

The CSV lands in `./data/`. To query by account name instead of CID, copy `accounts.example.json` to `./accounts.json` and edit — then `--account "riverside flats"` resolves names, aliases, and partial matches.

Before reading any surprising result (zero rows, mismatched totals), check the false-alarm table in `rules.md` — most surprises are per-template scope filters doing their documented job.

---

## Prerequisites

- Google Ads API credentials (`google-ads.yaml` at project root, or `--config <path>`) — see [google-ads-api-setup](../google-ads-api-setup/) if you don't have one; querying client accounts through a manager account requires `login_customer_id` in the yaml
- Python with the `google-ads` package (`pip install google-ads`)

Pairs with [gaql-query-patterns](../gaql-query-patterns/) when you outgrow the shipped templates — write a custom query there, save it as a ninth `.gaql` file here.

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
