---
name: account-diagnostic
description: 40-point Google Ads account inspection — discrete GREEN/YELLOW/RED checks across 14 categories (conversion tracking, pacing, impression share, quality score, search-term waste, keyword health, creative, RSA assets, account settings, PMAX config, negative keywords, placement safety, extensions, video & Demand Gen automation), scored into one overall verdict with estimated monthly waste. Auto-invoke when user says 'run diagnostic', 'inspect account', '40-point inspection', 'diagnostic for [account]', 'audit [account]', or 'account health check'.
allowed-tools: [Bash, Read]
---

# 40-Point Account Diagnostic

Like a mechanic's multi-point vehicle inspection, but for Google Ads accounts. Every check lands on an explicit GREEN/YELLOW/RED verdict with a finding, a dollar impact where one can be estimated, and a "do this" action line — no narrative to interpret.

---

## Invocation Triggers

Auto-invoke when user says:
- "Run diagnostic for [account]"
- "Inspect [account]"
- "40-point inspection"
- "Audit [account]" / "account health check"
- "Account diagnostic"

---

## How to Run

```bash
cd account-diagnostic
python scripts/run_diagnostic.py --cid 1234567890
```

### Options

```
--cid CID              Customer ID (no dashes) — required
--name NAME            Account name (optional, display only)
--days N               Lookback period (default: 30)
--vertical V           Calibration preset: property-management | local-service
                       (default: property-management)
--pacing-threshold N   Pacing tolerance % (overrides the vertical preset)
--sheet-id ID          Optional: write the color-coded Inspection tab into an
                       existing Google Sheet (gspread service-account auth)
```

---

## The Checks

| # | Category | Covers |
|---|----------|--------|
| 1-3 | Conversion Tracking | Primary actions exist, firing recently, no orphans/duplicates |
| 4-6 | Budget & Pacing | Spending at all, MTD pacing vs tolerance, projected EOM vs budget |
| 7-9 | Impression Share | Search IS, Budget Lost IS ($ opportunity), Rank Lost IS |
| 10-11 | Quality Score | Average QS, low-QS concentration |
| 12-13 | Search Terms | Zero-conversion waste %, high-spend zero-conv terms |
| 14-16 | Keyword Health | Serving rate, high-spend zero-conv keywords, match-type mix |
| 17-22 | Creative & Ads | Disapprovals, DKI, auto-created assets, dead URLs, seasonal copy, auto-apply |
| 23-25 | RSA Assets | Performance labels, LOW-rated control, BEST-rated existence |
| 26-29 | Account Settings | Location targeting mode, content suitability, auto-apply, geo exclusions |
| 30-34 | PMAX Config | Text/image automation, URL expansion, search themes, audience signals |
| 35-36 | Negative Keywords | Coverage per campaign, negative-vs-positive conflicts |
| 37-38 | Placement Safety | Suspicious placements, brand-unsafe YouTube placements |
| 39-40 | Extensions | Core (sitelinks/callouts), supplemental (snippets/images) |
| 41-42 | Local Service *(local-service preset only)* | Call extensions, location extensions |
| 43-44 | Video & DGen Automation | PMAX video enhancements; Demand Gen **ad-level** asset automation |

Check 44 matters because Demand Gen automation lives on the **ad** (`ad_group_ad.ad_group_ad_asset_automation_settings`), not the campaign — campaign-level audits structurally can't see it. Five settings are inspected per ad (design versions for images, generate-videos-from-assets, vertical conversion, shorter videos, landing-page preview), all but one of which default **ON**. Pair with the `dgen-automation-disable` skill to fix what this check flags.

---

## Scoring

- **Overall RED:** any auto-red circuit breaker (e.g. no conversion tracking), or 3+ RED checks
- **Overall YELLOW:** 1-2 RED, or 6+ YELLOW
- **Overall GREEN:** everything else
- **Estimated waste/mo:** sum of the dollar impacts across flagged checks (pacing gap and EOM projection overlap — read it as a ceiling, not a precise total)

Checks that don't apply (e.g. PMAX checks on an account with no PMAX) report N/A and don't count against the score.

---

## Vertical Presets

| Preset | Tuned for | Differences |
|--------|-----------|-------------|
| `property-management` | Lead-gen portfolios with strict pacing | Baseline: pacing ±8%, seasonal copy & missing geo-exclusions are RED, negative bar 20/campaign |
| `local-service` | Phone-driven local businesses (auto repair, home services) | Pacing ±10%, seasonal copy & missing geo-exclusions soften to YELLOW, negative bar 10, lower zero-conv dollar floors, adds checks 41-42 |

---

## Output

1. **Console report** — grouped by category, with icons, findings, and actions
2. **CSV** — full checklist written to `data/diagnostic-<cid>-<timestamp>.csv`
3. **Google Sheet** *(optional, `--sheet-id`)* — color-coded `Inspection` tab written into a sheet you own; requires a gspread service account (share the sheet with the service account's `client_email`)

---

## Prerequisites

- `google-ads.yaml` in the skill folder — see the `google-ads-api-setup` skill
- `pip install google-ads` (plus `gspread google-auth` if using `--sheet-id`)
- Google Ads API access at whatever level your yaml grants (single account or MCC with `login_customer_id`)

---

## Safety

Read-only. This skill runs GAQL SELECT queries exclusively — it never mutates an account. Fixing what it finds is a separate, human-approved step (see `mutation-safety`).
