# Investigation Methodology

A hypothesis-driven framework for diagnosing Google Ads performance issues. Teaches AI (and you) to investigate systematically instead of jumping to conclusions.

**The pain point:** When CPA spikes or spend drops, most PPC managers start pulling random reports hoping something jumps out. This leads to hours of unfocused analysis and "gut feel" conclusions. This skill enforces a structured investigation that starts with hypotheses and proves or eliminates them one layer at a time.

---

## What It Does

When you say "investigate why [account] is underperforming," the skill forces a disciplined process:

1. **Define the problem precisely** — not "account is bad" but "CPA increased from $37 to $59 between December and January"
2. **Generate hypotheses BEFORE pulling data** — list 5-8 possible causes before looking at a single report
3. **Gather evidence one layer at a time** — performance metrics first, then traffic quality, then segmentation, then change history
4. **Update probabilities as evidence comes in** — each data point either supports or eliminates a hypothesis
5. **Conclude with a root cause** — not a list of observations, but a specific diagnosis with a recommended fix

---

## Why This Matters

Without structure, AI will:
- Pull every report it can think of and dump raw data at you
- Confirm whatever bias you started with
- List 15 "observations" without connecting them to a root cause
- Miss the actual problem because it never looked in the right place

With this skill, AI becomes a junior analyst who follows a senior analyst's process.

---

## Installation

```bash
mkdir -p .claude/skills/investigation-methodology
cp SKILL.md .claude/skills/investigation-methodology/SKILL.md
```

Then use it:
```
"Investigate why [account name] CPA increased 50% last month"
"Why is [account] underspending by 20% this month?"
"Diagnose the performance drop in [campaign name]"
```

---

## Prerequisites

- Claude Code installed
- Google Ads API access recommended (for pulling live data), but the framework also works with exported data or screenshots

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
