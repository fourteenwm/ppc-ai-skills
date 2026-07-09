# Portfolio Health Prioritization

A 5-tier account prioritization system for daily portfolio health monitoring that determines which accounts to investigate first, based on pacing variance, portfolio-specific thresholds, and focus rules.

**The pain point:** A portfolio health check flags 25 accounts with issues. You can investigate maybe 5 in a day. Which 5? Without a system, you either chase the loudest alert or pick randomly. This skill provides a repeatable algorithm — prioritizing by severity, portfolio SLA, underspend vs. overspend, and recency of change — so you always work on what matters most.

![Sequence diagram: the morning portfolio health check flags 25 accounts across pacing, zero spend, and tracking; the manager has room for maybe 5 deep dives, so the triage AI tiers every account from 1-critical through 5-no-action and breaks ties with focus rules — underspend first, strict-SLA book first, sudden shifts before seasonal patterns — returning today's list of 3-5 investigations with everything else tiered in the briefing; same inputs, same order, every day](diagrams/workflow-hero.svg)

---

## What's Inside

- 5-tier priority system: Critical (investigate immediately), High Priority (today), Medium (this week), Low (monitor), No Action
- Portfolio-specific thresholds that adapt to client SLAs
- 4 focus rules for breaking ties: underspending before overspending, strict-SLA portfolios first, recent changes before historical patterns, high variance before near-threshold
- Prioritization decision tree for classifying any flagged account
- Selection algorithm that picks the top 3-5 accounts for deep investigation
- Integration patterns for daily briefing workflows
- Real-world example: 25 flagged accounts narrowed to 5 investigations

The decision tree in one view:

![Flowchart of the 5-tier triage decision tree in three phases: hard thresholds (variance beyond plus-or-minus 15% is Tier 1 critical, investigated same day with no exceptions; variance outside the portfolio's own tolerance — strict books at 5%, standard at 8% — is Tier 2 high priority within 24 hours), soft signals (zero spend this month or sharp deterioration inside 7 days is Tier 2; tracking issues, disapprovals, or campaigns ending soon are Tier 3 this week; accounts creeping toward the threshold are Tier 4 monitored for a few days; everything else is Tier 5 on pace, where most of the portfolio lives), and build the day (every Tier 1 account gets investigated, Tier 2 fills the remaining slots — underspend before overspend, strict-SLA book first, biggest variance first — and everything else is listed by tier in the briefing, seen but not chased)](diagrams/run-logic.svg)

The `.mmd` sources for both diagrams live in `diagrams/` — they're
[Mermaid](https://mermaid.js.org/) diagram-as-code, rendered with the included
`theme.json`.

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

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
