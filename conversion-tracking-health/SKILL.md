---
name: "Conversion Tracking Health"
description: "Audits conversion tracking health across Google Ads portfolios. Auto-invoke when user says 'conversion tracking audit', 'check conversion health', or 'audit conversions for [portfolio]'. Only analyzes accounts with spend in last 7 days. Identifies conversion actions that haven't fired or are stale."
allowed-tools: [Bash, Read]
---

# Conversion Tracking Health Audit Skill

**Trigger Phrases:**
- "conversion tracking audit for portfolio_2"
- "check conversion health for portfolio_1"
- "audit conversions for portfolio_3"
- "run conversion audit"
- "conversion tracking health"

## Purpose

Identifies conversion tracking issues across Google Ads portfolios by analyzing which conversion actions haven't fired recently or are stale. **Only audits accounts with spend in the last 7 days** to focus on actively running campaigns.

## Key Features

### 1. Spend Filter (Critical)
- **Only audits accounts with spend in last 7 days**
- Skips inactive/paused accounts automatically
- Rationale: Conversion tracking only matters for actively spending accounts
- Reduces noise from ~63 accounts (Google Sheet approach) to ~160 active accounts

### 2. Conversion Action Filtering
**Tracks Only:**
- Primary conversions (`include_in_conversions_metric = True`)
- Website conversions only

**Ignores:**
- Store visits (`STORE_VISITS`)
- Google-hosted actions (`GOOGLE_HOSTED` - local actions, clicks to call)
- Mobile app conversions (Android/iOS installs, in-app actions)
- Firebase events
- Observation-only conversions (not used in optimization)

### 3. Activity Categorization
- **Healthy:** ≤14 days (not shown in output)
- **Warning:** 15-30 days since last conversion
- **Stale:** 30+ days since last conversion
- **No Data:** 90+ days or never fired

### 4. Severity-Based Output
Results grouped worst-first:
1. ❌ **No Recent Data** (90+ days / never fired)
2. 🚨 **Stale** (30+ days)
3. ⚠️ **Warning** (15-30 days)

## Execution Workflow

### Step 1: Identify Accounts to Audit

Either:
- A list of customer IDs (`--cids 1234567890,2345678901`)
- A single CID (`--cid 1234567890`)
- A CSV file with `cid,name` rows (`--accounts-file portfolio.csv`) — useful
  for named portfolios

### Step 2: Run the Audit

Use the Bash tool to execute:

```bash
# Single account
python scripts/portfolio_conversion_audit.py --cid 1234567890

# Multiple accounts
python scripts/portfolio_conversion_audit.py --cids 1234567890,2345678901

# Portfolio from CSV (cid,name per row, no header)
python scripts/portfolio_conversion_audit.py --accounts-file portfolio.csv
```

**Expected Runtime:** ~1-2 seconds per account.

### Step 3: Present Results

The script outputs:

```
====================================================================================================
PORTFOLIO CONVERSION AUDIT - PORTFOLIO_2
====================================================================================================
Accounts to audit: 162
Lookback period: 90 days
Analysis date: 2025-11-04 16:36:20
====================================================================================================

Auditing accounts...

  ✓ Example Account Name 1
  ✓ Example Account Name 2
  ⊘ Example Paused Account (no spend in last 7 days)
  ...

Audit complete. Checked 160 accounts, skipped 2 (no spend).

====================================================================================================
RESULTS - PROBLEMATIC CONVERSIONS ONLY
====================================================================================================

❌ NO RECENT CONVERSIONS (90+ days) - 107 issues found

Account Name                        | Conversion Action              | Last Activity
----------------------------------- | ------------------------------ | ---------------
Example Account Name                 | Form_Contact-Submit_BC         | Never fired
Example Another Account              | Phone Call                     | Never fired
...

🚨 STALE (30+ days) - 26 issues found

Account Name                        | Conversion Action              | Last Activity
----------------------------------- | ------------------------------ | ---------------
Example Account Name                 | Contact                        | 84 days ago
...

⚠️  WARNING (15-30 days) - 40 issues found

Account Name                        | Conversion Action              | Last Activity
----------------------------------- | ------------------------------ | ---------------
Example Account Name                 | Form_Contact-Submit_BC         | 26 days ago
...

====================================================================================================
SUMMARY
====================================================================================================

Total accounts checked: 160
Accounts skipped (no spend in 7 days): 2
Total problematic conversions: 173
  ❌ No recent data: 107
  🚨 Stale (30+ days): 26
  ⚠️  Warning (15-30 days): 40

====================================================================================================
```

### Step 4: Interpret Results

**Key Metrics:**
- **Accounts checked** - Active accounts with spend in last 7 days
- **Accounts skipped** - Inactive accounts (no spend)
- **Total problematic conversions** - Individual conversion actions with issues (not unique accounts)

**Understanding the Numbers:**
- One account can have multiple problematic conversion actions
- Example: Portfolio 2 shows 173 problematic conversions across many accounts
- This means many accounts have 1-2 conversion actions with issues

## Complementary to Google Ads Script

**User's Existing Google Ads Script:**
- Runs daily in Google Ads environment
- Outputs to "Zero Conversions" tab in Google Sheets
- Shows ~63 accounts with conversion tracking problems
- No spend filter (includes all accounts)

**This Python Skill:**
- Runs on-demand from PPC Brain
- Filters by spend (only active accounts)
- Shows 173 problematic conversion actions across 160 accounts
- More granular - counts individual conversion actions, not just accounts

**How They Complement:**
- Google Sheet: Broad overview of all accounts (including inactive)
- Python Audit: Focused view of active accounts only
- Use both: Sheet for comprehensive tracking, Python for actionable insights

## Advanced Usage

### Custom Lookback Period

```bash
python scripts/portfolio_conversion_audit.py --accounts-file portfolio.csv --days 180
```

### Include Accounts With No Recent Spend

By default, accounts with no spend in the last 7 days are skipped. To audit
everything regardless of spend:

```bash
python scripts/portfolio_conversion_audit.py --accounts-file portfolio.csv --include-no-spend
```

### Single Account Deep-Dive

For detailed analysis of a single account:

```bash
python scripts/last_conversion_dates_by_action.py --cid 1234567890 --days 90
```

This shows ALL conversion actions (including healthy ones) with full details.

## Use Cases

### 1. Daily Portfolio Health Check
**Scenario:** Daily portfolio health check includes conversion tracking review
**Action:** Run skill for Portfolio 2, focus on "No Data" section for immediate action

### 2. Client Reporting
**Scenario:** Client asks "Are our conversions tracking properly?"
**Action:** Run audit, export results, summarize findings in client-facing report

### 3. New Campaign Launch
**Scenario:** Launched new campaigns 2 weeks ago, need to verify tracking
**Action:** Run audit, check if new conversion actions are firing

### 4. Troubleshooting Low Conversions
**Scenario:** Account has low conversion volume, investigating why
**Action:** Run single-account deep-dive to see all conversion actions and their health

## Error Handling

**No Active Accounts:**
- If all accounts have no spend, summary shows 0 accounts checked
- Output: "Accounts skipped (no spend in 7 days): 162"

**API Access Errors:**
- If account query fails, error message shown but script continues
- Error format: `Error querying conversion actions: [ERROR_MESSAGE]`

**No Conversion Issues:**
- If all conversions are healthy (≤14 days)
- Output: "🎉 NO ISSUES FOUND! All conversion actions are healthy."

## Technical Details

### GAQL Queries Used

**1. Check Account Spend:**
```sql
SELECT metrics.cost_micros
FROM customer
WHERE segments.date BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'
```

**2. Get Conversion Actions:**
```sql
SELECT
    conversion_action.id,
    conversion_action.name,
    conversion_action.type,
    conversion_action.status,
    conversion_action.category,
    conversion_action.include_in_conversions_metric
FROM conversion_action
WHERE conversion_action.status != 'REMOVED'
ORDER BY conversion_action.name
```

**3. Get Conversion Performance:**
```sql
SELECT
    segments.conversion_action_name,
    segments.date,
    metrics.conversions
FROM campaign
WHERE segments.date BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'
  AND metrics.conversions > 0
ORDER BY segments.date DESC
```

### Account Loading

The script accepts accounts via three flags (combinable):
- `--cid 1234567890`        - single CID
- `--cids 123,456,789`      - comma-separated CIDs
- `--accounts-file foo.csv` - CSV file with `cid,name` per row (no header)

## Output Files

Audit runs are saved to your project's output folder (e.g., `./data/audits/` or wherever you configure).

**Note:** Output files are not automatically cleaned up. Delete old files manually if needed.

## Integration with Other Skills

**Related Skills:**
- [`portfolio-health-prioritization`](../portfolio-health-prioritization/) - Determines which accounts need investigation
- Your daily triage workflow — for catching all portfolio issues (external)
- [`client-communication-standards`](../client-communication-standards/) - Format findings for client reports

**Workflow Example:**
1. Run `conversion-tracking-health` for Portfolio 2
2. Identify accounts with "No Data" issues
3. Use `portfolio-health-prioritization` to determine which to fix first
4. Create client summary using `client-communication-standards` format

## Maintenance

**Update Frequency:** On-demand (run when needed, no scheduled execution)

**Potential Enhancements:**
- CSV export option
- Email/Slack alerts for critical issues
- Trend analysis (track changes over time)
- Integration with Run Rate Issues Analysis sheet
- Automated fix suggestions

**Dependencies:**
- `google-ads.yaml` at project root - Google Ads API credentials (override with `--config`)
- Python environment with `google-ads` library installed

## Version History

**v1.0** (2025-11-04)
- Initial skill creation
- Portfolio-wide audit with spend filter (7 days)
- Filters out store/mobile/Google-hosted conversions
- Only tracks primary conversions (used in optimization)
- Severity-based output (No Data → Stale → Warning)
- Summary shows accounts checked vs. skipped
- Complements existing Google Ads Script approach

---

**Script Location:** `scripts/portfolio_conversion_audit.py` (provide your own — see Phase 3 inlining notes)
**Trigger:** Say "conversion tracking audit for [portfolio]" or "check conversion health"
