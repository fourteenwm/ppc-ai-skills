---
name: youtube-placement-audit
description: Audit Google Ads accounts for bad YouTube placements (kids content, adult, gaming, non-English, spam) across PMAX, Demand Gen, and Display campaigns. Flags violations, writes to Google Sheets, then extracts channels for bulk negation.
---

# YouTube Placement Brand Safety Audit

Scans all accounts under your MCC for YouTube placements and flags brand safety violations. Then aggregates flagged videos by channel so you can negate at the channel level instead of one video at a time.

---

## Why This Exists

PMAX and Demand Gen campaigns serve ads on YouTube placements you never chose. Without active auditing, your ads show on kids' channels, foreign-language content, spam videos, and worse. Google doesn't give you a "block all kids content" button, so you need to find and exclude these placements yourself.

The manual way: Export placements, eyeball thousands of rows, copy URLs, add exclusions one by one.

This skill: Scan all accounts, flag violations automatically, aggregate by channel, get a clean negate list.

---

## What Gets Flagged

### Keyword Flags (written to "Bad - YouTube" tab)
- **Kids content:** toy, child, pokemon, doll, cartoon, nursery, peppa pig, disney, muppets, roblox, minecraft, fortnite
- **Adult content:** xxx, sexy, onlyfans
- **Gaming:** gaming, ninja, twitch
- **Spam/Clickbait:** viral, prank, 1-800
- **Legal:** dui, bail bonds
- **Null placements:** Empty/unnamed placements (low-quality inventory)

### Non-English Content (written to "Bad - YouTube - NEA" tab)
Cyrillic, Arabic, Hebrew, CJK (Chinese/Japanese/Korean), Hindi, Thai, Greek, Armenian, Georgian, Bengali, Tamil, Telugu, and 10+ other non-Latin scripts.

---

## Setup

### Prerequisites
1. Google Ads API access (`google-ads.yaml` credential file)
2. YouTube Data API v3 key (for channel extractor only)
3. Python 3.10+

### Install
```bash
pip install google-ads gspread google-auth google-api-python-client pyyaml
```

### Credentials
Your `google-ads.yaml` needs:
```yaml
client_id: YOUR_CLIENT_ID
client_secret: YOUR_CLIENT_SECRET
refresh_token: YOUR_REFRESH_TOKEN
developer_token: YOUR_DEVELOPER_TOKEN
login_customer_id: YOUR_MCC_ID
use_proto_plus: true
youtube_api_key: YOUR_YOUTUBE_API_KEY  # only for channel extractor
```

Google Sheets access reuses the same OAuth credentials. Your GCP project needs the Sheets scope enabled.

---

## Usage

### Step 1: Run the placement audit

```bash
# Test with 3 accounts
python scripts/youtube_placement_audit.py --mcc 1234567890 --sheet SHEET_ID --test --limit 3

# Full audit
python scripts/youtube_placement_audit.py --mcc 1234567890 --sheet SHEET_ID --force

# Filter to specific accounts
python scripts/youtube_placement_audit.py --mcc 1234567890 --sheet SHEET_ID --filter "Acme" --force
```

### Step 2: Extract channels (recommended)

```bash
# Both keyword + NEA channels
python scripts/youtube_channel_extractor.py --sheet SHEET_ID --creds google-ads.yaml --force

# Only non-English channels
python scripts/youtube_channel_extractor.py --sheet SHEET_ID --creds google-ads.yaml --nea-only --force
```

### Step 3: Negate in Google Ads

1. Open your Google Sheet
2. Review channels in "Channels to Negate" tabs
3. Add channel URLs as placement exclusions:
   - **PMAX:** Campaign-level placement exclusions
   - **Demand Gen / Display:** Ad group or campaign exclusions

---

## Output

| Sheet Tab | Content |
|-----------|---------|
| Bad - YouTube | Keyword-flagged placements |
| Bad - YouTube - NEA | Non-English Alphabet placements |
| Channels to Negate | Aggregated channels from keyword flags |
| Channels to Negate - NEA | Aggregated channels from NEA flags |

---

## PMAX API Limitation

The `performance_max_placement_view` resource only returns **impressions**. Clicks, cost, and conversions show as 0 for PMAX campaigns. Full metrics are available for Display and Demand Gen.

---

## The Channel Aggregation Payoff

Flagging individual videos is step one. The channel extractor is where the real leverage is:

- 24,000 flagged videos -> ~9,000 channels (62% reduction)
- Each channel exclusion blocks ALL future videos from that channel
- One monthly run keeps your placements clean

---

## Customization

Edit `FLAGGED_KEYWORDS` at the top of `youtube_placement_audit.py` to add industry-specific terms. For example, a B2B SaaS company might add:

```python
'free download': 'Spam',
'crack': 'Piracy',
'tutorial for kids': 'Kids content',
```

---

## Runtime

| Accounts | Audit | Channel Extraction |
|----------|-------|-------------------|
| 10 | ~2 min | ~30 sec |
| 50 | ~8 min | ~1 min |
| 100 | ~15 min | ~2 min |
| 300+ | ~25-30 min | ~4-5 min |

Run monthly.
