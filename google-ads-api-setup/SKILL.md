---
name: google-ads-api-setup
description: One-time setup guide and scripts for getting Google Ads API access working. Auto-invoke when user says "set up Google Ads API", "generate credentials", "create google-ads.yaml", "OAuth setup", "test API connection", or hits authentication errors like "invalid_grant", "redirect_uri_mismatch", "The developer token is not approved", or a refresh token that keeps expiring every week. Prerequisite for every skill that queries or modifies Google Ads.
allowed-tools: [Bash, Read, Write]
---

# Google Ads API Setup

**Purpose:** Get your Google Ads API connection working from scratch. This is the prerequisite for every other skill that queries or modifies Google Ads accounts.

**Type:** Setup / onboarding skill (one-time — run once per machine)

**Time required:** ~30 minutes

---

## When to Invoke

Auto-invoke when user says:
- "Set up Google Ads API"
- "Generate credentials"
- "Create google-ads.yaml"
- "OAuth setup for Google Ads"
- "Test my API connection"
- "How do I get a refresh token"

Or when they hit common authentication errors:
- `google.auth.exceptions.RefreshError: invalid_grant`
- "My refresh token keeps expiring every 7 days"
- `redirect_uri_mismatch`
- `Request had invalid authentication credentials`
- `The developer token is not approved`
- `login_customer_id is required`

---

## What This Skill Does

1. Walks the user through the 9-step Google Cloud Console + OAuth + Developer Token flow (see `README.md`), including the Internal-vs-External consent screen decision and publishing External apps to production so refresh tokens don't expire every 7 days
2. Generates their refresh token via `generate_credentials.py` — one consent covering **Google Ads + Google Sheets + Drive read-only**, because the Sheets-writing skills in this catalog (non-serving-keyword-scanner, ads-checker, rsa-refresh, sqr-pipeline, and others) reuse this same token from `google-ads.yaml` for their report output
3. Verifies connectivity via `test_connection.py`
4. Produces a working `google-ads.yaml` at their project root

> **Token generated before 2026-07-17?** It carries only the Ads scope — Ads queries work, but Sheets-writing skills 403. Re-run `generate_credentials.py` once and paste the new `refresh_token` into your `google-ads.yaml`. Scopes are fixed when a token is minted; they can't be added afterward.

---

## Files in This Skill

| File | Purpose |
|------|---------|
| `README.md` | Full 9-step setup walkthrough with common mistakes and troubleshooting |
| `generate_credentials.py` | OAuth flow — prompts the user to authorize in a browser, prints the refresh token (requests the Ads + Sheets + Drive-read scopes in one consent) |
| `test_connection.py` | Confirms `google-ads.yaml` works by listing accessible accounts |
| `google-ads.example.yaml` | Template YAML with all required fields — users copy and fill in |
| `diagrams/` | Workflow diagrams (Mermaid sources + rendered SVGs embedded in the README) |

---

## How to Run

### Step 1 — Generate credentials (after README steps 1-6: OAuth client created, packages installed)

```bash
python generate_credentials.py --client-secrets client_secret.json
```

Opens a browser URL. User signs in → grants access → refresh token prints to terminal. The consent asks for Google Ads, Google Sheets, and Drive read-only together — if Google shows individual checkboxes, tick all three (the script warns if any were skipped).

### Step 2 — Copy the example YAML

```bash
cp google-ads.example.yaml google-ads.yaml
```

Fill in `client_id`, `client_secret`, `refresh_token`, `developer_token`, `login_customer_id`.

### Step 3 — Test the connection

```bash
python test_connection.py --config google-ads.yaml
```

Expected output: list of accounts under the MCC.

---

## Common Failure Modes

| Error | Cause | Fix |
|-------|-------|-----|
| `invalid_grant` | External app left in "Testing" status (tokens expire in 7 days), or token revoked | Publish the app to production (README Step 3, Option B), then re-run `generate_credentials.py` |
| `redirect_uri_mismatch` | OAuth client created as "Web application" instead of "Desktop app" | Delete the client, create a new one with type **Desktop app**, regenerate token |
| `developer token is not approved` | New token awaiting Google approval | Check API Center in MCC; test tokens work for test accounts only |
| `DEVELOPER_TOKEN_PROHIBITED` | Cloud project already made calls with a different MCC's dev token (each project locks to one token) | Create a fresh Cloud project + OAuth client, regenerate the refresh token, call from there |
| `login_customer_id is required` | YAML missing the MCC ID | Add `login_customer_id: "1234567890"` (digits only) |
| `ModuleNotFoundError: google.ads` | Package not installed | `pip install google-ads google-auth google-auth-oauthlib google-auth-httplib2 pyyaml` |
| `The caller does not have permission` | Account not linked to your MCC, or wrong Google account used in OAuth | Verify the CID is accessible from the MCC you're using; confirm which account authorized |
| Sheets write 403s (`insufficient authentication scopes`) while Ads queries work | Refresh token minted before 2026-07-17 (Ads scope only), or consent checkboxes left unticked | Re-run `generate_credentials.py`, tick every permission, paste the new token into `google-ads.yaml` |

See `README.md` for the full troubleshooting list.

---

## Security Notes

- **Never commit** `google-ads.yaml`, `client_secret.json`, or the refresh token itself
- `.gitignore` in this repo already excludes `*.yaml`, `*.env`, and `client_secret*.json`
- Refresh tokens grant full access to linked Google Ads accounts — plus, with the scopes this generator requests, read/write access to your Google Sheets and read access to your Drive file listing. Treat as passwords
- Revoke compromised tokens at [myaccount.google.com/permissions](https://myaccount.google.com/permissions)

---

## Related Skills

- [`mutation-safety`](../mutation-safety/) — install before any skill that modifies accounts
- [`gaql-query-patterns`](../gaql-query-patterns/) — start here once API is working
- [`google-ads-query`](../google-ads-query/) — general-purpose GAQL executor

---

## Installation

Clone the repo so you get the full folder — both scripts, the example yaml, and the diagrams the README embeds:

```bash
git clone https://github.com/fourteenwm/ppc-ai-skills.git
cp -r ppc-ai-skills/google-ads-api-setup .claude/skills/google-ads-api-setup
```
