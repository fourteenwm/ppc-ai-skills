---
name: google-ads-api-setup
description: One-time setup guide and scripts for getting Google Ads API access working. Auto-invoke when user says "set up Google Ads API", "generate credentials", "create google-ads.yaml", "OAuth setup", "test API connection", or hits authentication errors like "invalid_grant" or "The developer token is not approved". Prerequisite for every skill that queries or modifies Google Ads.
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
- `Request had invalid authentication credentials`
- `The developer token is not approved`
- `login_customer_id is required`

---

## What This Skill Does

1. Walks the user through the 9-step Google Cloud Console + OAuth + Developer Token flow (see `README.md`)
2. Generates their refresh token via `generate_credentials.py`
3. Verifies connectivity via `test_connection.py`
4. Produces a working `google-ads.yaml` at their project root

---

## Files in This Skill

| File | Purpose |
|------|---------|
| `README.md` | Full 9-step setup walkthrough with common mistakes and troubleshooting |
| `generate_credentials.py` | OAuth flow — prompts the user to authorize in a browser, prints the refresh token |
| `test_connection.py` | Confirms `google-ads.yaml` works by listing accessible accounts |
| `google-ads.example.yaml` | Template YAML with all required fields — users copy and fill in |

---

## How to Run

### Step 1 — Generate credentials (after OAuth setup in README steps 1-5)

```bash
python generate_credentials.py --client-secrets client_secret.json
```

Opens a browser URL. User signs in → grants access → refresh token prints to terminal.

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
| `invalid_grant` | Refresh token expired or revoked | Re-run `generate_credentials.py` |
| `developer token is not approved` | New token awaiting Google approval | Check API Center in MCC; test tokens work for test accounts only |
| `login_customer_id is required` | YAML missing the MCC ID | Add `login_customer_id: "1234567890"` (digits only) |
| `ModuleNotFoundError: google.ads` | Package not installed | `pip install google-ads google-auth google-auth-oauthlib` |
| `The caller does not have permission` | Account not linked to your MCC | Verify the CID is accessible from the MCC you're using |

See `README.md` for the full troubleshooting list.

---

## Security Notes

- **Never commit** `google-ads.yaml`, `client_secret.json`, or the refresh token itself
- `.gitignore` in this repo already excludes `*.yaml`, `*.env`, and `client_secret*.json`
- Refresh tokens grant full access to linked Google Ads accounts — treat as passwords
- Revoke compromised tokens at [myaccount.google.com/permissions](https://myaccount.google.com/permissions)

---

## Related Skills

- [`mutation-safety`](../mutation-safety/) — install before any skill that modifies accounts
- [`gaql-query-patterns`](../gaql-query-patterns/) — start here once API is working
- [`google-ads-query`](../google-ads-query/) — general-purpose GAQL executor

---

## Installation

```bash
mkdir -p .claude/skills/google-ads-api-setup
curl -o .claude/skills/google-ads-api-setup/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/google-ads-api-setup/SKILL.md
curl -o .claude/skills/google-ads-api-setup/README.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/google-ads-api-setup/README.md
curl -o .claude/skills/google-ads-api-setup/generate_credentials.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/google-ads-api-setup/generate_credentials.py
curl -o .claude/skills/google-ads-api-setup/test_connection.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/google-ads-api-setup/test_connection.py
curl -o .claude/skills/google-ads-api-setup/google-ads.example.yaml \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/google-ads-api-setup/google-ads.example.yaml
```
