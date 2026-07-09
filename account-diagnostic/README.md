# Account Diagnostic

A 40-point Google Ads account inspection — like a mechanic's multi-point vehicle inspection, but for ad accounts. Every check produces a discrete GREEN/YELLOW/RED verdict with a finding, an estimated dollar impact where one exists, and an action line.

**The pain point:** "Audit this account" usually produces a wall of narrative you still have to interpret. An inspection checklist doesn't negotiate — 40+ discrete checks either pass or they don't, and the ones that fail come with a dollar figure and a next step. Run it on any account and you know in two minutes where the problems are.

---

## What's Inside

- **44 checks across 14 categories** (40 core + preset extras): conversion tracking, budget & pacing, impression share, quality score, search-term waste, keyword health, creative & ads, RSA assets, account settings, PMAX config, negative keywords, placement safety, extensions, and video & Demand Gen automation
- **Demand Gen ad-level automation check** — DGen asset automation lives on the *ad*, not the campaign, so campaign-scoped audits miss it entirely; this inspects all five ad-level settings (most default ON)
- **PMAX automation sweep** — text assets, image extraction/enhancement, video enhancements, final URL expansion
- **Two vertical presets** — `property-management` (strict pacing, lead-gen) and `local-service` (phone-driven, adds call/location extension checks)
- **Scored verdict** — auto-red circuit breakers, overall GREEN/YELLOW/RED, estimated monthly waste
- **Three output modes** — console report, CSV, and an optional color-coded Google Sheet tab

---

## Installation

Tool-backed skill — clone the repo so you get the `scripts/` folder:

```bash
git clone https://github.com/fourteenwm/ppc-ai-skills.git
cp -r ppc-ai-skills/account-diagnostic .claude/skills/account-diagnostic
```

---

## Prerequisites

- Google Ads API credentials (`google-ads.yaml` in the skill folder — see [google-ads-api-setup](../google-ads-api-setup/))
- Python with the `google-ads` package
- Optional, for `--sheet-id` Sheet output: `gspread` + `google-auth` with a service account

---

## Usage

```bash
cd account-diagnostic

# Basic inspection (console + CSV)
python scripts/run_diagnostic.py --cid 1234567890

# Local-service calibration, 60-day lookback
python scripts/run_diagnostic.py --cid 1234567890 --vertical local-service --days 60

# Also write the color-coded tab into a sheet you own
python scripts/run_diagnostic.py --cid 1234567890 --sheet-id YOUR_SHEET_ID
```

---

## Output

```
======================================================================
  42-POINT GOOGLE ADS INSPECTION
======================================================================
  --- BUDGET & PACING ---
  [X]  5. MTD pacing within tolerance
       RED: +34.0% underspent (threshold: +/-8%) ($21,784)
       -> Immediate action needed — $21,784/mo gap
  ...
  --- VIDEO & DGEN AUTOMATION ---
  [+] 44. DGen ad-level automation disabled
       GREEN: All automation OFF across 74 DGen ad(s)

======================================================================
  OVERALL: RED
  26 Green | 6 Yellow | 10 Red | 0 N/A
  Estimated waste: $48,531/mo
======================================================================
```

Plus `data/diagnostic-<cid>-<timestamp>.csv`, and the `Inspection` sheet tab if requested.

---

## Related Skills

- [dgen-automation-disable](../dgen-automation-disable/) — fixes what check 44 flags (with dry-run + approval gate)
- [pmax-asset-automation](../pmax-asset-automation/) — deeper PMAX automation management
- [underspending-investigation](../underspending-investigation/) — root-cause diagnosis when checks 5-8 fire
- [mutation-safety](../mutation-safety/) — install before acting on any finding
