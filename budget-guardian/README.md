# Budget Guardian

A 2-hour spend tripwire for your Google Ads MCC. Alert-only — never pauses campaigns.

## What it catches

- Fat-fingered budgets — wrong formulas or stale values in a budget sheet that quietly push the wrong number across multiple accounts
- Hijacked MCCs and malicious spend — unauthorized PMax campaigns at huge daily budgets, drained accounts, agency-level changes nobody approved
- Runaway PMax during learning that blows past budget
- Any account where month-to-date spend crosses 100% or 120% of its monthly budget

## How it works

A GitHub Actions cron fires every 2 hours. The job:

1. Reads per-account monthly budgets from a Google Sheet you control
2. Queries Google Ads API for each account's month-to-date spend
3. Compares spend to budget
4. If `spend / budget >= 1.0` and you haven't been alerted at the 100% threshold this month → posts a **Warning** to Slack
5. If `spend / budget >= 1.2` and you haven't been alerted at the 120% threshold this month → posts a **Critical** to Slack
6. Records the alert in a state tab so the same alert doesn't fire twice in one month

**Alerts are deduped per account per threshold per month.** You get a 100% ping once, a 120% ping once, then silence on that account until next month.

## Prerequisites

You'll need:

1. **A Google Ads MCC** with API access (developer token + OAuth refresh token)
2. **A Google account** with edit access to a Google Sheet (we'll create it together)
3. **A Slack workspace** with permission to create an incoming webhook
4. **A GitHub repo** where the cron will run (free for public repos and many private use cases)
5. **Python 3.12** locally (only for the one-time `setup_tabs.py` step — the cron runs on GitHub's runners)

## Setup (about 20 minutes)

### Step 1 — Get Google Ads API credentials

If you don't have these yet:

- Apply for a developer token on your MCC ([instructions](https://developers.google.com/google-ads/api/docs/get-started/dev-token))
- Run through the OAuth refresh-token flow to get a refresh token tied to a Google account with access to the MCC

You should end up with a YAML file like this:

```yaml
developer_token: "YOUR_DEV_TOKEN"
client_id: "xxx.apps.googleusercontent.com"
client_secret: "GOCSPX-xxx"
refresh_token: "1//0xxx"
login_customer_id: "1234567890"   # MCC ID without dashes
use_proto_plus: True
```

Save it somewhere safe — you'll paste its contents into a GitHub secret in Step 5.

### Step 2 — Get Google Sheets OAuth credentials

The Guardian reads budgets from and writes state to a Google Sheet. It needs a user-OAuth token for the Sheets API.

The fastest path:

1. Create a Google Cloud project (or reuse one)
2. Enable the Google Sheets API
3. Create an OAuth client (Desktop type)
4. Run the [Google OAuth playground](https://developers.google.com/oauthplayground/) with scope `https://www.googleapis.com/auth/spreadsheets`
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

### Step 3 — Create your budget sheet

Create a new Google Sheet (or use an existing one). You'll add two tabs:

- `Budgets` — your per-account monthly budgets (you fill this in)
- `Guardian Config` and `Guardian State` — auto-created in Step 6

Set up the `Budgets` tab like this:

| Account Name | CID | Monthly Budget |
|--------------|-----|----------------|
| Acme Auto Repair | 1234567890 | 3000 |
| Bright Smiles Dental | 9876543210 | 2500 |
| Coastal HVAC | 5555555555 | 5000 |

- **Account Name** (column A): any label — used in Slack alerts
- **CID** (column B): Google Ads customer ID, digits only (no dashes)
- **Monthly Budget** (column C): dollar amount, no currency symbol

Grab the sheet ID from the URL: `https://docs.google.com/spreadsheets/d/<THIS_IS_THE_ID>/edit`

See `sheet-template.md` for more detail.

### Step 4 — Create a Slack incoming webhook

**If you don't use Slack yet:** Slack is free for small workspaces and takes about 2 minutes to set up.

1. Go to `https://slack.com/get-started` → **Create a Workspace**
2. Enter your email, confirm via the 6-digit code Slack sends you
3. Name the workspace (e.g. "Ads Alerts") and skip the "invite teammates" step
4. Create a channel for budget alerts (e.g. `#budget-alerts`) — or use the default `#general`
5. You're now ready for the webhook steps below

**Create the webhook:**

1. Go to `https://api.slack.com/apps` → **Create New App** → **From scratch**
2. Name it (e.g. "Budget Guardian") and pick the workspace from above
3. In the left sidebar: **Incoming Webhooks** → toggle **Activate Incoming Webhooks** to On
4. Scroll down → click **Add New Webhook to Workspace** → pick the alerts channel → **Allow**
5. Copy the webhook URL (starts with `https://hooks.slack.com/services/...`) — you'll paste this into a GitHub secret in Step 5

**Test the webhook before you deploy** so a typo in the URL doesn't cost you the first real alert. From any terminal, run:

```bash
curl -X POST -H 'Content-Type: application/json' \
  --data '{"text":"Budget Guardian webhook test"}' \
  YOUR_WEBHOOK_URL
```

If the test message lands in your alerts channel, you're good. If you see `invalid_token` or `no_service`, the URL is wrong — go back to the app's Incoming Webhooks page and copy it again.

**Optional — @-mentions on alerts:**

If you want the Guardian to @-mention you (or a group) when an alert fires, grab your Slack member ID:

- In Slack, click your profile picture → **Profile** → **More** → **Copy member ID** (looks like `U01ABC23DEF`)
- The mention format is `<@U01ABC23DEF>`
- For a Slack user group, the format is `<!subteam^S01ABC23DEF>` (find the group ID via the group's URL)

You'll set this as the `SLACK_USER_MENTION` secret in Step 5. Leave it blank if you don't want @-mentions.

### Step 4b — Prefer email, Discord, or Teams instead of Slack?

The Guardian's notification layer is one self-contained file: `workflows/budget_guardian/slack.py` (~80 lines). The rest of the code calls it through three functions:

```python
def send_warning(webhook_url: str, name: str, cid: str, budget: float, spend: float):
    """Fires at 100% of budget."""

def send_critical(webhook_url: str, name: str, cid: str, budget: float, spend: float):
    """Fires at 120% of budget."""

def send_error(webhook_url: str, error_message: str):
    """Fires if the workflow itself crashes."""
```

Drop in a replacement file (e.g. `email.py`, `discord.py`, `teams.py`) that exports those three functions, swap the import in `main.py`, and you're done. The `webhook_url` parameter can be repurposed — for email, pass the recipient address; for Discord, pass the Discord webhook URL (same format as Slack). Set the relevant secret in GitHub Actions accordingly.

### Step 5 — Set up the GitHub repo and GitHub Actions

This is where the 2-hour cron actually runs. GitHub Actions is GitHub's built-in scheduler — you give it a workflow YAML, it runs the workflow on a schedule (or on demand). No server to maintain.

**If you don't use GitHub yet:** Free, takes about 3 minutes.

1. Go to `https://github.com` → **Sign up**
2. Verify your email when prompted
3. Top-right `+` icon → **New repository**
4. Name it (e.g. `budget-guardian-deploy`), choose **Private** (recommended — you'll be storing credentials), leave "Initialize with README" **unchecked**
5. Click **Create repository**. You'll land on an empty repo page with a clone URL — copy it.

**Push this skill's files to your new repo.** From the folder where you have the unzipped skill files locally (the same files you see in this package):

```bash
git init budget-guardian-deploy
cd budget-guardian-deploy
# Copy ALL the contents of this skill folder into the repo root
# (SKILL.md, README.md, requirements.txt, .github/, workflows/, etc.)
git add .
git commit -m "Initial: Budget Guardian deployment"
git remote add origin <the-clone-URL-from-above>
git push -u origin main
```

After the push, open your repo on github.com and click the **Actions** tab. You should see "Budget Guardian" listed in the left sidebar. If you don't see it, the `.github/workflows/budget-guardian.yml` file isn't where it needs to be — double-check the folder structure matches the package.

**Add repository secrets** (the sensitive values the workflow needs at runtime). In your repo: **Settings → Secrets and variables → Actions → New repository secret** for each of these.

> **Important:** Paste the **full file contents** into the Value field — not the file path or filename. For JSON/YAML files, open the file in a text editor, select all, copy, paste.

| Secret name | What to paste |
|-------------|---------------|
| `GUARDIAN_TOKEN_SHEETS_JSON` | Full contents of your `token.json` from Step 2 |
| `GUARDIAN_GOOGLE_ADS_YAML` | Full contents of your Google Ads YAML from Step 1 |
| `SLACK_WEBHOOK_URL` | Webhook URL from Step 4 (single line) |
| `GUARDIAN_SHEET_ID` | The sheet ID from Step 3 (the long string from the sheet URL, no quotes) |
| `SLACK_USER_MENTION` | *(Optional)* `<@YOUR_SLACK_USER_ID>` for @-mentions, or leave blank |

**Add an optional repository variable** (non-sensitive config). Same menu, but click the **Variables** tab → **New repository variable**:

| Variable name | When to set it |
|---------------|----------------|
| `GUARDIAN_BUDGET_TAB` | Only if you named your budget tab something other than `Budgets`. Defaults to `Budgets` if unset. |

**Cost & limits.** GitHub Actions is generous:
- **Public repos:** unlimited minutes, free.
- **Private repos:** 2,000 free minutes/month. The Guardian uses about 1 minute per run × 12 runs/day × 30 days = ~360 minutes/month — well under 20% of the free tier.
- **Storage:** negligible. The workflow doesn't write artifacts.

**Reading the logs.** Once a run has fired:
- **Actions** tab → **Budget Guardian** → click any run row → click the `guardian` job → click any step to expand its logs
- Failed runs automatically email you (configure at `github.com/settings/notifications`)
- You can trigger a manual run any time: Actions → Budget Guardian → **Run workflow** button (top-right of the run list). Useful for testing without waiting for the next 2-hour tick.

### Step 6 — Bootstrap the sheet tabs

This step creates the `Guardian Config` and `Guardian State` tabs in your sheet and sets the kill switch to `ENABLED`.

```bash
pip install -r requirements.txt

# Set env vars for the one-time setup
export GOOGLE_TOKEN_PATH=/path/to/your/token.json
export GUARDIAN_SHEET_ID=your_sheet_id_from_step_3

python -m workflows.budget_guardian.setup_tabs
```

You should see output like:

```
Will create: Guardian Config
Will create: Guardian State
Tabs created.
Headers and defaults written.
Done! Guardian Config kill switch set to ENABLED.
```

Open your sheet — you should now see the two new tabs. The `Guardian Config` tab has a `Kill Switch` row set to `ENABLED`. Flip it to `DISABLED` any time you want to pause the Guardian without touching GitHub.

### Step 7 — Run a manual test

In your GitHub repo, go to **Actions → Budget Guardian → Run workflow** to trigger a manual run. Watch the logs.

If everything is wired up correctly, you'll see something like:

```
============================================================
BUDGET GUARDIAN
============================================================
Loaded 3 account budgets from sheet
Acme Auto Repair (1234567890): $1,250.00 / $3,000.00 = 42%
Bright Smiles Dental (9876543210): $2,100.00 / $2,500.00 = 84%
Coastal HVAC (5555555555): $0.00 / $5,000.00 = 0%
============================================================
SUMMARY
  Accounts checked: 3
  Warnings (100%):  0
  Critical (120%):  0
  Errors:           0
============================================================
```

If you want to verify Slack alerts work without waiting for an account to actually overspend, temporarily set one of your budgets very low (e.g. $1) and re-run. You should get a 100% and 120% alert in Slack. Then reset the budget.

### Step 8 — Let the cron run

The workflow `.github/workflows/budget-guardian.yml` is configured to run every 2 hours on the hour (`0 */2 * * *`). Once you've pushed it and the secrets are set, it runs automatically. No further action needed.

## What an alert looks like

**100% Warning:**

> :warning: **Warning: Budget Hit 100%**
> Account: Acme Auto Repair
> CID: 1234567890
> Monthly Budget: $3,000.00
> MTD Spend: $3,142.00 (105%)
> _No action taken. Monitor closely._

**120% Critical:**

> :rotating_light: **CRITICAL: Budget Exceeded 120%**
> Account: Acme Auto Repair
> CID: 1234567890
> Monthly Budget: $3,000.00
> MTD Spend: $3,720.00 (124%)
> _Investigate immediately. No campaigns were paused._

## Operations

### Kill switch

Set the `Guardian Config` tab's `Kill Switch` cell to `DISABLED` to silence the Guardian without touching GitHub. The next 2-hour run will see the disabled state and exit immediately.

### Adding a new account

Add a row to the `Budgets` tab with the account's name, CID, and monthly budget. The next run picks it up automatically.

### Resetting alerts mid-month

If you want a previously-alerted account to re-alert (e.g. you raised the budget and want a fresh tripwire), delete the corresponding row from the `Guardian State` tab.

### Monthly cleanup

The Guardian automatically clears state rows from previous months at the start of each run, so the State tab stays small.

## Cost

- **GitHub Actions:** 12 runs/day × 30 days = 360 runs/month. Each run is ~30-60 seconds. Well within GitHub's free tier for public repos and most private repos.
- **Google Ads API:** ~1-2 queries per account per run. For a 50-account MCC, that's ~50,000 queries/month — well under standard quotas.
- **Google Sheets API:** ~5 reads/writes per run. Trivial.
- **Slack:** Free.

## Troubleshooting

**"SLACK_WEBHOOK_URL not set"** — Check that the `SLACK_WEBHOOK_URL` secret is set in GitHub Actions repository secrets, and that the workflow YAML references it.

**"GOOGLE_TOKEN_PATH environment variable not set"** — The workflow writes the token to `/tmp/sheets-token.json` before the run. If you see this error, the `Write credentials` step probably failed — check that `GUARDIAN_TOKEN_SHEETS_JSON` is set.

**"customerClient: invalid_customer_id"** — A CID in your budget sheet doesn't match a real account, or doesn't grant the OAuth account access. Double-check the CID column.

**"PERMISSION_DENIED" from Sheets API** — The OAuth account doesn't have edit access to the sheet. Share the sheet with that account.

**No alerts firing even when budgets are exceeded** — Check the `Guardian Config` kill switch is `ENABLED`. Then check the `Guardian State` tab — if the account already has a row for the current month and threshold, dedupe is suppressing the alert. Delete the row to re-alert.

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)

