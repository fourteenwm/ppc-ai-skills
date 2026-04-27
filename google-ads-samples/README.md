# Google Ads Samples

A reference library of 39 official Google Ads API code samples that auto-loads when building new scripts, agents, or API integrations — so you start from proven patterns instead of guessing.

**The pain point:** The Google Ads API has hundreds of services, operations, and field paths. Writing a new script from scratch means trial-and-error with operation structures, service clients, and error handling. This skill points Claude to the right official example first, cutting implementation time by 50-75% for complex operations.

---

## What's Inside

- 39 indexed official Google Ads Python examples across 4 categories
- Account Management (10 scripts): hierarchy traversal, account creation, user access, change history
- Campaign Management (8 scripts): batch creation, ad validation, labels, experiments, bid adjustments
- Advanced Operations (19 scripts): Performance Max, RSAs, Demand Gen, shared keyword sets, portfolio bidding
- Reporting (2 scripts): parallel multi-account report downloads
- Quick-reference index organized by use case (creating campaigns, mutations, ads, account management, bidding, reporting)
- Step-by-step protocol: search examples, read the pattern, explain to user, adapt, reference source

---

## Installation

```bash
mkdir -p .claude/skills/google-ads-samples
curl -o .claude/skills/google-ads-samples/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/google-ads-samples/SKILL.md
```

---

## Prerequisites

None. This is a reference skill — it teaches Claude how to find and use existing code samples. The actual Google Ads API credentials are only needed when running the adapted scripts.

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage 118 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
