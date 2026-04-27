# Change History Checker

Query Google Ads account change history for any date range — not limited to the 30-day window of `change_event`.

**The pain point:** Google Ads' `change_event` resource only goes back 30 days, so you can't answer "what did I change in October?" in December. This skill uses `change_status` instead, which has no date limit, and provides ready-to-use query patterns for tracking campaign, keyword, extension, budget, and ad changes.

---

## What's Inside

- Full script template for querying `change_status` across any date range
- Filters by resource type (campaigns, keywords, extensions, budgets, ads, bid strategies)
- Groups results by date and resource type for readable summaries
- Reference table of all resource types and status values
- Common query recipes: "What extensions did I update?", "What keywords did I add/remove?", "What campaign settings changed?"

---

## Installation

```bash
mkdir -p .claude/skills/change-history-checker
curl -o .claude/skills/change-history-checker/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/change-history-checker/SKILL.md
```

---

## Prerequisites

- Google Ads API credentials (YAML config)
- Python with `google-ads` package

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage 118 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
