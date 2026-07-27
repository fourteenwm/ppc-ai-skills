---
name: pmax-asset-automation
description: Audit and fix Performance Max campaign asset automation settings. Opts out of Google's auto-generated headlines, descriptions, videos, and image enhancements that often produce off-brand or hallucinated output. Auto-invoke when user says "audit PMAX asset automation", "check auto-created assets", "fix PMAX automatic assets", or "are PMAX campaigns opted out".
---

# PMax Asset Automation

Audit Performance Max campaigns for Google's five asset-automation settings
and drive them to the house standard: **all five OPTED_OUT**. The audit is
shipped code (`scripts/audit_pmax_asset_automation.py`); the fix is a
documented mutation pattern run under
[mutation-safety](../mutation-safety/). Judgment calls (which flags matter,
when ON is legitimate, triage order) live in [rules.md](rules.md); exact
script mechanics live in
[references/audit-contract.md](references/audit-contract.md).

## Why This Exists

PMax campaigns ship with five asset automations ON by default: Google
generates new text assets, expands your final URLs to pages you didn't
pick, trims/remixes/creates YouTube videos, auto-crops images, and extracts
new images from your landing pages — all served without per-asset approval.
The generated assets frequently drift off-brand or contradict verified
business claims, and the UI offers no portfolio-wide view (one campaign at
a time, buried in Settings → Asset automation). For most serious
advertisers the right default is all five off and manual asset management;
this skill codifies that standard and scales the check across accounts.

## What this skill deliberately does NOT do

- **Never modifies an account.** The shipped script is read-only; there is
  no fix script in this folder. Fixing is a mutation you run through the
  documented pattern below, gated by mutation-safety.
- **Doesn't decide whether OPTED_IN is wrong.** Some ONs are deliberate
  (client strategy, running experiments, evidence-backed exceptions) —
  rules.md owns that call and the coordinate-before-flipping cases.
- **Doesn't see beyond the five tracked types.** REMOVED campaigns are out
  of scope, and any automation type Google ships in the future is invisible
  until the script's list is extended (contract § fixed scope).
- **Doesn't resolve account names.** Except under `--all` (which walks the
  MCC), accounts display as `CID <n>` — bring your own name lookup.
- **Writes nothing to disk.** Console-only; redirect stdout when you need a
  record.

## How to Check in the Google Ads UI (single campaign)

Campaign → **Settings** → expand **Asset automation** → all five toggles
OFF. Fine for one campaign; useless at portfolio scale — that's what the
script is for.

## How to Audit via the API

Requires working Google Ads API access —
[google-ads-api-setup](../google-ads-api-setup/) if you don't have it.

```bash
# Single account
python scripts/audit_pmax_asset_automation.py --cid 1234567890

# Multiple accounts (comma-separated)
python scripts/audit_pmax_asset_automation.py --cids "1234567890,2345678901"

# All accounts under the MCC (uses login_customer_id from your yaml)
python scripts/audit_pmax_asset_automation.py --all

# Credentials somewhere other than ./google-ads.yaml
python scripts/audit_pmax_asset_automation.py --all --config path/to/google-ads.yaml
```

Output: a per-account breakdown — every ENABLED or PAUSED PMax campaign,
its five settings with `[OK]`/`[!]` markers, per-campaign compliance
verdicts, and a portfolio summary. Read it in rules.md's triage order
(**error lines first, count sanity second, findings third**) — the summary
line `All accounts fully compliant!` has two known failure shapes
([examples.md](examples.md) 2 and 3). Full selection semantics, the
seeded-default mechanic, and every console shape:
[references/audit-contract.md](references/audit-contract.md).

## How to Fix via the API (Mutation)

Fixing is a mutation — **it goes through
[mutation-safety](../mutation-safety/). No exceptions.**

1. **Dry run** — show which campaigns will change and which settings go to
   `OPTED_OUT`
2. **User approves** — explicit confirmation required
3. **Execute** — `CampaignService.mutate_campaigns` with an update on
   `asset_automation_settings`
4. **Verify** — re-run the audit ~24h later; settings have been observed
   reverting after campaign edits (rules.md false-alarm table)

Do not batch across accounts without a per-account dry run — PMax settings
affect serving, and a bad portfolio-scale mutation is painful to unwind.
Before fixing anything unexplained, run rules.md's escalation ladder
(attribute via change history first).

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | This file — workflow + routing |
| `rules.md` | Judgment layer: risk ranking of the five settings, when-ON-is-legitimate, triage order, false alarms, escalation ladder, cadence |
| `examples.md` | Three worked reads: the paused-campaign video call, the false "fully compliant", the all-five-ON baseline |
| `references/audit-contract.md` | Line-derived script mechanics: selection, seeded defaults, error isolation, console shapes |
| `scripts/audit_pmax_asset_automation.py` | The audit (read-only, console-only) |

## After a Run

Nothing lands on disk — the report exists only in the console. A cold
session cannot tell an audit ran; redirect stdout
(`> pmax-audit-$(date +%Y%m%d).txt`) to keep a durable record, and always
capture the before/after pair around a fix. Account state never changes
from running the audit.

## When to Load What

| Moment | Load |
|---|---|
| Reading any audit output — triage, risk ranking, is-this-ON-legitimate | [rules.md](rules.md) |
| Exact selection/error/console-shape questions | [references/audit-contract.md](references/audit-contract.md) |
| First read, or the summary looks too clean | [examples.md](examples.md) |
| Any fix — dry run, approval, execute | [mutation-safety](../mutation-safety/) |
| An OPTED_IN nobody can explain — who flipped it, when | [change-history-checker](../change-history-checker/) |
| Same problem, Demand Gen campaigns (ad-level automation) | [dgen-automation-disable](../dgen-automation-disable/) — the ad-level twin |
| Building a new PMax with the opt-outs pre-baked | [pmax-builder](../pmax-builder/) — then audit after import |
| This check as one slice of a full account sweep | [account-diagnostic](../account-diagnostic/) — its automation checks route here to fix |
| No API credentials yet | [google-ads-api-setup](../google-ads-api-setup/) |
| The philosophy behind the standard (*Empty > Inaccurate*) | [ad-copy-verification-standard](../ad-copy-verification-standard/) |

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
