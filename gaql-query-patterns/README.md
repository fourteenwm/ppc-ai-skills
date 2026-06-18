# GAQL Query Patterns

Ready-to-use Google Ads Query Language (GAQL) templates for the most common PPC analysis tasks.

**The pain point:** GAQL syntax is powerful but poorly documented. Most PPC practitioners waste hours guessing at field names, figuring out which resource to query, and debugging `INVALID_PREDICATE_ENUM_VALUE` errors. These templates are battle-tested across over 110 accounts.

---

## What's Included

| Pattern | Use Case |
|---------|----------|
| Campaign Spend Analysis | Recent spend, budget utilization, campaign health |
| Impression Share Metrics | Budget vs. quality constraints, auction competitiveness |
| Search Term Report | What queries triggered your ads, with performance data |
| Keyword Performance | Keyword-level metrics with quality score |
| Ad Performance | RSA asset performance, ad strength |
| Conversion Tracking | Conversion actions, values, attribution |
| Geographic Performance | Performance by location |
| Device Performance | Mobile vs. desktop vs. tablet breakdown |
| Change History | What changed in the account and when |
| Account-Level Metrics | High-level account summary |

---

## Installation

Copy `SKILL.md` into your Claude Code project:

```bash
mkdir -p .claude/skills/gaql-query-patterns
cp SKILL.md .claude/skills/gaql-query-patterns/SKILL.md
```

Once installed, Claude will automatically reference these patterns when you ask questions like:
- "Show me spend for the last 7 days"
- "What's our impression share?"
- "Pull search terms for this account"

---

## Using Without Claude Code

You don't need Claude Code to use these queries. Copy any query from `SKILL.md` and run it through:
- The Google Ads API directly (Python, Node.js, etc.)
- Google Ads Scripts (with minor syntax adjustments)
- Any tool that accepts GAQL

---

## Prerequisites

- Google Ads API access ([setup guide](../google-ads-api-setup/))
- Or Google Ads Scripts access (for script-compatible queries)

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
