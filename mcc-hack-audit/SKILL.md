---
name: "MCC Hack Audit"
description: "Portfolio-wide scan of every manager (MCC) that has access to accounts in your Google Ads tree. Built after an MCC link-fraud incident where hostile external MCCs were found linked to client accounts via compromised admin credentials. Classifies each manager link as INTERNAL (in your tree), HOSTILE (known threat), or EXTERNAL (potential exposure — no judgment). Outputs CSV by default with optional Google Sheets upload. Auto-invoke when user says 'mcc hack audit', 'audit mcc links', 'scan for external managers', 'check manager links', 'run mcc link scan', 'find external mccs', or asks who has access to their Google Ads accounts."
allowed-tools: [Bash, Read]
---

# MCC Hack Audit

**Trigger Phrases:** "mcc hack audit", "audit mcc links", "scan for external managers", "check manager links", "find external mccs", "who has access to my accounts"

## Purpose

Identify every manager account (MCC) that has a link into your Google Ads tree. Built after a real-world MCC link-fraud incident where hostile external MCCs gained access to client accounts via compromised client-side admin credentials.

This skill answers: **"Which MCCs currently have access to which of my accounts, and which are outside my own tree?"**

It does NOT remove links, send notifications, or judge legitimacy. Identification is the goal. Action is yours.

## What It Scans

**Included:**
- Every account under your `login_customer_id` (walks `customer_client`)
- Every active manager-link relationship on each account (`customer_manager_link`)
- All account statuses (ENABLED, CANCELED, SUSPENDED, CLOSED) — security-relevant data lives in canceled accounts too

**Output:**
- Every (account, manager) pair
- Suspicious-only subset (HOSTILE + EXTERNAL)

## Classification Model — No Judgment

Three classifications, defined by objective ownership only:

| Class | Definition |
|---|---|
| `INTERNAL` | manager_cid is inside your own MCC tree (auto-detected by walking `customer_client`) |
| `HOSTILE` | manager_cid matches an entry in your hostile-MCC list (you populate this) |
| `EXTERNAL` | Anything else. Potential exposure point regardless of name/age/footprint. **Never** auto-classified as legitimate. |

**Critical:** There is no "allowlist" or "trusted partner" concept by design. Every non-internal manager is EXTERNAL — even an agency you've worked with for 10 years, even an MCC that's been linked since the account was created. The point is identification, not pre-clearance. You judge.

If you'd rather not see long-standing trusted MCCs in the suspicious list, the script supports an explicit `--trusted-cids` flag (covered below), but be aware: every trusted entry is a place a determined attacker could target.

## Prerequisites

- Google Ads API credentials YAML with MCC access (`google-ads.yaml`)
- Your `login_customer_id` set in the YAML — the script auto-detects your tree from this
- Python packages: `google-ads`, `pyyaml`
- Optional: `gspread` if you want Sheets upload

## How to Run

```bash
# Default: walks your full tree, writes CSVs to output/
python scripts/mcc_hack_audit.py

# Custom output directory
python scripts/mcc_hack_audit.py --output-dir my-audit-output

# Include Google Sheets upload (requires gspread auth)
python scripts/mcc_hack_audit.py --sheet-id YOUR_SHEET_ID

# Add known-hostile CIDs from a JSON file
python scripts/mcc_hack_audit.py --hostile-list hostile.json

# Mark specific external CIDs as trusted (they'll be classified TRUSTED instead of EXTERNAL)
python scripts/mcc_hack_audit.py --trusted-cids "1234567890,0987654321"

# Tune parallelism (default 20, lower if you hit RESOURCE_EXHAUSTED)
python scripts/mcc_hack_audit.py --workers 10

# Custom credentials path
python scripts/mcc_hack_audit.py --config /path/to/google-ads.yaml
```

**Runtime:** ~2-5 min for a 1,000-account tree at 20 workers. Plan ~10 min for a 10,000-account tree.

**Hostile list format (`hostile.json`):**
```json
{
  "1234567890": "label or context for this hostile MCC",
  "0987654321": "another known-bad CID with a one-line note"
}
```

Start empty. Populate as incidents occur. See "Contributing Hostile-MCC Intelligence" below if you want to share back to the community.

## Output

### CSV Files (always written)

`output/mcc_link_scan_YYYYMMDD.csv` — every (account, manager) pair:

| Column | Description |
|---|---|
| `account_cid` | The account being scanned |
| `account_name` | Account display name |
| `account_status` | ENABLED / CANCELED / SUSPENDED / CLOSED |
| `manager_cid` | The manager MCC with access |
| `manager_link_id` | Google's link ID (higher = more recent) |
| `link_status` | ACTIVE / PENDING / REFUSED / CANCELED |
| `classification` | INTERNAL / HOSTILE / EXTERNAL / TRUSTED |
| `label` | Hostile context (if known) or empty |

`output/mcc_link_scan_YYYYMMDD_SUSPICIOUS.csv` — HOSTILE + EXTERNAL rows only, HOSTILE first, then EXTERNAL sorted by link_id descending (newest first).

### Google Sheet (optional, if `--sheet-id` provided)

Creates/overwrites these tabs:
- `All Manager Links` — every (account, manager) pair
- `Suspicious Links` — HOSTILE + EXTERNAL
- `Managers and Their Accounts` — pivoted: one row per distinct manager, with their account count
- `Internal Managers` — your detected internal MCCs

## Encoded Knowledge (do not regress)

Hard-won lessons from running this against a 10,000-account real-world tree:

1. **The Google Ads API does NOT expose `customer.descriptive_name` for external MCCs.** Direct lookup on a non-internal CID returns permission denied. The Google Ads UI has elevated visibility you don't get via API. To put human-readable names on suspicious CIDs, use the UI's Account Access page.

2. **`customer_manager_link.start_time` is documented but NOT supported.** The API rejects it with `UNRECOGNIZED_FIELD`. Use `manager_link_id` as a rough chronological proxy — IDs increase monotonically, so a higher link_id means a more recent link.

3. **`change_event` does NOT track manager-link acceptance events.** Even when an attacker accepts a hostile MCC invite, `change_event` shows no entry for the link itself. You'll see post-link mutation activity (campaigns, ads, etc.) but not the link acceptance. To trace "who clicked accept," use the UI's Change History or Google Support.

4. **CANCELED/CLOSED accounts still hold manager-link history.** Don't filter them out — they often hold the most security-relevant data (an account that was just canceled because of fraud, for instance). API errors on these are fast and expected.

5. **20 parallel workers is the sweet spot.** Higher rates risk `RESOURCE_EXHAUSTED` throttling. Use `--workers 10` if you see throttling.

6. **No allowlist by design.** If you mark a long-standing partner as TRUSTED via `--trusted-cids`, you've reduced their visibility — not their attack surface. Re-audit on a cadence regardless.

## Contributing Hostile-MCC Intelligence

If you discover a hostile MCC during incident response, consider opening an issue or PR with the CID and a one-line context note. Community threat-intel benefits everyone, but only contribute when:

- You've confirmed the MCC was hostile (mutations made, link rejected, client confirmed compromise)
- The CID is no longer your active threat (publishing tips off attackers who are still active in your tree)
- You're comfortable with the CID being public

There is no central registry shipped with this skill. Maintain your own `hostile.json` and share excerpts when appropriate.

## Sister Skill (planned)

A companion skill — tracking **who's making changes** by actor email (using `change_event`) — is in the works. This skill answers "who has access." The companion answers "who's making changes." Together they give you both the access map and the activity log.

## Limitations

- **No watchdog mode.** This skill is manual. For automated daily-diff detection of new external manager links, you'd need to schedule the run and diff CSVs across days.
- **No name visibility for external CIDs.** Manual UI lookup is the only path to put a name to a CID.
- **No outreach.** This skill identifies; it does NOT email clients, post to Slack, or notify anyone. All communication is your call.
- **Single MCC.** The script reads `login_customer_id` from your YAML. If you operate across multiple parent MCCs, run it once per parent.

## Related Skills

- `mutation-safety` — gates any change you make in response to findings
- `change-history-checker` — pull cross-account change events to follow up on suspicious manager activity
- `gaql-query-patterns` — reference for related queries
