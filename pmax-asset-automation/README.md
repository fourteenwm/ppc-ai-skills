# PMax Asset Automation

Audit and fix Performance Max campaign asset automation settings. Opts out of Google's auto-generated headlines, descriptions, videos, and image enhancements that often produce off-brand or hallucinated output.

**The pain point:** Performance Max ships with five asset automation settings turned ON by default. Google generates new text assets, expands your final URLs, edits your YouTube videos, auto-crops images, and extracts new images from your landing pages — all without per-asset approval. The generated assets frequently drift off-brand or contradict verified business claims. There is no UI for portfolio-wide auditing — you have to click into each campaign one at a time. This skill codifies the "all five OPTED_OUT" standard and gives you an API-based workflow to audit and enforce it at scale.

---

## What's Inside

- A ready-to-run portfolio audit script (`--cid`, `--cids`, or `--all` under
  an MCC; `--config` for a non-default credentials path) — read-only,
  console output with per-campaign compliance verdicts
- The five PMax asset automation settings and why each one matters
- How to check settings in the Google Ads UI (for single campaigns)
- Mutation pattern for fixing non-compliant campaigns (wrapped in mutation-safety)
- Operator docs: `rules.md` (risk ranking, when ON is legitimate, triage
  order, escalation ladder), `examples.md` (three worked reads incl. the
  false "fully compliant"), and `references/audit-contract.md` (exact
  script mechanics, line-cited)

---

## Installation

```bash
mkdir -p .claude/skills/pmax-asset-automation/scripts .claude/skills/pmax-asset-automation/references
for f in SKILL.md README.md rules.md examples.md; do
  curl -o .claude/skills/pmax-asset-automation/$f \
    https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/pmax-asset-automation/$f
done
curl -o .claude/skills/pmax-asset-automation/references/audit-contract.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/pmax-asset-automation/references/audit-contract.md
curl -o .claude/skills/pmax-asset-automation/scripts/audit_pmax_asset_automation.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/pmax-asset-automation/scripts/audit_pmax_asset_automation.py
```

---

## Prerequisites

- [Google Ads API](../google-ads-api-setup/) set up for the audit and fix workflows (`google-ads.yaml` at project root, or point the script at it with `--config`)
- [Mutation Safety](../mutation-safety/) skill installed if you plan to run the fix mutation

No API keys or external dependencies beyond what you already need for Google Ads API access.

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
