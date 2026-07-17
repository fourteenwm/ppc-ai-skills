---
name: non-serving-keyword-scanner
description: "Scans your agency accounts for keywords with 0 impressions in last 180 days. Auto-invoke when user says 'scan non-serving keywords', 'find dead keywords', 'keyword cleanup report', or 'non-serving keyword scan'. Outputs to Google Sheet for human review."
allowed-tools: [Bash, Read]
---

# Non-Serving Keyword Scanner

**Trigger Phrases:** "scan non-serving keywords", "find dead keywords", "keyword cleanup report"

## Purpose

Identifies keywords across all your accounts that have received **zero impressions in the last 180 days**. These "dead" keywords clutter accounts and should be reviewed for pausing.

**Approach:** Human-in-the-Loop - Generates report only, no auto-pausing.

## Prerequisites

- **Credentials:** `google-ads.yaml` at project root — see the [google-ads-api-setup](../google-ads-api-setup/) skill if you don't have one. The sheet-writing step reuses this same file's OAuth credentials for the Sheets API — its refresh token must carry the `spreadsheets` + `drive.readonly` scopes, which the setup skill's generator grants by default (token predates that? re-run the generator once)
- **Output sheet:** any Google Sheet you own — you pass its ID via `--sheet-id`
- **Python packages:** `pip install google-ads gspread google-auth pyyaml`

## What It Scans

**Included:**
- All accounts in your portfolio
- Search campaigns only
- Enabled campaigns, ad groups, and keywords only

**Excluded:**
- Paused campaigns, ad groups, or keywords
- Ad groups named "special" or "specials" (dynamic pricing ad groups)
- Non-Search campaign types (Pmax, Display, etc.)

## Output

**Google Sheet:** any spreadsheet you own — pass its ID with `--sheet-id`
**Tab:** "Non-Serving Keywords" (created if missing, cleared and rewritten each run; override with `--tab-name`)

**Columns:**
| Column | Description |
|--------|-------------|
| Account Name | Google Ads account name |
| CID | Customer ID |
| Campaign | Campaign name |
| Ad Group | Ad group name |
| Keyword | Keyword text |
| Match Type | EXACT, PHRASE, or BROAD |
| Impressions | 0 (confirmed non-serving) |
| Clicks | Should be 0 |
| Conversions | Should be 0 |
| Cost | Should be $0 |

## How to Run

```bash
# Scan a single account — fastest first run
python scripts/non_serving_keyword_scan.py --cid 1234567890 --sheet-id YOUR_SHEET_ID

# Scan multiple accounts
python scripts/non_serving_keyword_scan.py --cids "1234567890,2345678901" --sheet-id YOUR_SHEET_ID

# Scan all enabled accounts under your MCC (walks customer_client)
python scripts/non_serving_keyword_scan.py --all --sheet-id YOUR_SHEET_ID

# Scan a curated account list (copy accounts.example.md to accounts.md and edit)
python scripts/non_serving_keyword_scan.py --accounts accounts.md --sheet-id YOUR_SHEET_ID

# Custom threshold (e.g., 90 days instead of default 180)
python scripts/non_serving_keyword_scan.py --cid 1234567890 --sheet-id YOUR_SHEET_ID --days 90

# Custom tab name
python scripts/non_serving_keyword_scan.py --cid 1234567890 --sheet-id YOUR_SHEET_ID --tab-name "Dead Keywords 90d"
```

**Required CLI args:** `--sheet-id` (Google Sheet ID for output)

**Account selection — three modes (mutually exclusive; with no account flag the script defaults to `--accounts accounts.md`):**
- `--cid CID` — single account (fastest first run)
- `--cids CID1,CID2,...` — multiple accounts
- `--all` — every enabled account under your MCC's `login_customer_id`
- `--accounts PATH` — curated markdown list (default: `./accounts.md`); a starter file ships with this skill as `accounts.example.md` — copy it and edit

Running without a usable account source (e.g., the default mode with no `accounts.md` present) prints this mode list instead of a traceback.

**Accounts file format** (see the shipped `accounts.example.md`) — one `### CID:` header per account, then one or more `- Name` lines; the FIRST name is the display name, extra lines are optional aliases:

```markdown
### CID: 123-456-7890
- Example Client A

### CID: 234-567-8901
- Example Client B
- Example Client B (alias)
```

**Optional flags:**
- `--days N` — zero-impression threshold (default: 180)
- `--tab-name NAME` — sheet tab name (default: "Non-Serving Keywords")
- `--config PATH` — google-ads.yaml location (default: `./google-ads.yaml`)

**Runtime:** ~3-5 seconds per account. Plan ~3-5 minutes for a ~50-account MCC.

**Progress Output:**
```
[1/N] Scanning Portfolio 1 - Example Account A... 0 non-serving keywords
[2/N] Scanning Portfolio 1 - Example Account B... 3 non-serving keywords
...
[N/N] Scanning Portfolio 2 - Example Account Z... 1 non-serving keywords

================================================================================
SCAN COMPLETE
================================================================================
Total accounts scanned: N
Accounts with non-serving keywords: 23
Total non-serving keywords found: 156

Results written to:
https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
```

## After Running

1. Open the Google Sheet
2. Review the "Non-Serving Keywords" tab
3. For each keyword, decide:
   - **Pause:** Keyword is truly dead, no longer relevant
   - **Keep:** Keyword may serve in future (seasonal, niche)
   - **Investigate:** Check if there's a broader issue (bid too low, negative conflict)
4. Pause keywords manually in Google Ads UI

## Filters Applied

**GAQL Query Filters:**
- `ad_group_criterion.type = 'KEYWORD'`
- `ad_group_criterion.status = 'ENABLED'`
- `ad_group.status = 'ENABLED'`
- `campaign.status = 'ENABLED'`
- `campaign.advertising_channel_type = 'SEARCH'`
- `metrics.impressions = 0` (over LAST_180_DAYS)

**Python Post-Filters:**
- Exclude ad groups where name.lower() in ['special', 'specials']

## Troubleshooting

**"Accounts file not found" / "No accounts parsed"**
- Pick an account source: `--cid`, `--cids`, `--all`, or `--accounts` (copy `accounts.example.md` to `accounts.md` and edit)

**"No keywords found"**
- Check if Search campaigns exist and are enabled
- Verify date range is correct (180 days)

**"API Error for account X"**
- Script continues with other accounts
- Check if account is accessible under MCC

**403 / "insufficient authentication scopes" writing the sheet**
- Your `google-ads.yaml` refresh token predates the Sheets scopes — re-run the `google-ads-api-setup` generator once and paste the new refresh_token

**"Sheet not updating"**
- Verify gspread authentication is current
- Check Sheet ID is correct

## Related Skills

- `conversion-tracking-health` - Similar portfolio-wide audit pattern
- `gaql-query-patterns` - GAQL templates

## Future Enhancements

- Add `--portfolio` flag to scan a specific portfolio only
- Add "Pause Selected" mode gated by the `mutation-safety` approval flow
