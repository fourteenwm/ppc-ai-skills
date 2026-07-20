# Markdown to Sheets Presenter - Setup Guide

## Prerequisites

One credential file: `google-ads.yaml` at your project root. If you don't
have one, the [google-ads-api-setup skill](../google-ads-api-setup/) walks
you through creating it — its generator mints the refresh token with the
`spreadsheets` scope this skill needs, alongside the Ads scopes the rest of
the catalog uses.

Set up before 2026-07-17? Re-run the generator once and paste the new
`refresh_token` into your `google-ads.yaml` — earlier tokens were Ads-only
and will 403 at the Sheets step.

Python packages:

```bash
pip install google-api-python-client google-auth pyyaml
```

---

## Quick Test

From your project root (where `google-ads.yaml` lives):

```bash
python .claude/skills/markdown-to-sheets-presenter/scripts/create_spreadsheet.py "Test Report"
```

You should get JSON with the new sheet's ID and URL. The sheet is created
in the Drive root of the account that authorized the token — move it into
a folder in Drive if you organize by client.

---

## Usage

### From Claude Code

```
"Make this competitive analysis presentable for the client"
"Export this report to Google Sheets"
"Create a Google Sheet from this report"
```

### From Command Line

```bash
python .claude/skills/markdown-to-sheets-presenter/scripts/create_spreadsheet.py "Report Name"

# Credentials somewhere else?
python .claude/skills/markdown-to-sheets-presenter/scripts/create_spreadsheet.py "Report Name" --config credentials/google-ads.yaml
```

---

## Troubleshooting

### "Credentials not found at google-ads.yaml"
- Run from the directory that holds `google-ads.yaml`, or pass `--config path/to/google-ads.yaml`
- No file yet? See the [google-ads-api-setup skill](../google-ads-api-setup/)

### "Google Sheets refused the request (403)"
- Your refresh token predates the Sheets scope — re-run the api-setup generator once and paste the new `refresh_token` into `google-ads.yaml`

### "Can't find the sheet in Drive"
- It's created in the Drive root of the Google account that authorized the token — check that account, then move the sheet wherever you like
