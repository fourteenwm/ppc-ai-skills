# Sheet Template

The Shared Budget Updater uses a single Google Sheet tab. Default name:
`Shared Budget Uploader` (override with the `SHEET_TAB` repository variable).

## The tab (you create + maintain this)

| Column | Header | Type | Notes |
|--------|--------|------|-------|
| A | Customer ID | string | Google Ads customer ID — dashes ok (`123-456-7890` works) |
| B | Shared Budget ID | string (digits) | The shared budget's ID under that customer |
| C | New Budget Amount | number | Dollars — `$` and `,` ok (`$1,234.56` works) |
| D | Done | workflow-owned | `x` = processed; empty = pending. **Never fill this by hand** |

Example:

| Customer ID | Shared Budget ID | New Budget Amount | Done |
|-------------|------------------|-------------------|------|
| 1234567890 | 11111111 | 1500 | x |
| 1234567891 | 22222222 | $2,750.00 | |

## Semantics

- **A row with A+B+C filled and D empty is an approved, pending change.** The
  next scheduled run pushes it to Google Ads and writes `x` in column D.
- **Column D is workflow-owned.** Only the workflow writes it. Hand-marking a
  row `x` silently cancels an approved change; hand-clearing an `x`
  re-pushes that row on the next run (useful, but do it deliberately).
- Failed rows keep an empty column D and retry automatically on the next run.
- Amounts of $0 or less are skipped with an alert and never sent to the API.
- The first row is the header row — the workflow reads from row 2 onward.
- Finding the Shared Budget ID: in Google Ads, **Tools → Shared library →
  Shared budgets** — the `budgetId` appears in the URL when you open one, or
  pull `campaign_budget.id` via the API/your reporting tool of choice.
