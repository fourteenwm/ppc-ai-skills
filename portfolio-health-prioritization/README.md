# Portfolio Health Prioritization

A 5-tier account prioritization system for daily portfolio health monitoring that determines which accounts to investigate first, based on pacing variance, portfolio-specific thresholds, and focus rules.

**The pain point:** A portfolio health check flags 25 accounts with issues. You can investigate maybe 5 in a day. Which 5? Without a system, you either chase the loudest alert or pick randomly. This skill provides a repeatable algorithm — prioritizing by severity, portfolio SLA, underspend vs. overspend, and recency of change — so you always work on what matters most.

---

## What's Inside

- 5-tier priority system: Critical (investigate immediately), High Priority (today), Medium (this week), Low (monitor), No Action
- Portfolio-specific thresholds that adapt to client SLAs
- 4 focus rules for breaking ties: underspending before overspending, strict-SLA portfolios first, recent changes before historical patterns, high variance before near-threshold
- Prioritization decision tree for classifying any flagged account
- Selection algorithm that picks the top 3-5 accounts for deep investigation
- Integration patterns for daily briefing workflows
- Real-world example: 25 flagged accounts narrowed to 5 investigations

---

## Installation

```bash
mkdir -p .claude/skills/portfolio-health-prioritization
curl -o .claude/skills/portfolio-health-prioritization/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/portfolio-health-prioritization/SKILL.md
```

---

## Prerequisites

None. This is a protocol skill — it works with just Claude Code installed. No API keys or external dependencies required. Customize the portfolio names and thresholds in the SKILL.md to match your client structure.

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage 118 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
