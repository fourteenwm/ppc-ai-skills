# Google Ads API Setup

Get your Google Ads API connection working from scratch. This is the prerequisite for every other skill that queries or modifies Google Ads accounts.

**Time required:** 30 minutes (one-time setup)

**The pain point:** Setting up Google Ads API access is where most people give up. The Google Cloud Console is confusing, OAuth is a maze, and one wrong step means cryptic errors. This guide walks through every step with the exact clicks and the common mistakes.

---

## What You'll Have When Done

- A working `google-ads.yaml` credential file
- The ability to query any account under your MCC
- A test script that confirms everything works

---

## Prerequisites

- Google Ads account with **MCC (Manager) access**
- Google Cloud account (free: [console.cloud.google.com](https://console.cloud.google.com))
- **Python 3.10+** installed
- **pip** (comes with Python)

---

## Step 1: Create a Google Cloud Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click the project dropdown (top-left, next to "Google Cloud") → **New Project**
3. Name it something you'll recognize (e.g., "PPC Tools")
4. Click **Create**, then select the new project from the dropdown

**Common mistake:** Forgetting to select the project after creating it. The dropdown should show your new project name.

---

## Step 2: Enable the Google Ads API

1. In the left sidebar: **APIs & Services → Library**
2. Search for "Google Ads API"
3. Click on it → Click **Enable**

**Common mistake:** Enabling "Google Ads" (the general product page) instead of "Google Ads API" (the developer API). Make sure you're on the API with the blue API icon.

---

## Step 3: Configure the OAuth Consent Screen

This tells Google what your app is. Even though it's just for you, Google requires it.

1. **APIs & Services → OAuth consent screen**
2. Choose **External** → Click **Create**
3. Fill in:
   - **App name:** "PPC Tools" (or whatever you want)
   - **User support email:** your email
   - **Developer contact email:** your email
4. Click **Save and Continue** through each screen (Scopes, Test Users, Summary)
5. On the **Test Users** step → click **+ Add Users** → add your own email
6. Click **Save and Continue** → **Back to Dashboard**

**Common mistake:** Skipping the Test Users step. If you don't add yourself as a test user, the OAuth flow will fail with "Access blocked: This app's request is invalid."

**Common mistake:** Choosing "Internal" instead of "External." Internal only works with Google Workspace organizations. Choose External even if it's just for you.

---

## Step 4: Create OAuth Client Credentials

1. **APIs & Services → Credentials**
2. Click **+ Create Credentials → OAuth client ID**
3. Application type: **Desktop app**
4. Name: "PPC Tools Desktop" (or whatever you want)
5. Click **Create**
6. A popup shows your Client ID and Client Secret — click **Download JSON**
7. Save the downloaded file as `client_secret.json` in this folder

**Keep this file safe.** It contains your OAuth client credentials. Never commit it to git.

---

## Step 5: Get Your Developer Token

1. Log into Google Ads at [ads.google.com](https://ads.google.com)
2. Navigate to your **MCC account** (the top-level manager account)
3. Click the **wrench icon** (Tools & Settings) → **Setup → API Center**
4. Copy your **Developer Token**

**If you don't see API Center:** You may need to apply for API access. Click "Apply for access" — approval can take a few days for new accounts.

**If your token says "Test Account":** That's fine for development. Test tokens can only access test accounts, but you can apply for Basic access once you're ready.

**Note:** The developer token belongs to the MCC, not your personal Google account.

---

## Step 6: Install Python Dependencies

```bash
pip install google-ads google-auth google-auth-oauthlib google-auth-httplib2 pyyaml
```

---

## Step 7: Generate Your Refresh Token

Run the credential generator script included in this folder:

```bash
python generate_credentials.py --client-secrets client_secret.json
```

1. A URL prints in your terminal — open it in your browser
2. Sign in with the Google account that has Google Ads access
3. You'll see a "Google hasn't verified this app" warning — click **Continue** (this is your own app)
4. Grant the requested permissions
5. The terminal shows: `Your refresh token is: 1//0xxxxxxx...`
6. **Copy this token** — you'll need it in the next step

**Common mistake:** Signing in with the wrong Google account. Use the account that has access to the Google Ads MCC, not a personal account.

**Common mistake:** The "unverified app" warning scares people off. Since you created this app yourself, it's safe to continue.

---

## Step 8: Create Your google-ads.yaml

1. Copy the example file:
   ```bash
   cp google-ads.example.yaml google-ads.yaml
   ```

2. Open `google-ads.yaml` and fill in your values:
   ```yaml
   # Get client_id and client_secret from your client_secret.json file
   client_id: "YOUR_CLIENT_ID.apps.googleusercontent.com"
   client_secret: "YOUR_CLIENT_SECRET"

   # From Step 7
   refresh_token: "YOUR_REFRESH_TOKEN"

   # From Step 5
   developer_token: "YOUR_DEVELOPER_TOKEN"

   # Your MCC (Manager) account ID, digits only, no dashes
   login_customer_id: "1234567890"

   use_proto_plus: True
   ```

**Where to find client_id and client_secret:** Open your `client_secret.json` file — the values are in the `installed` section.

**login_customer_id format:** Use digits only, no dashes. If your MCC ID is `123-456-7890`, enter `1234567890`.

---

## Step 9: Test Your Connection

```bash
python test_connection.py --config google-ads.yaml
```

**Expected output:**
```
Connecting to Google Ads API...
Success! Found X accounts under your MCC.

Accounts:
  - Account Name 1 (ID: 1234567890)
  - Account Name 2 (ID: XXXXXXXXXX)
  ...
```

If you see your accounts listed, you're done. The API connection is working.

---

## Troubleshooting

### "google.auth.exceptions.RefreshError: invalid_grant"
Your refresh token has expired or was revoked. Re-run Step 7 to generate a new one.

### "Request had invalid authentication credentials"
Double-check that `client_id`, `client_secret`, and `refresh_token` in your YAML all match (no extra spaces, no missing characters).

### "The developer token is not approved"
New developer tokens need Google approval. Check API Center in your MCC for the approval status. Test tokens work for test accounts only.

### "The caller does not have permission"
Your Google account doesn't have access to the account you're trying to query. Check your MCC → Accounts to verify the account is linked.

### "ModuleNotFoundError: No module named 'google.ads'"
Run `pip install google-ads` again. If using a virtual environment, make sure it's activated.

### "login_customer_id is required"
Add `login_customer_id` to your YAML file. This should be your MCC's customer ID (digits only, no dashes).

---

## Security Notes

- **Never commit** `google-ads.yaml` or `client_secret.json` to git
- Add both to your `.gitignore`
- Your refresh token grants full access to your Google Ads accounts — treat it like a password
- If you suspect a token is compromised, revoke it at [myaccount.google.com/permissions](https://myaccount.google.com/permissions)

---

## Next Steps

Once your API connection is working:
- Use the [GAQL Query Patterns](../gaql-query-patterns/) skill to start querying your accounts
- Install the [Mutation Safety](../mutation-safety/) skill before making any changes

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage 118 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
