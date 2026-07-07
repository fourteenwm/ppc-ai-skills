# Shared Budget Updater

A sheet-driven daily budget pusher for Google Ads shared budgets. Add an
approved change as a row (CID, shared budget ID, new amount); a GitHub Actions
cron pushes it to Google Ads and marks the row done.

> **⚠️ This tool CHANGES live Google Ads budgets.** There is no dry-run and no
> confirmation prompt — by design, the sheet is the approval surface. **Whoever
> can edit the sheet can change your spend.** Lock the sheet's sharing down to
> the people who are allowed to approve budget changes, and test on a
> non-production account first (Step 6).

## How it works

![Sequence diagram: a PPC manager enters budget changes in a sheet; the daily updater reads pending rows, validates each amount, updates only the budget amount via the Google Ads API, marks successes done, and sends one consolidated Slack alert for any failures — failed rows retry automatically on the next run](diagrams/workflow-hero.svg)

A GitHub Actions cron fires once a day. The job:

1. Reads the uploader tab for rows where columns A/B/C are filled and column D
   is empty (each such row is an approved, pending change)
2. Skips any row whose amount is $0 or less (alerted, never sent to the API)
3. Pushes each remaining row via `campaignBudgets:mutate` — the **amount is
   the only field it can touch** (`updateMask: amount_micros`)
4. Marks successful rows done (`x` in column D) in one batch write
5. Sends **one consolidated Slack alert** listing every failed row; failed
   rows keep an empty column D and retry automatically on the next run

The job exits 0 even when some rows fail — the Slack alert is the failure
signal, and the workflow-crash alert stays reserved for real crashes.

Every decision gate in one view:

![Flowchart of the run logic in three phases: the run starts (cron fires, read the budget tab, exit if nothing is pending), for each pending row (parse the amount, the over-zero guard, the single-field API update with retries, capture any error), and after the loop (batch-write done marks, one consolidated Slack alert, failed rows become tomorrow's retry queue)](diagrams/run-logic.svg)

The `.mmd` sources for both diagrams live in `diagrams/` — they're
[Mermaid](https://mermaid.js.org/) diagram-as-code, rendered with the included
`theme.json`.

## Prerequisites

1. **A Google Ads account or MCC** with API access (developer token + OAuth
   refresh token)
2. **A Google account** with edit access to a Google Sheet
3. **A Slack workspace** with permission to create an incoming webhook
4. **A GitHub repo** where the cron will run (private recommended)

## Setup (about 20 minutes)

### Step 1 — Get Google Ads API credentials

If you don't have these yet:

- Apply for a developer token on your MCC ([instructions](https://developers.google.com/google-ads/api/docs/get-started/dev-token))
- Run through the OAuth refresh-token flow to get a refresh token tied to a
  Google account with access to the accounts you'll update

You should end up with a YAML file like this:

```yaml
developer_token: "YOUR_DEV_TOKEN"
client_id: "xxx.apps.googleusercontent.com"
client_secret: "GOCSPX-xxx"
refresh_token: "1//0xxx"
login_customer_id: "1234567890"   # MCC ID without dashes
use_proto_plus: True
```

Save it somewhere safe — you'll paste its contents into a GitHub secret in
Step 5.

### Step 2 — Get Google Sheets OAuth credentials

The updater reads the uploader tab and writes column D. It needs a user-OAuth
token for the Sheets API.

The fastest path:

1. Create a Google Cloud project (or reuse one)
2. Enable the Google Sheets API
3. Create an OAuth client (Desktop type)
4. Run the [Google OAuth playground](https://developers.google.com/oauthplayground/)
   with scope `https://www.googleapis.com/auth/spreadsheets`
5. Exchange the auth code for a refresh token and save the resulting JSON

You should end up with a `token.json` that looks like:

```json
{
  "token": "ya29.xxx",
  "refresh_token": "1//0xxx",
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id": "xxx.apps.googleusercontent.com",
  "client_secret": "GOCSPX-xxx",
  "scopes": ["https://www.googleapis.com/auth/spreadsheets"]
}
```

### Step 3 — Create the uploader sheet

Create a new Google Sheet (or add a tab to an existing pacing sheet you
control). Add one tab — default name `Shared Budget Uploader` — with this
header row:

| Customer ID | Shared Budget ID | New Budget Amount | Done |
|-------------|------------------|-------------------|------|

See `sheet-template.md` for column semantics, example rows, and how to find a
shared budget's ID. No bootstrap script is needed — the header row is the
whole setup.

Grab the sheet ID from the URL:
`https://docs.google.com/spreadsheets/d/<THIS_IS_THE_ID>/edit`

**Now set the sharing.** This tab is your approval gate: anyone with edit
access can queue a live budget change. Share it accordingly.

### Step 4 — Create a Slack incoming webhook

1. Go to `https://api.slack.com/apps` → **Create New App** → **From scratch**
2. Name it (e.g. "Budget Updater") and pick your workspace
3. In the left sidebar: **Incoming Webhooks** → toggle **Activate Incoming
   Webhooks** to On
4. Scroll down → **Add New Webhook to Workspace** → pick the alerts channel →
   **Allow**
5. Copy the webhook URL — you'll paste it into a GitHub secret in Step 5

**Test the webhook** before you deploy:

```bash
curl -X POST -H 'Content-Type: application/json' \
  --data '{"text":"Shared Budget Updater webhook test"}' \
  YOUR_WEBHOOK_URL
```

**Optional — @-mentions on alerts:** click your Slack profile picture →
**Profile** → **More** → **Copy member ID** (looks like `U01ABC23DEF`). The
mention format is `<@U01ABC23DEF>` — you'll set it as the
`SLACK_USER_MENTION` secret in Step 5. Leave it out for no @-mentions.

**Prefer email, Discord, or Teams instead?** The notification layer is one
self-contained file: `workflows/shared_budget_updater/slack.py`. The rest of
the code calls a single function:

```python
def send_row_failures(webhook_url: str, failed: list[dict], processed_count: int):
    """One consolidated alert for all failed rows in a run."""
```

Drop in a replacement file that exports that function, swap the import in
`main.py`, and repurpose the `webhook_url` parameter (email recipient, Discord
webhook, etc.).

### Step 5 — Set up the GitHub repo and secrets

1. Create a **private** GitHub repo (you'll be storing credential secrets)
2. Copy ALL of this skill folder's contents into the repo root (`SKILL.md`,
   `README.md`, `requirements.txt`, `.github/`, `workflows/`, etc.) and push
3. Open the **Actions** tab — you should see "Shared Budget Updater" listed

**Add repository secrets** (Settings → Secrets and variables → Actions → New
repository secret):

> **Important:** Paste the **full file contents** into the Value field — not
> the file path or filename.

| Secret name | What to paste |
|-------------|---------------|
| `UPDATER_TOKEN_SHEETS_JSON` | Full contents of your `token.json` from Step 2 |
| `UPDATER_GOOGLE_ADS_YAML` | Full contents of your Google Ads YAML from Step 1 |
| `UPDATER_SHEET_ID` | The sheet ID from Step 3 (the long string from the URL, no quotes) |
| `SLACK_WEBHOOK_URL` | Webhook URL from Step 4 (single line) |
| `SLACK_USER_MENTION` | *(Optional)* `<@YOUR_SLACK_USER_ID>` for @-mentions |

**Optional repository variable** (Variables tab → New repository variable):

| Variable name | When to set it |
|---------------|----------------|
| `SHEET_TAB` | Only if you named your tab something other than `Shared Budget Uploader` |

### Step 6 — Manual test (do this before trusting it)

Safe test path — one row, your own test account, a $1 change:

1. Pick an account **you own** (a test account, not a client), note one shared
   budget's current amount
2. Add one row to the tab: that CID, that shared budget ID, an amount $1
   different from the current one, column D empty
3. In GitHub: **Actions → Shared Budget Updater → Run workflow**
4. Watch the logs — you should see `Row 2: CID=... Amount=$...` then
   `Marked 1 row(s) done in sheet`
5. Verify in Google Ads that the shared budget changed, and in the sheet that
   column D now shows `x`
6. **Revert:** add another row setting the budget back to the original amount,
   run again (or let the next cron do it)

To see the failure alert once, add a row with amount `0` and run — you'll get
the consolidated Slack alert with `INVALID_AMOUNT`, and the row stays
unmarked. Delete the row afterward.

### Step 7 — Let the cron run

The workflow is configured for `15 14 * * *` UTC (8:15am MDT). Edit the cron
line in `.github/workflows/shared-budget-updater.yml` to match your own
morning — ideally after your pacing/approval process finishes and before the
ad day ramps up.

## Operations

### Column D semantics

- Empty D + filled A/B/C = approved, pending — will be pushed on the next run
- `x` in D = processed — the workflow will never touch that row again
- **Clearing an `x` re-pushes that row on the next run.** Useful for
  re-applying a change, but do it deliberately — it is a live mutation
- Never hand-write `x` — that silently cancels an approved change

### The $0-or-less guard

Rows with an amount of $0 or less are skipped with an `INVALID_AMOUNT` alert
and are never sent to the API. A $0 budget is almost always an attempt to
pause spend — which is a status change this tool deliberately cannot make.
Remove the row and pause the campaign through normal channels.

### Failed rows retry themselves

Any failed row keeps an empty column D, so the next scheduled run picks it up
again automatically. Don't re-dispatch the workflow to force a retry — fix
the underlying issue (usually the row data) and let the schedule heal it.

### Alert triage

`rules.md` has the error-code → action table; `examples.md` walks three real
decisions. Short version: transient errors need nothing; sheet-data errors
(INVALID_AMOUNT, NOT_FOUND) get fixed in the sheet by a human; permission
errors mean your OAuth or account access broke — investigate immediately.

## Troubleshooting

**"UPDATER_SHEET_ID environment variable not set"** — The secret isn't set in
GitHub, or the workflow yml doesn't reference it. Check Step 5.

**"INVALID_AMOUNT"** — The row's amount is $0 or less. The guard skipped it
before any API call. Fix or remove the row.

**"NOT_FOUND" / "INVALID_CUSTOMER_ID"** — The CID/budget ID pair doesn't
resolve: transposed digits, a budget from a different account, or an account
your OAuth user can't access. Verify both IDs.

**"USER_PERMISSION_DENIED" / "PERMISSION_DENIED"** — The OAuth account lost
access to the Ads account, or the Sheets token can't edit the sheet. Check
MCC links and sheet sharing.

**Rows sit unprocessed with empty column D** — Check the Actions tab: is the
cron firing? Are A, B, and C all filled? The workflow only processes rows
with all three filled and D empty.

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
