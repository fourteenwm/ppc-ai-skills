---
name: dgen-automation-disable
description: Bulk-disable Demand Gen ad-level asset automation settings. Auto-invoke when user says "disable dgen automation", "fix dgen asset settings", "turn off dgen auto assets", "dgen automation fix", or "fix demand gen automation".
allowed-tools: [Bash, Read]
---

# DGen Ad-Level Automation Disable

**Purpose:** Programmatically set all Demand Gen ad-level asset automation settings to `OPTED_OUT` across one or many accounts.

**Type:** Mutation skill (two-step approval required)

---

## Auto-Invoke When

- "disable dgen automation"
- "fix dgen asset settings"
- "turn off dgen auto assets"
- "dgen automation fix"
- "fix demand gen automation"

---

## Background

Demand Gen asset automation operates at the **ad level** (not campaign level like PMax). Google auto-generates creative variations that frequently drift off-brand or reduce quality control for managed accounts.

### Settings Controlled

**DemandGenMultiAssetAd:**
| Setting | Description | Default |
|---------|-------------|---------|
| `GENERATE_DESIGN_VERSIONS_FOR_IMAGES` | Adds design elements to images | ON |
| `GENERATE_VIDEOS_FROM_OTHER_ASSETS` | Generates videos from images/text | ON |

**DemandGenVideoResponsiveAd:**
| Setting | Description | Default |
|---------|-------------|---------|
| `GENERATE_VERTICAL_YOUTUBE_VIDEOS` | Converts horizontal to vertical | ON |
| `GENERATE_SHORTER_YOUTUBE_VIDEOS` | Shortens videos | ON |
| `GENERATE_LANDING_PAGE_PREVIEW` | Landing page screenshot in ads | OFF (but found ON in some accounts) |

`DEMAND_GEN_CAROUSEL_AD` and `DEMAND_GEN_PRODUCT_AD` have no automation settings — skipped.

---

## Two-Step Mutation Flow

This skill follows the [`mutation-safety`](../mutation-safety/) pattern. **Never skip the dry-run, never auto-approve.**

### Step 1 — Dry-run preview

```bash
# Single account
python scripts/fix_dgen_ad_automation.py --cid 1234567890

# Multiple accounts (comma-separated CIDs)
python scripts/fix_dgen_ad_automation.py --cids "1234567890,2345678901"

# All enabled accounts under the MCC
python scripts/fix_dgen_ad_automation.py --all
```

Output includes:
- Per-account list of ads needing changes
- Specific settings that will flip from `OPTED_IN` → `OPTED_OUT`
- Total count (ads, settings, accounts)
- An **APPROVAL CODE** like `APPROVE-A3F9B2C1`

### Step 2 — Execute with approval code

```bash
python scripts/fix_dgen_ad_automation.py --cid 1234567890 APPROVE-A3F9B2C1
```

The script:
- Re-computes the approval code from current ad state
- Refuses to execute if the code doesn't match (safety net if ads changed since the dry-run)
- Mutates via `AdGroupAdService.mutate_ad_group_ads`
- Writes to local log at `./logs/mutations_log.jsonl`
- Optionally writes to a Google Sheet log (`--log-sheet-id`)

### Step 3 — Verify (optional, single-account only)

```bash
python scripts/fix_dgen_ad_automation.py --cid 1234567890 APPROVE-A3F9B2C1 --verify
```

Re-queries the account and confirms every DGen ad is now `OPTED_OUT` on all applicable settings. Reports any non-compliant ads.

### How the approval code works

The code is a SHA-256 hash of the sorted `(cid, ad_id, settings_to_fix)` tuples across all pending mutations, truncated to 8 hex chars.

- **Deterministic:** same pending work → same code. No state file needed.
- **Safe against drift:** if ads change between dry-run and execute (new ads, settings changed by Google's defaults reappearing, etc.), the code changes and execution is refused.

---

## CLI Reference

| Flag | Default | Purpose |
|------|---------|---------|
| `--cid CID` | — | Single account (mutually exclusive with `--cids`/`--all`) |
| `--cids CID1,CID2,...` | — | Multiple accounts |
| `--all` | — | All enabled non-manager accounts under `login_customer_id` from google-ads.yaml |
| `approval_code` (positional) | — | `APPROVE-XXXXXXXX` from dry-run. Omit for dry-run mode. |
| `--config` | `google-ads.yaml` | Path to Google Ads credentials YAML |
| `--log-dir` | `logs` | Directory for local JSONL mutation log |
| `--log-sheet-id` | *(off)* | Optional Google Sheet ID for central mutation log |
| `--verify` | off | Post-execute re-query (single account only) |

---

## Mutation Logging

### Local (always on)

Every execution appends to `./logs/mutations_log.jsonl`:

```json
{"timestamp_utc": "2026-04-23T15:30:00+00:00", "approval_code": "APPROVE-A3F9B2C1",
 "account_cid": "1234567890", "account_name": "Example Account", "action_type": "DISABLE_DGEN_AUTOMATION",
 "details": {"ads_updated": 3, "settings_changed": [...], "ad_types": [...]},
 "success": true, "error": null}
```

This is your audit trail. The script creates the directory if it doesn't exist.

### Google Sheet (opt-in)

Pass `--log-sheet-id YOUR_SHEET_ID` to also log to a central Sheet with columns:
`Timestamp | Account | CID | Action Type | Details | Success | Error | Approval Code`

Uses the refresh token in `google-ads.yaml` — that token must have the spreadsheets scope.

---

## CRITICAL Implementation Note

**Replacement behavior:** When updating `ad_group_ad_asset_automation_settings`, you must specify ALL applicable settings for the ad type. If you only specify one, the others reset to defaults (`OPTED_IN`).

The script handles this correctly — it always sets every applicable setting for each ad type. If you write your own tooling against this field, do the same.

---

## Prerequisites

1. **Google Ads API credentials** — `google-ads.yaml` at project root (see [`google-ads-api-setup`](../google-ads-api-setup/))
2. **Python:** `pip install google-ads google-auth google-api-python-client pyyaml`
3. **For `--log-sheet-id`:** the refresh token in `google-ads.yaml` must include `https://www.googleapis.com/auth/spreadsheets` scope

---

## Installation

```bash
mkdir -p .claude/skills/dgen-automation-disable/scripts
curl -o .claude/skills/dgen-automation-disable/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/dgen-automation-disable/SKILL.md
curl -o .claude/skills/dgen-automation-disable/scripts/fix_dgen_ad_automation.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/dgen-automation-disable/scripts/fix_dgen_ad_automation.py
```

---

## Related Skills

- [`mutation-safety`](../mutation-safety/) — two-step approval pattern this skill implements
- [`pmax-asset-automation`](../pmax-asset-automation/) — PMax equivalent (campaign-level, not ad-level)
- [`ad-copy-verification-standard`](../ad-copy-verification-standard/) — the underlying philosophy: *Empty > Inaccurate.* Google's auto-generated assets frequently violate this.

---

## When to Run

- **Post-onboarding** — run once after taking over any new account with DGen campaigns
- **Periodic audit** — DGen settings are observed to reset silently after certain campaign edits. Re-run monthly to catch drift.
- **Before a brand-sensitive launch** — confirm no auto-generation is active right before a new creative goes live
