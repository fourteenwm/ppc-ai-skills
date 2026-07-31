---
name: youtube-placement-audit
description: Audit Google Ads accounts for bad YouTube placements (kids content, adult, gaming, non-English, spam) across PMAX, Demand Gen, and Display campaigns. Flags violations, writes to Google Sheets, then extracts channels for bulk negation.
---

# YouTube Placement Brand Safety Audit

Scans all accounts under your MCC for YouTube placements and flags brand
safety violations, then aggregates flagged videos by channel so you can
negate at the channel level instead of one video at a time. The flags are
machine leads; the negate/keep calls live in [rules.md](rules.md), and
exact script mechanics live in
[`references/audit-contract.md`](references/audit-contract.md).

---

## Why This Exists

PMAX and Demand Gen campaigns serve ads on YouTube placements you never
chose. Without active auditing, your ads show on kids' channels,
foreign-language content, spam videos, and worse. Google doesn't give you
a "block all kids content" button, so you need to find and exclude these
placements yourself.

The manual way: Export placements, eyeball thousands of rows, copy URLs,
add exclusions one by one.

This skill: Scan all accounts, flag violations automatically, aggregate by
channel, get a clean negate list.

---

## What this skill deliberately does NOT do

- **Never touches Google Ads state.** Both scripts read the API and write
  a sheet; placement exclusions are applied by you in the UI or Editor.
- **Doesn't judge placements.** A flag means a pattern matched
  (substring, case-insensitive — Toyota trips `toy`). The negate/keep
  call is rules.md's category table, not the flag itself.
- **Doesn't see foreign languages in Latin script.** The non-English
  check reads Unicode *scripts* — Spanish/French/German content never
  flags (contract). Extend `FLAGGED_KEYWORDS` if that matters for your
  market.
- **Doesn't route flagged channels through the extractor.** Channel-type
  placements are already channels — the extractor only processes video
  rows, so pull `YOUTUBE_CHANNEL` rows from the Bad tabs directly when
  building the exclusion list.
- **Audits ENABLED accounts only** — paused/canceled accounts under the
  MCC are never scanned.

---

## What Gets Flagged

**27 keywords across 6 reason labels** (full table + matching semantics:
[contract](references/audit-contract.md)):

- **Kids content** (15 keywords — toy, cartoon, roblox, minecraft, peppa
  pig…) → the biggest category and the biggest false-positive surface
- **Adult content** (4) · **Gaming content** (3) · **Spam** and
  **Spam/Clickbait** (3) · **Legal** (2 — dui, bail bonds)
- **Null/Empty placements** — blank/unnamed placements (low-quality
  inventory), written to the keyword tab
- **Non-English content** → the `Bad - YouTube - NEA` tab: 24 non-Latin
  Unicode scripts (Cyrillic, Arabic, Hebrew, CJK, Devanagari, Thai…) —
  detection is per-character and script-based, and it runs only when no
  keyword matched

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

Google Sheets access reuses the same OAuth credentials. Your GCP project
needs the Sheets scope enabled, and the OAuth account needs edit access
to the output sheet.

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

A zero-flag run writes nothing (existing tab rows persist — check `Run
Date`), and a failed per-account query is silent: an account printing `No
YouTube placements` against sibling accounts full of them is the
false-clean tell ([rules.md](rules.md) § triage).

### Step 2: Extract channels (recommended)

```bash
# Both keyword + NEA channels
python scripts/youtube_channel_extractor.py --sheet SHEET_ID --creds google-ads.yaml --force

# Only non-English channels
python scripts/youtube_channel_extractor.py --sheet SHEET_ID --creds google-ads.yaml --nea-only --force
```

### Step 3: Review, then negate in Google Ads

1. Open your Google Sheet
2. Read the flags through [rules.md](rules.md)'s category table — the
   substring traps live there
3. Build the exclusion list: "Channels to Negate" tabs **plus the
   `YOUTUBE_CHANNEL` rows from the Bad tabs** (those bypass the
   extractor)
4. Add channel URLs as placement exclusions:
   - **PMAX:** Campaign-level placement exclusions
   - **Demand Gen / Display:** Ad group or campaign exclusions

---

## Output

| Sheet Tab | Content |
|-----------|---------|
| Bad - YouTube | Keyword-flagged placements (incl. Null/Empty) |
| Bad - YouTube - NEA | Non-English Alphabet placements |
| Channels to Negate | Aggregated channels from keyword flags |
| Channels to Negate - NEA | Aggregated channels from NEA flags |

All four tabs carry a `Run Date` column — check it per tab before acting
(a tab with no rows this run keeps last run's data; contract).

---

## PMAX API Limitation

The `performance_max_placement_view` resource only returns
**impressions**. Clicks, cost, and conversions show as 0 for PMAX
campaigns. Full metrics are available for Display and Demand Gen. Triage
PMAX rows on impressions — zeros there are the API, not evidence.

---

## The Channel Aggregation Payoff

Flagging individual videos is step one. The channel extractor is where the real leverage is:

- 24,000 flagged videos -> ~9,000 channels (62% reduction)
- Each channel exclusion blocks ALL future videos from that channel
- One monthly run keeps your placements clean

---

## Customization

Edit `FLAGGED_KEYWORDS` at the top of `youtube_placement_audit.py` to add
industry-specific terms. For example, a B2B SaaS company might add:

```python
'free download': 'Spam',
'crack': 'Piracy',
'tutorial for kids': 'Kids content',
```

Custom terms inherit substring matching — `crack` also hits
"firecracker". [rules.md](rules.md) § customization judgment has the
isolation tricks; test list changes with `--test` first.

---

## Runtime

| Accounts | Audit | Channel Extraction |
|----------|-------|-------------------|
| 10 | ~2 min | ~30 sec |
| 50 | ~8 min | ~1 min |
| 100 | ~15 min | ~2 min |
| 300+ | ~25-30 min | ~4-5 min |

Run monthly.

---

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | This file — workflow + routing |
| `rules.md` | Judgment layer: category calls, substring traps, when NOT to negate, triage order, cadence |
| `examples.md` | Three worked reads incl. the false-clean account and the Toyota trap |
| `references/audit-contract.md` | Line-derived mechanics of both scripts: taxonomy, matching, silent-swallow, tab semantics |
| `scripts/youtube_placement_audit.py` | Step 1 — scan accounts, flag, write the Bad tabs |
| `scripts/youtube_channel_extractor.py` | Step 2 — aggregate flagged videos into channels |
| `README.md` | User-facing overview + install |

---

## After a Run

The Google Sheet is the only durable record — console output isn't
persisted. Each tab's `Run Date` column says when it was last actually
written (audit tabs: date; channel tabs: date+time). Account state never
changes from running either script; if a cold session needs to know
whether exclusions were *applied*, that evidence lives in Google Ads
change history, not here.

---

## When to Load What

| Moment | Load |
|---|---|
| Reading flag output — negate/keep calls, traps, triage | [rules.md](rules.md) |
| Exact matching/tab/query mechanics, the silent-swallow and stale-tab traps | [references/audit-contract.md](references/audit-contract.md) |
| First read, or a portfolio that looks suspiciously clean | [examples.md](examples.md) |
| An account reads empty and you need to separate no-data from no-access | [google-ads-query](../google-ads-query/) — its errors surface loudly |
| This check as one slice of a full account sweep | [account-diagnostic](../account-diagnostic/) — its placement-safety checks (37-38) route here for the full portfolio sweep |
| No API credentials yet | [google-ads-api-setup](../google-ads-api-setup/) |
| Scripting the exclusions themselves (mutation) | [mutation-safety](../mutation-safety/) — preview, approve, execute, verify |
