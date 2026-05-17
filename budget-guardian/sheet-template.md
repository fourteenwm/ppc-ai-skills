# Sheet Template

The Guardian uses a single Google Sheet with three tabs.

## Tab 1: `Budgets` (you create + maintain this)

| Column | Header | Type | Notes |
|--------|--------|------|-------|
| A | Account Name | string | Displayed in Slack alerts |
| B | CID | string (digits only) | Google Ads customer ID, no dashes |
| C | Monthly Budget | number | Dollar amount, no currency symbol, no commas |

Example:

| Account Name | CID | Monthly Budget |
|--------------|-----|----------------|
| Acme Auto Repair | 1234567890 | 3000 |
| Bright Smiles Dental | 9876543210 | 2500 |
| Coastal HVAC | 5555555555 | 5000 |

**Rules:**

- One row per account. If you have a multi-CID account, sum the budgets and use one of the CIDs (or add multiple rows — each will be tracked separately).
- The first row is the header row. The Guardian reads from row 2 onwards (up to row 200 by default).
- Empty rows are skipped. Rows where Monthly Budget is 0 or blank are skipped.
- Account Name is purely a label — change it any time without affecting behavior. CID and Monthly Budget are what drive the logic.

You can override the tab name by setting the `GUARDIAN_BUDGET_TAB` environment variable.

## Tab 2: `Guardian Config` (auto-created by `setup_tabs.py`)

| Cell | Purpose |
|------|---------|
| A1 | Header: "Kill Switch" |
| A2 | Value: `ENABLED` or `DISABLED` |

Set A2 to `DISABLED` to silence the Guardian without touching GitHub. The next 2-hour run will exit immediately when it sees `DISABLED`.

## Tab 3: `Guardian State` (auto-created by `setup_tabs.py`, auto-maintained by the workflow)

| Column | Header | Purpose |
|--------|--------|---------|
| A | Month | `YYYY-MM` format — the month this alert fired |
| B | CID | The account's CID |
| C | Account Name | Label from the Budgets tab at time of alert |
| D | Threshold | `100%` or `120%` |
| E | Action | `warned` or `alerted` |
| F | Timestamp | When the alert was sent (UTC) |

**Do not edit this tab manually unless you want to reset alerts.**

To force a re-alert for an account this month, delete its row(s) from this tab. The next run will see no prior alert and fire a fresh one.

The Guardian clears stale rows (previous months) automatically at the start of each run, so this tab stays small.
