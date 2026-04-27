# SQR 3-Run Consistency Pipeline

Production search query classification using 3 independent Claude Code Task agents for consensus-based confidence — no external API costs.

**The pain point:** Single-pass LLM classification of search queries produces inconsistent results. Run the same prompt twice and you get different categories for edge-case queries. This skill runs 3 independent classification passes in parallel using Sonnet Task agents, then only surfaces queries where 2+ runs agree on "off-brand" — giving you consensus-based confidence without paying for external API calls.

---

## What's Inside

- 3-run parallel classification using Claude Code Task agents (Sonnet 4.6)
- Consensus logic: 3-3 unanimous (highest confidence) and 2-3 majority tabs in output sheet
- No external API costs — classification runs through your Claude AI subscription
- Prep, Classify, Compare pipeline with clear handoffs between stages
- Human review columns in output sheet for final approval before negative keyword upload
- Max-batches flag for testing the pipeline end-to-end on small sets
- Integration with upstream prep script and downstream SQR upload skill

---

## Installation

```bash
mkdir -p .claude/skills/sqr-3run
curl -o .claude/skills/sqr-3run/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/sqr-3run/SKILL.md
```

---

## Prerequisites

- Claude Code with Task agent support (for spawning 3 parallel classification agents)
- Google Sheets API credentials (for reading/writing SQR data)
- Python for prep and compare scripts
- The `offbrand-analyzer` skill's `prompt.md` (classification prompt used by each agent)

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage 118 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
