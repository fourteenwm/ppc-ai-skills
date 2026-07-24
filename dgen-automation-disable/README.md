# DGen Automation Disable

Bulk-disable ad-level asset automation settings across Demand Gen campaigns — the auto-generated design variations, auto-created videos, and landing page previews that reduce creative control.

**The pain point:** Demand Gen campaigns ship with multiple asset automation settings turned ON by default at the ad level (not campaign level like PMax). Google auto-generates design variations from your images, creates videos from your assets, and adds landing page previews — all without asking. Across a managed portfolio, manually toggling these off in every ad across every account doesn't scale. This skill does it in one batch.

---

## What's Inside

- Bulk disable of 5 DGen ad-level automation settings across DemandGenMultiAssetAd and DemandGenVideoResponsiveAd types
- Dry-run preview by default — shows exactly what will change before anything happens
- Two-step approval workflow with deterministic approval codes (the mutation-safety pattern): any account drift between preview and execute refuses safely
- Per-account error handling — one failure doesn't stop the batch, and each account's mutation is all-or-nothing
- Logging: local JSONL file always on for executes; central Google Sheets log opt-in
- Supports a single account, a CID list, or every enabled account under your MCC
- Post-execution verification option (single account)
- Operator docs: `rules.md` (the five dry-run reads, when NOT to disable, mismatch handling, cadence), `examples.md` (a clean run, a drift mismatch, a false compliance), `references/mutation-contract.md` (exact selection/hash/logging mechanics)

---

## Installation

```bash
mkdir -p .claude/skills/dgen-automation-disable/scripts .claude/skills/dgen-automation-disable/references
for f in SKILL.md README.md rules.md examples.md; do
  curl -o .claude/skills/dgen-automation-disable/$f \
    https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/dgen-automation-disable/$f
done
curl -o .claude/skills/dgen-automation-disable/references/mutation-contract.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/dgen-automation-disable/references/mutation-contract.md
curl -o .claude/skills/dgen-automation-disable/scripts/fix_dgen_ad_automation.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/dgen-automation-disable/scripts/fix_dgen_ad_automation.py
```

---

## Prerequisites

- Google Ads API credentials (YAML config) with write access — see [google-ads-api-setup](../google-ads-api-setup/)
- Python with `google-ads` package (plus `google-auth` and `google-api-python-client` if you use the optional Sheet log)
- The `mutation-safety` skill (for the two-step approval protocol)
- Optional: for `--log-sheet-id`, the refresh token in your `google-ads.yaml` must carry the spreadsheets scope (the api-setup generator's default token does) — the always-on local JSONL log needs nothing extra

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
