# Investigation Methodology

A hypothesis-driven framework for diagnosing Google Ads performance issues. Teaches AI (and you) to investigate systematically instead of jumping to conclusions.

**The pain point:** When CPA spikes or spend drops, most PPC managers start pulling random reports hoping something jumps out. This leads to hours of unfocused analysis and "gut feel" conclusions. This skill enforces a structured investigation that starts with hypotheses and proves or eliminates them one layer at a time.

![Sequence diagram: a PPC manager reports vague underperformance; the AI analyst sharpens it into a precise problem statement — which metric, before vs now, over what period — lists 5-8 hypotheses before touching any data, then pulls evidence one layer at a time, updating every hypothesis after each layer, and closes with a verdict: one root cause, the evidence that proves it, and one specific fix; inconclusive is a valid answer, guessing is not](diagrams/workflow-hero.svg)

---

## What It Does

When you say "investigate why [account] is underperforming," the skill forces a disciplined process:

1. **Define the problem precisely** — not "account is bad" but "CPA increased from $37 to $59 between December and January"
2. **Generate hypotheses BEFORE pulling data** — list 5-8 possible causes before looking at a single report
3. **Gather evidence one layer at a time** — performance metrics first, then traffic quality, then segmentation, then change history
4. **Update probabilities as evidence comes in** — each data point either supports or eliminates a hypothesis
5. **Conclude with a root cause** — not a list of observations, but a specific diagnosis with a recommended fix

The loop in one view:

![Flowchart of the hypothesis loop in three phases: frame the problem (sharpen vague statements into a precise metric-before-after-period question, then list 5-8 hypotheses across internal, external, and measurement categories before pulling any data), the evidence loop (pull one layer at a time, update each hypothesis as supported, weakened, or eliminated, and repeat until one clear root cause emerges — or layers run out, in which case say so and flag what needs manual digging), and verdict (one root cause stated in a sentence, the 3-5 data points that prove it, a hypothesis scorecard, and a recommendation with numbers, not vibes)](diagrams/run-logic.svg)

The `.mmd` sources for both diagrams live in `diagrams/` — they're
[Mermaid](https://mermaid.js.org/) diagram-as-code, rendered with the included
`theme.json`.

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
