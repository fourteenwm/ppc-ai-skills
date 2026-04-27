# Impression Share Diagnostics

A decision framework for interpreting Google Ads impression share metrics in a smart bidding world — and identifying the true root cause of underspending.

**The pain point:** Every PPC manager has stared at a campaign that's underspending with Rank Lost IS at 78% and wondered "do I need to improve quality or raise budget?" The wrong answer costs you a month of learnings. This skill gives you a decision tree based on which IS metrics are flashing, what bidding strategy you're on, and what's actually recoverable.

---

## What It Solves

Smart bidding broke the old impression share playbook. You can't manually bid anymore. The algorithm controls everything. So what do the IS metrics actually mean now?

This skill tells you:

- **When Budget Lost IS is the primary constraint** (increase budget)
- **When Rank Lost IS is just noise** (leave it alone — it's informational, not a target)
- **When you're hitting a demand ceiling** (don't increase budget, reallocate it)
- **When you're in a ramp-up period** (wait — don't touch it)
- **When display/video campaigns are bid-cap limited** (fix the bid cap, not the budget)

---

## What's Inside

- **4 diagnostic scenarios** with patterns, mechanisms, and recommendations
- **IS patterns cheat sheet** — quick lookup table matching IS values to diagnosis
- **Smart bidding context** — why budget is the primary lever now
- **Budget vs. quality trade-off rules** — when to increase, when to fix quality first
- **Demand ceiling formula** — calculate whether an ad group can actually absorb more budget based on current IS
- **Campaign-type-specific guidance** — Search, PMax, Demand Gen, Display/Video remarketing
- **API gotcha** — the Google Ads API returns IS as decimals (0.0-1.0), not percentages. Get this wrong and your thresholds are off by 100x.

---

## Installation

```bash
mkdir -p .claude/skills/impression-share-diagnostics
curl -o .claude/skills/impression-share-diagnostics/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/impression-share-diagnostics/SKILL.md
```

Or just copy `SKILL.md` into your project's `.claude/skills/impression-share-diagnostics/` folder.

---

## When It Activates

Auto-invokes when Claude sees:
- "impression share", "Search IS", "Budget Lost IS", "Rank Lost IS"
- Underspending investigations
- "Why isn't this campaign spending?"
- Budget increase decisions
- Auction competitiveness analysis

---

## Prerequisites

- Google Ads API access (to pull IS metrics) OR Google Ads UI access
- No external dependencies — this is a reasoning framework, not an executable tool

---

## Pairs With

- **[budget-recommendation-calculator](../budget-recommendation-calculator/)** — After you diagnose the constraint, calculate the conservative fix
- **[investigation-methodology](../investigation-methodology/)** — The broader hypothesis-driven framework this skill plugs into
- **[gaql-query-patterns](../gaql-query-patterns/)** — Ready-made GAQL queries for the IS metrics this skill interprets

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage 118 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
