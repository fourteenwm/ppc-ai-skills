# YouTube Placement Brand Safety Audit

Scan your Google Ads MCC for bad YouTube placements across PMAX, Demand Gen, and Display campaigns. Flag brand safety violations, write results to Google Sheets, then aggregate by channel for bulk negation.

**The pain point:** PMAX and Demand Gen serve your ads on YouTube placements you never chose. Without auditing, your ads end up on kids' channels, foreign-language content, adult videos, and spam. This skill finds those placements across your entire portfolio and gives you a clean list of channels to negate.

---

## What It Does

Two scripts that work together:

1. **`youtube_placement_audit.py`** — Scans all accounts under your MCC, pulls YouTube placements, flags violations (kids, adult, gaming, non-English, spam), writes to Google Sheets in two tabs.

2. **`youtube_channel_extractor.py`** — Reads flagged videos from your sheet, looks up which channel each video belongs to via YouTube Data API, aggregates by channel. This is where the real leverage is: 24,000 flagged videos collapse to ~9,000 channels, and each channel exclusion blocks ALL future videos.

---

## Installation

```bash
mkdir -p .claude/skills/youtube-placement-audit/scripts
curl -o .claude/skills/youtube-placement-audit/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/youtube-placement-audit/SKILL.md
curl -o .claude/skills/youtube-placement-audit/scripts/youtube_placement_audit.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/youtube-placement-audit/scripts/youtube_placement_audit.py
curl -o .claude/skills/youtube-placement-audit/scripts/youtube_channel_extractor.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/youtube-placement-audit/scripts/youtube_channel_extractor.py
```

---

## Quick Start

### 1. Install dependencies
```bash
pip install google-ads gspread google-auth google-api-python-client pyyaml
```

### 2. Set up credentials

You need a `google-ads.yaml` file:
```yaml
client_id: YOUR_CLIENT_ID
client_secret: YOUR_CLIENT_SECRET
refresh_token: YOUR_REFRESH_TOKEN
developer_token: YOUR_DEVELOPER_TOKEN
login_customer_id: YOUR_MCC_ID
use_proto_plus: true
youtube_api_key: YOUR_YOUTUBE_API_KEY  # only for channel extractor
```

If you don't have Google Ads API access yet, see the [Google Ads API Setup](../google-ads-api-setup/) skill in this repo.

### 3. Create a Google Sheet

Create a blank sheet and copy its ID from the URL. Make sure your OAuth account has edit access.

### 4. Run it

```bash
# Test with a few accounts
python scripts/youtube_placement_audit.py --mcc 1234567890 --sheet YOUR_SHEET_ID --test --limit 3

# Full audit
python scripts/youtube_placement_audit.py --mcc 1234567890 --sheet YOUR_SHEET_ID --force

# Extract channels for bulk negation
python scripts/youtube_channel_extractor.py --sheet YOUR_SHEET_ID --creds google-ads.yaml --force
```

### 5. Negate in Google Ads

Open your sheet, review the "Channels to Negate" tabs, add channel URLs as placement exclusions.

---

## Customization

Edit `FLAGGED_KEYWORDS` at the top of the audit script to add your own industry-specific terms. Keywords are matched case-insensitively against placement names.

---

## Detailed Documentation

See [SKILL.md](SKILL.md) for complete setup instructions, output format details, PMAX API limitations, and runtime estimates.

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
