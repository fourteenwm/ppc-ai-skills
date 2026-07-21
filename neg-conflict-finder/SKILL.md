---
name: neg-conflict-finder
description: Find negative keyword conflicts across an MCC. Auto-invoke when user asks "find negative keyword conflicts", "audit negatives across my MCC", "which negatives are blocking my keywords", or wants to identify conflicts between positives and negatives at any level (ad group, campaign, shared list, MCC shared list, account-level).
---

# MCC Negative Keyword Conflict Finder

Identifies every place a negative keyword is blocking a positive keyword you bid on, across all accounts under an MCC, at every level Google supports — ad group, campaign, account-level shared lists, and MCC-level shared lists.

## When to Use

- User asks to find or audit negative keyword conflicts
- User suspects old negatives are silently blocking active keywords
- User wants a portfolio-wide negative keyword health check
- User wants to know which positives are being blocked and where the negative lives

## What It Does

Runs as a Google Ads Script inside an MCC. For each labeled account it:

1. Pulls all positive keywords (ad group level, enabled only)
2. Pulls all negative keywords from every level Google supports:
   - Ad group negatives
   - Campaign negatives
   - Account-level shared lists
   - MCC-level shared lists (applied via `customer.managerCustomer`)
   - Account-level negative keywords (when the API supports the field path; degrades gracefully when not)
3. Runs match-type-aware blocking detection (broad blocks broad/phrase/exact, phrase blocks phrase/exact via subsequence match, exact blocks exact only)
4. Writes one row per conflict to a Google Sheet, with the conflicting negative, where it lives, and which positive(s) it blocks

**Output Sheet columns:**

| Column | Description |
|--------|-------------|
| Account Name | Google Ads account name |
| Conflicting Negative Keyword | The negative that's blocking |
| Level & Location | Where the negative lives (e.g., "Shared List: Global Negatives", "Campaign: Brand - Search") |
| Blocked Positive Keywords | The positive keyword(s) being blocked |

## Setup

1. **Open the Google Ads Scripts editor** at the MCC level (Tools → Bulk actions → Scripts in the legacy UI, or Tools → Scripts under the modern MCC UI)
2. **Create a new script** and paste the contents of `scripts/mcc-neg-keyword-conflict.js`
3. **Edit the configuration block** at the top:
   - `ACCOUNT_LABEL` — set to a label you've applied to the accounts you want to process. **Required.** The script only iterates labeled accounts.
   - `SHEET_URL` — optional. Leave blank to have the script create a fresh sheet on each run, or paste an existing Sheet URL to overwrite it.
   - `REQUIRE_RECENT_SPEND` — optional spend filter (default `true`). Skips accounts with no spend in the last 7 days. Set to `false` to process every labeled account.
4. **Authorize the script** when Google prompts (first run only)
5. **Run** — manually first, then schedule daily/weekly under Frequency

## Run the Script

There are no CLI commands — this is a Google Ads Script. After pasting and configuring:

1. Click **Preview** to check authorization and config without writing rows
2. Click **Run** to execute fully
3. Open the linked Sheet to review conflicts
4. Set a Frequency (Daily, Weekly, etc.) for ongoing monitoring

## How to Resolve Conflicts

The script identifies — it doesn't remove. Resolution is manual review (intentionally — automated removal of negatives is high-risk). For each row:

1. **Read the negative + the positive(s) it blocks.** If the negative is doing real work (blocking off-brand traffic), keep it and let the positive die.
2. **If the positive is intentional, remove the negative.** Find it at the level shown in `Level & Location`:
   - Ad group level → Ad Group → Negative Keywords tab
   - Campaign level → Campaign → Negative Keywords tab
   - Shared list → Tools → Shared Library → Negative keyword lists → [list name]
   - MCC shared list → MCC level → Tools → Shared Library
3. **If neither — kill the conflicting negative.** Often these are old negatives from a campaign that doesn't exist anymore.

## Limitations

- **Search campaigns only.** Performance Max, Display, and Video campaigns don't use traditional negatives the same way.
- **Enabled keywords only.** Paused positives won't show as blocked.
- **Account-level negatives may be skipped** if Google's `customer_negative_criterion` API rejects the keyword field path. Other levels still detect normally — the script logs a warning and continues.
- **Read-only.** The script writes to a Sheet but never modifies any account. Review and remove negatives in the UI yourself.

## What NOT to Do

- Do NOT remove a negative just because it shows up as a conflict. Some conflicts are intentional (a brand campaign with `[brand_name]` as positive and `brand_name reviews` as negative is a deliberate split, not a bug).
- Do NOT auto-remove negatives based on this output without reviewing each one.
- Do NOT run on every account in the MCC at once. Use the label filter — narrow to a portfolio or service tier first.
