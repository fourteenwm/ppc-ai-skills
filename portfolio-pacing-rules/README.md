# Portfolio Pacing Rules

Portfolio-specific pacing thresholds, budget tolerances, brand campaign caps, and performance targets that auto-load when analyzing whether accounts are on pace.

**The pain point:** Different clients have different tolerance for budget variance. One client allows 8% deviation, another demands 5%. One measures ROAS, another measures CPA. Without encoded rules, you end up re-explaining thresholds every time or — worse — applying the wrong portfolio's rules to the wrong account. This skill makes pacing rules automatic.

---

## What's Inside

- Per-portfolio pacing thresholds with warning and critical zones
- Brand campaign cap enforcement (e.g., 15% max spend on brand)
- Performance target frameworks: ROAS-focused vs. CPA-focused portfolios
- Month-start normalization rules (reduced severity for days 1-5)
- Budget management philosophy for smart bidding: conservative 5-10% increases, no large jumps
- Pacing variance calculation reference (% Through Month - % Spent)
- Portfolio constraint documentation: shared budgets, campaign structure, reporting format preferences
- Integration with investigation agents and daily monitoring workflows

---

## Installation

```bash
mkdir -p .claude/skills/portfolio-pacing-rules
curl -o .claude/skills/portfolio-pacing-rules/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/portfolio-pacing-rules/SKILL.md
```

---

## Prerequisites

None. This is a protocol skill — it works with just Claude Code installed. No API keys or external dependencies required. Edit the SKILL.md to replace example portfolio names and thresholds with your own client data.

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage 118 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
