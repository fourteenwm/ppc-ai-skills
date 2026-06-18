# DGen Automation Disable

Bulk-disable ad-level asset automation settings across Demand Gen campaigns — the auto-generated design variations, auto-created videos, and landing page previews that reduce creative control.

**The pain point:** Demand Gen campaigns ship with multiple asset automation settings turned ON by default at the ad level (not campaign level like PMax). Google auto-generates design variations from your images, creates videos from your assets, and adds landing page previews — all without asking. Across a managed portfolio, manually toggling these off in every ad across every account doesn't scale. This skill does it in one batch.

---

## What's Inside

- Bulk disable of 5 DGen ad-level automation settings across DemandGenMultiAssetAd and DemandGenVideoResponsiveAd types
- Dry-run preview by default — shows exactly what will change before anything happens
- Two-step MutationGuard approval workflow with unique approval codes
- Per-account error handling — one failure doesn't stop the batch
- Dual logging: local JSONL file and Google Sheets mutation log
- Supports single account, portfolio filter, or all accounts
- Post-execution verification option

---

## Installation

```bash
mkdir -p .claude/skills/dgen-automation-disable
curl -o .claude/skills/dgen-automation-disable/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/dgen-automation-disable/SKILL.md
```

---

## Prerequisites

- Google Ads API credentials (YAML config) with write access
- Python with `google-ads` package
- The `mutation-safety` skill (for the two-step approval protocol)
- Google Sheets API credentials (for mutation logging)

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
