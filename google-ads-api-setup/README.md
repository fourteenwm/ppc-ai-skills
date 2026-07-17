# Google Ads API Setup

Get your Google Ads API connection working from scratch. This is the prerequisite for every other skill that queries or modifies Google Ads accounts.

**Time required:** 30 minutes (one-time setup)

**The pain point:** Setting up Google Ads API access is where most people give up. The Google Cloud Console is confusing, OAuth is a maze, and one wrong step means cryptic errors. This guide walks through every step with the exact clicks, the common mistakes, and — the part most guides skip — the one setting that stops your credentials from silently dying a week later.

![Sequence diagram: a PPC manager creates a Cloud project and enables the Ads API, picks Internal or External on the consent screen (External apps get published to production — left in Testing, tokens expire every 7 days), creates a Desktop-type OAuth client, copies the developer token from the MCC's API Center, then runs the two included scripts — one browser sign-in produces the refresh token, google-ads.yaml gets its five values, and the connection test lists the accounts under the MCC](diagrams/workflow-hero.svg)

---

## What You'll Have When Done

- A working `google-ads.yaml` credential file
- The ability to query any account under your MCC
- A test script that confirms everything works
- Credentials that **keep working** — not ones that expire after 7 days
- One token that also covers **Google Sheets** — the skills in this catalog that write reports to Sheets reuse it straight from your `google-ads.yaml`, no second OAuth setup

---

## Prerequisites

- Google Ads account with **MCC (Manager) access**
- Google Cloud account (free: [console.cloud.google.com](https://console.cloud.google.com))
- **Python 3.10+** installed
- **pip** (comes with Python)

---

## Before You Start

- **Use the same Google account everywhere in this guide** — the one that has access to your MCC. Cloud Console, OAuth authorization, all of it. Mixing accounts is the #1 source of "permission denied" errors later. Not sure which account that is? Log into [ads.google.com](https://ads.google.com) and check the profile icon in the top-right.
- You'll be moving between two websites: **Google Cloud Console** and **Google Ads**. Keep both tabs open.
- Nothing here costs money. The Google Ads API is free, and Google Cloud's free tier covers everything in this guide. Ignore the "$300 free credits" offer if it appears.

---

## Mental Model: What's Actually Happening (60 seconds)

When your code calls the Google Ads API, Google asks five questions:

| Question Google asks | Answered by | You get it in |
|----------------------|-------------|---------------|
| "Which app is calling?" | OAuth Client ID + Secret | Step 4 |
| "Is this app allowed to use the Ads API?" | API enabled on your Cloud project | Step 2 |
| "Are *you* licensed to use the Ads API at all?" | Developer token | Step 5 |
| "Which user authorized this?" | Refresh token | Step 7 |
| "Which MCC are you acting from?" | login_customer_id | Step 8 |

All five answers end up in one file: `google-ads.yaml`. That's the whole game — the rest is clicking through Google's consoles to collect them.

Here's the entire journey at a glance — three phases, two decision gates, one destination:

![Flowchart of the setup in three phases: in Google Cloud Console (create a project and enable the Ads API, then the Workspace-org fork — Internal consent screen with no expiry, or External plus test user plus publishing the app because Testing-status tokens die every 7 days — then a Desktop-type OAuth client, since a Web app fails later with redirect_uri_mismatch, and download client_secret.json), in Google Ads (Admin → API Center, copy the developer token — each Cloud project locks to one token), and in the terminal (pip install, generate the refresh token with one browser sign-in, fill the five values in google-ads.yaml, run the connection test — accounts listed means done; any error maps to a fix in the troubleshooting table)](diagrams/setup-flow.svg)

The `.mmd` sources for both diagrams live in `diagrams/` — they're [Mermaid](https://mermaid.js.org/) diagram-as-code, rendered with the included theme.

---

## Step 1: Create a Google Cloud Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click the project dropdown (top-left, next to "Google Cloud") → **New Project**
3. Name it something you'll recognize (e.g., "PPC Tools")
4. **Organization:** If your company uses Google Workspace, create the project **inside your organization** — that unlocks the simpler "Internal" option in Step 3. No Workspace? "No organization" is fine.
5. Click **Create**, then select the new project from the dropdown

**Common mistake:** Forgetting to select the project after creating it.

✅ **Check:** The project name in the top bar matches what you just created.

---

## Step 2: Enable the Google Ads API

1. In the left sidebar: **APIs & Services → Library**
2. Search for "Google Ads API"
3. Click on it → Click **Enable**

**Common mistake:** Enabling "Google Ads" (the general product page) or "AdSense" instead of "Google Ads API" (the developer API). It must say "Google Ads API" exactly.

✅ **Check:** You're on a page titled "Google Ads API" showing a **Manage** button (instead of "Enable").

---

## Step 3: Configure the OAuth Consent Screen

This tells Google what your app is. Even though it's just for you, Google requires it.

Go to **APIs & Services → OAuth consent screen**. (Newer consoles brand this area **"Google Auth Platform"** — same settings, spread across Branding / Audience / Clients pages. The steps below map onto either layout.)

When asked for **User Type**, this is a real fork — pick based on your situation:

### Option A — Internal (pick this if you can)

Available only when your Cloud project belongs to a **Google Workspace organization** AND the Google account you'll authorize with in Step 7 is on that domain.

1. Choose **Internal** → **Create**
2. Fill in: **App name** (e.g., "PPC Tools"), **User support email**, **Developer contact email**
3. Save. Done — skip to Step 4.

Internal apps skip the test-user list, never show the "unverified app" warning, and their refresh tokens **don't expire on a timer**. If the Internal option is greyed out, your project isn't inside a Workspace org — use Option B.

### Option B — External (everyone else: gmail.com accounts, no Workspace)

1. Choose **External** → **Create**
2. Fill in: **App name**, **User support email**, **Developer contact email**
3. **Save and Continue** through the Scopes screen (don't add any scopes)
4. On the **Test Users** step → **+ Add Users** → add your own email → **Save and Continue** → **Back to Dashboard**
5. **Now publish the app:** on the OAuth consent screen page (the "Audience" page in newer consoles), click **Publish App** → confirm pushing to **In production**

**Why publish? This is the step most guides get wrong.** An External app left in "Testing" status gets refresh tokens that **Google expires after 7 days**. Your setup works today, then dies next week with `invalid_grant` — forever, on repeat, until you publish. Publishing now means the token you generate in Step 7 never expires.

Publishing does **not** require Google's verification review for your own use. The console may show "needs verification" notices — ignorable. The only effect you'll see is an "unverified app" warning during authorization, which Step 7 shows you how to click through.

**Common mistake:** Skipping the Test Users step before publishing. Harmless once published, but if you pause the guide here, you'll get "Access blocked" when authorizing.

✅ **Check:** The consent screen page shows your app as **Internal**, or as **External** with publishing status **In production**.

---

## Step 4: Create OAuth Client Credentials

1. **APIs & Services → Credentials**
2. Click **+ Create Credentials → OAuth client ID**
3. Application type: **Desktop app** — this is the most important choice on the page.

   > ⚠️ **Do NOT pick "Web application."** It fails later — when you generate the refresh token — with `redirect_uri_mismatch`. If you already created a Web client, delete it and create a fresh **Desktop app** one.

4. Name: "PPC Tools Desktop" (or whatever you want)
5. Click **Create**
6. A popup shows your Client ID and Client Secret — click **Download JSON**
7. Save the downloaded file as `client_secret.json` in this folder

**Keep this file safe.** It contains your OAuth client credentials. Never commit it to git.

💡 **Lost the file later?** Cloud Console → Credentials → click your OAuth client's name → **Download JSON** (top-right). The client ID never changes; the secret can be rotated if needed.

✅ **Check:** Your new client appears under "OAuth 2.0 Client IDs" with type **Desktop**.

---

## Step 5: Get Your Developer Token

1. Log into Google Ads at [ads.google.com](https://ads.google.com)
2. Navigate to your **MCC account** (the top-level manager account)
3. Click **Admin** (gear icon in the left nav) → **API Center**. (Shortcut: [ads.google.com/aw/apicenter](https://ads.google.com/aw/apicenter). On the older UI: wrench icon "Tools & Settings" → **Setup → API Center**.)
4. Copy your **Developer Token**

**If you don't see API Center:** You may need to apply for API access. Click "Apply for access" — approval can take a few days for new accounts.

**If your token says "Test Account":** That's fine for development. Test tokens can only access test accounts, but you can apply for Basic access once you're ready.

**Note:** The developer token belongs to the MCC, not your personal Google account. One more rule to know: **each Cloud project locks permanently to the first developer token that calls through it** — a project can never switch to a different MCC's token later. (The token itself is reusable from any fresh project.) If you ever hit `DEVELOPER_TOKEN_PROHIBITED`, see Troubleshooting.

✅ **Check:** You have a token string copied (a ~22-character mix of letters, numbers, dashes, underscores).

---

## Step 6: Install Python Dependencies

```bash
pip install google-ads google-auth google-auth-oauthlib google-auth-httplib2 pyyaml
```

✅ **Check:** `python -c "import google.ads.googleads"` runs without error.

---

## Step 7: Generate Your Refresh Token

Run the credential generator script included in this folder:

```bash
python generate_credentials.py --client-secrets client_secret.json
```

The consent screen will ask for three permissions in one go: **Google Ads**, **Google Sheets**, and **Drive (read-only)**. The Ads scope is the API connection itself. The Sheets and Drive-read scopes are there because the skills in this catalog that write reports to Google Sheets (non-serving-keyword-scanner, ads-checker, rsa-refresh, sqr-pipeline, and others) reuse this same refresh token from your `google-ads.yaml` — one token, no second OAuth flow. Scopes are fixed the moment a token is minted, so granting all three now is what makes that work.

1. Your browser opens automatically (the URL also prints in the terminal as a fallback — paste it into a browser yourself if nothing opens)
2. Sign in with the Google account that has Google Ads access
3. **External apps:** you'll see **"Google hasn't verified this app"** — click **Advanced → Go to [your app name] (unsafe)**. This is expected: it's *your own* app, you trust it. (Internal apps skip this screen entirely.)
4. Grant the requested permissions — if Google shows **individual checkboxes** (Ads / Sheets / Drive), **tick all of them**. The script warns you if any were skipped.
5. The terminal shows: `Your refresh token is: 1//0xxxxxxx...`
6. **Copy this token** — you'll need it in the next step

**Common mistake:** Signing in with the wrong Google account. Use the account that has access to the Google Ads MCC, not a personal account.

**Common mistake:** The "unverified app" warning scares people off. Since you created this app yourself, it's safe to continue.

✅ **Check:** The terminal printed a refresh token starting with `1//`, with no missing-permission warning.

> **Did this setup before 2026-07-17?** Your existing token carries only the Ads scope — it keeps working for everything Ads-only, but skills that write to Google Sheets will fail with 403 errors. Re-run this step once (a refresh token can't gain scopes after the fact) and paste the new `refresh_token` into your `google-ads.yaml`. Nothing else in your setup changes.

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

**Where to find your MCC ID:** Log into [ads.google.com](https://ads.google.com) in MCC view — the top-right shows it as `123-456-7890`. Strip the dashes: `1234567890`.

✅ **Check:** All five values filled in, no `YOUR_*` placeholders left, `login_customer_id` has no dashes.

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

✅ **Check:** You see your accounts listed. That's it — the API connection is working, and because of Step 3 it will *stay* working.

---

## Troubleshooting

### "google.auth.exceptions.RefreshError: invalid_grant"
Two causes, in order of likelihood:
1. **Your app is External and still in "Testing" status** — Google expires those refresh tokens after 7 days. Fix it permanently: Cloud Console → OAuth consent screen → **Publish App** (see Step 3, Option B), then re-run Step 7 for a fresh token.
2. The token was revoked (e.g., via your Google account's security page, or a Google Workspace password reset). Re-run Step 7.

### "redirect_uri_mismatch" when generating the refresh token
Your OAuth client is a "Web application" instead of "Desktop app." Go to Credentials, delete that client, create a new one with type **Desktop app** (Step 4), and re-run Step 7.

### "Request had invalid authentication credentials"
Double-check that `client_id`, `client_secret`, and `refresh_token` in your YAML all match (no extra spaces, no missing characters).

### "The developer token is not approved"
New developer tokens need Google approval. Check API Center in your MCC for the approval status. Test tokens work for test accounts only.

### "The developer token is not allowed with the project" (DEVELOPER_TOKEN_PROHIBITED)
Each Cloud project locks permanently to the **first** developer token that makes a call through it. This error means the project you're calling from has already made calls with a *different* MCC's token — common when you reused a project from a tutorial, an old employer, or a previous MCC. Fix: create a **fresh Cloud project** and redo Steps 1–4 in it (new project, enable the API, consent screen, new OAuth client), then regenerate the refresh token (Step 7). Your current developer token works fine from the fresh project — tokens aren't locked to projects, only the reverse.

### "The caller does not have permission" / "USER_PERMISSION_DENIED" / "Customer not found"
One of:
- The Google account you authorized with in Step 7 doesn't have access to this MCC. Check your MCC → Accounts to verify, and confirm which account you signed in with.
- Your `login_customer_id` still has dashes in it. Digits only: `1234567890`.

### A skill's Google Sheets step fails with 403 / "insufficient authentication scopes" (but the connection test passes)
Your refresh token doesn't carry the Sheets scopes. Two causes:
1. **The token predates 2026-07-17**, when this generator started requesting the Sheets + Drive-read scopes alongside Ads. Re-run Step 7 and update `refresh_token` in your YAML.
2. **Consent checkboxes were left unticked.** If Google showed individual permission checkboxes during authorization, all of them must be ticked. Re-run Step 7 and tick everything — the script warns at the end if a permission is missing.

### "ModuleNotFoundError: No module named 'google.ads'"
Run `pip install google-ads` again. If using a virtual environment, make sure it's activated.

### "login_customer_id is required"
Add `login_customer_id` to your YAML file. This should be your MCC's customer ID (digits only, no dashes).

### Wrong Google account keeps getting used
If your browser is signed into multiple Google accounts, OAuth can grab the wrong one. Open an **Incognito/Private window**, sign into only the correct account, and paste the authorization URL from Step 7 there.

### Need to start over completely
Delete the OAuth client (Credentials page → trash icon). Delete the project (IAM & Admin → Settings → **Shut Down**). Redo from Step 1 with a fresh project — your developer token is unaffected and works from the new project (projects lock to a token, never the other way around).

---

## Security Notes

- **Never commit** `google-ads.yaml` or `client_secret.json` to git
- Add both to your `.gitignore`
- Your refresh token grants full access to your Google Ads accounts — plus, with the scopes from Step 7, read/write access to your Google Sheets and read access to your Drive file listing. Treat it like a password
- If you suspect a token is compromised, revoke it at [myaccount.google.com/permissions](https://myaccount.google.com/permissions)

---

## Next Steps

Once your API connection is working:
- Use the [GAQL Query Patterns](../gaql-query-patterns/) skill to start querying your accounts
- Install the [Mutation Safety](../mutation-safety/) skill before making any changes

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
