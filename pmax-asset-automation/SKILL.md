---
name: pmax-asset-automation
description: Audit and fix Performance Max campaign asset automation settings. Opts out of Google's auto-generated headlines, descriptions, videos, and image enhancements that often produce off-brand or hallucinated output. Auto-invoke when user says "audit PMAX asset automation", "check auto-created assets", "fix PMAX automatic assets", or "are PMAX campaigns opted out".
---

# PMax Asset Automation

**Purpose:** Audit and fix Performance Max campaign settings for Google's automatically created assets.

**Type:** Settings compliance + optional mutation skill

---

## Why This Exists

Performance Max campaigns ship with five asset automation settings turned ON by default. Google will:

1. Generate new text assets (headlines, descriptions) it thinks will perform well
2. Expand your final URLs to pages you did not select
3. Enhance your YouTube videos (trim, remix, generate new ones)
4. Auto-crop images to new aspect ratios
5. Extract images from your landing pages into new assets

The upside: Google fills gaps in your asset library automatically. The downside: the generated assets frequently drift off-brand, contradict verified business claims, or pull images from pages the advertiser would never have chosen. There is no per-asset approval — Google just serves what it generated.

For most serious advertisers, the right default is **all five settings OPTED_OUT** and manual asset management. This skill codifies that standard and gives you a workflow to audit + enforce it across accounts.

---

## Settings Checked

| Setting | What Google Does When ON | Preferred |
|---------|--------------------------|-----------|
| `TEXT_ASSET_AUTOMATION` | Generates new headlines and descriptions it predicts will perform | `OPTED_OUT` |
| `FINAL_URL_EXPANSION_TEXT_ASSET_AUTOMATION` | Expands final URLs to any page on the domain and generates matching ad copy | `OPTED_OUT` |
| `GENERATE_ENHANCED_YOUTUBE_VIDEOS` | Edits, trims, or remixes your YouTube videos automatically | `OPTED_OUT` |
| `GENERATE_IMAGE_ENHANCEMENT` | Auto-crops images to produce new aspect ratios | `OPTED_OUT` |
| `GENERATE_IMAGE_EXTRACTION` | Extracts images from your landing pages into new ad assets | `OPTED_OUT` |

---

## How to Check in the Google Ads UI

For a single campaign:

1. Open the campaign → **Settings**
2. Expand **Asset automation**
3. Verify each of the five toggles is OFF
4. Save

For a portfolio-wide view, the UI forces you to click into each campaign one at a time. That is why the API-based audit below exists — it scales to dozens or hundreds of campaigns.

---

## How to Audit via the API

This skill assumes you have working Google Ads API access. See the [google-ads-api-setup](../google-ads-api-setup/) skill if you do not.

### Quick Start — Use the Included Script

A working implementation ships with this skill at `scripts/audit_pmax_asset_automation.py`. Usage:

```bash
# Single account
python scripts/audit_pmax_asset_automation.py --cid 1234567890

# Multiple accounts (comma-separated)
python scripts/audit_pmax_asset_automation.py --cids "1234567890,2345678901"

# All accounts under the MCC
python scripts/audit_pmax_asset_automation.py --all
```

Output is a per-account breakdown showing each PMax campaign's asset automation settings with compliance status (all should be `OPTED_OUT` for full compliance). Uses `google-ads.yaml` at the project root for credentials.

### What the Query Looks Like

The audit query pulls asset automation settings for every active PMax campaign and reports which ones are not at the preferred standard. A typical implementation:

```python
from google.ads.googleads.client import GoogleAdsClient

query = """
SELECT
  campaign.id,
  campaign.name,
  campaign.advertising_channel_type,
  campaign.asset_automation_settings
FROM campaign
WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
  AND campaign.status = 'ENABLED'
"""
```

For each campaign, iterate through `asset_automation_settings` and flag any setting where `asset_automation_status != 'OPTED_OUT'` for the five types listed above.

Output a per-campaign report: campaign name, CID, which settings are ON, and recommended action.

---

## How to Fix via the API (Mutation)

Once the audit surfaces non-compliant campaigns, fixing them is a mutation. **That means it goes through [mutation-safety](../mutation-safety/).** No exceptions.

The typical flow:

1. **Dry run** — Show which campaigns will be modified and which specific settings will be set to `OPTED_OUT`
2. **User approves** — Explicit confirmation required
3. **Execute** — Apply the mutation using `CampaignService.mutate_campaigns` with an update operation on `asset_automation_settings`

Do not batch this across accounts without a per-account dry run. PMax settings affect serving behavior — a bad mutation at portfolio scale is painful to clean up.

---

## When to Use This Skill

- **New account setup** — run the audit immediately after creating any PMax campaign
- **Portfolio compliance checks** — run the audit monthly to catch settings that were changed (by you, by a team member, or by Google's "helpful" defaults reappearing after campaign edits)
- **Client handoff** — audit all PMax campaigns before taking over a new account
- **Post-mutation verification** — re-run the audit 24 hours after applying fixes to confirm the settings stuck

---

## Edge Cases and Caveats

- **Some industries genuinely benefit from text asset automation.** High-volume ecommerce accounts with weak creative teams sometimes see better performance with `TEXT_ASSET_AUTOMATION` ON. Audit first, opt out as default, leave it on only when you have data proving it helps.
- **Image extraction from URLs** is the riskiest setting. Google will pull images from any page on the landing domain — including pages the advertiser may not want represented in ads. Opt out of this one even if you are OK with other automations.
- **Final URL expansion** is independently controversial. Some advertisers deliberately use it to widen PMax reach. If you want URL expansion, opt out of `TEXT_ASSET_AUTOMATION` only and leave `FINAL_URL_EXPANSION_TEXT_ASSET_AUTOMATION` ON — but be prepared to review the expanded URL set regularly.
- **The settings reset silently.** Google has been observed flipping automations back on after certain campaign edits. That is why periodic auditing matters — set it and forget it does not work here.

---

## Related Skills

- [`mutation-safety`](../mutation-safety/) — **required** for any fix operation
- [`google-ads-api-setup`](../google-ads-api-setup/) — prerequisite for API-based audit + fix
- [`ad-copy-verification-standard`](../ad-copy-verification-standard/) — the underlying philosophy: *Empty > Inaccurate.* Google's auto-generated assets frequently violate this.
- [`dgen-automation-disable`](../dgen-automation-disable/) — companion skill for Demand Gen ad-level asset automation

---

## Installation

```bash
mkdir -p .claude/skills/pmax-asset-automation
curl -o .claude/skills/pmax-asset-automation/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/pmax-asset-automation/SKILL.md
```

No other setup required. The skill loads automatically when Claude Code sees any PMax-related audit, fix, or compliance task.
