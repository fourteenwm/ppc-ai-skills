# Budget Recommendation Calculator

A conservative calculation framework for recommending budget changes that won't shock smart bidding algorithms or blow up client CPAs.

**The pain point:** AI wants to be helpful. Ask it to fix underspending and it'll recommend doubling the budget. A week later, your CPA is 3x the goal, the algorithm is thrashing, and the client is furious. This skill forces AI to think like a disciplined PPC specialist — small increases, performance guardrails, ramp-up respect.

---

## The Philosophy

**5-10% increases. Never more. Never aggressive catch-up.**

Why:
- Smart bidding needs 3-7 days to adapt
- Large jumps cause algorithm shock (CPAs spike during adjustment)
- Multiple small increases > one large increase
- Predictable spend changes build client trust

---

## What It Solves

Given pacing variance, impression share metrics, and performance data, the skill answers:

1. **Should we increase budget at all?** (7-check go/no-go decision tree)
2. **If yes, by how much?** (3 calculation methods with adjustment factors)
3. **Daily budget translation** (monthly ÷ days, with proper rounding)
4. **Edge cases** (ramp-up periods, low demand, shared budgets, end-of-month catch-up)

---

## What's Inside

- **Go/No-Go decision tree** — 7 required checks before recommending an increase
- **3 calculation methods:**
  - Pacing-based (primary) with adjustment factor guidelines
  - IS-based (alternative) for estimating spend potential
  - Daily budget translation (tactical)
- **Hard cap: never exceed 10% in single change** — enforced throughout
- **Output templates** — standardized recommendation format (approve) and do-not-increase format (reject)
- **4 edge case playbooks:**
  - Recent budget increase (ramp-up period)
  - Low demand (high IS, low Budget Lost)
  - Shared budget dynamics (reallocation vs increase)
  - End-of-month catch-up (conservative vs aggressive trade-offs)
- **Pre-flight checklist** — 7 quality checks before recommending

---

## Why It Refuses to Help Sometimes

The skill will explicitly recommend **NOT** increasing budget when:
- CPA is >20% over goal (quality fixes required first)
- ROAS is <80% of target
- A budget increase happened in the last 7 days (still ramping)
- Search IS is >80% with low Budget Lost IS (you're demand-capped)
- It's less than 5 days into the month
- It's less than 3 days left in the month

This is the point. AI that refuses to act when the data says "don't" is more valuable than AI that always has an answer.

---

## Installation

```bash
mkdir -p .claude/skills/budget-recommendation-calculator
curl -o .claude/skills/budget-recommendation-calculator/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/budget-recommendation-calculator/SKILL.md
```

---

## When It Activates

Auto-invokes when Claude is asked to:
- Recommend budget changes
- Investigate underspending
- Calculate "how much should we increase this?"
- Determine optimal budget given pacing variance
- Create end-of-month catch-up plans

---

## Prerequisites

- A pacing data source (Google Sheet, spreadsheet, or direct GAQL query for MTD spend vs target)
- Access to impression share metrics (for the IS-based method)
- No external dependencies — this is a calculation framework

---

## Pairs With

- **[impression-share-diagnostics](../impression-share-diagnostics/)** — Diagnose the root cause before calculating the fix
- **[mutation-safety](../mutation-safety/)** — Two-step approval protocol for writing budget changes to live accounts
- **[gaql-query-patterns](../gaql-query-patterns/)** — GAQL templates for pulling budget, spend, and IS data

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
