# YouTube Placement Brand Safety Audit

Scan your Google Ads MCC for bad YouTube placements across PMAX, Demand Gen, and Display campaigns. Flag brand safety violations, write results to Google Sheets, then aggregate by channel for bulk negation.

**The pain point:** PMAX and Demand Gen serve your ads on YouTube placements you never chose. Without auditing, your ads end up on kids' channels, foreign-language content, adult videos, and spam. This skill finds those placements across your entire portfolio and gives you a clean list of channels to negate.

---

## What It Does

Two scripts that work together:

1. **`youtube_placement_audit.py`** — Scans all accounts under your MCC, pulls YouTube placements, flags violations (kids, adult, gaming, non-English, spam), writes to Google Sheets in two tabs.

2. **`youtube_channel_extractor.py`** — Reads flagged videos from your sheet, looks up which channel each video belongs to via YouTube Data API, aggregates by channel. This is where the real leverage is: 24,000 flagged videos collapse to ~9,000 channels, and each channel exclusion blocks ALL future videos.

Plus operator docs: `rules.md` (which flags to act on, the substring
traps, when NOT to negate), `examples.md` (three worked reads incl. the
account that reads clean but isn't), and
`references/audit-contract.md` (exact mechanics of both scripts,
line-cited).

---

## Installation

```bash
mkdir -p .claude/skills/youtube-placement-audit/scripts .claude/skills/youtube-placement-audit/references
for f in SKILL.md README.md rules.md examples.md; do
  curl -o .claude/skills/youtube-placement-audit/$f \
    https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/youtube-placement-audit/$f
done
curl -o .claude/skills/youtube-placement-audit/references/audit-contract.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/youtube-placement-audit/references/audit-contract.md
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

### 5. Review, then negate in Google Ads

Open your sheet and read the flags through `rules.md` first — matching is
substring-based (a Toyota channel trips `toy`), so the sheet is a review
surface, not a paste-ready list. Build the exclusion list from the
"Channels to Negate" tabs plus any `YOUTUBE_CHANNEL` rows in the Bad tabs
(those don't flow through the extractor), then add the channel URLs as
placement exclusions.

---

## Customization

Edit `FLAGGED_KEYWORDS` at the top of the audit script to add your own industry-specific terms. Keywords are matched case-insensitively against placement names.

---

## Detailed Documentation

See [SKILL.md](SKILL.md) for complete setup instructions, output format details, PMAX API limitations, and runtime estimates.

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
