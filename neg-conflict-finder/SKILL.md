---
name: neg-conflict-finder
description: Find negative keyword conflicts across an MCC. Auto-invoke when user asks "find negative keyword conflicts", "audit negatives across my MCC", "which negatives are blocking my keywords", or wants to identify conflicts between positives and negatives at any level (ad group, campaign, shared list, MCC shared list, account-level).
---

# MCC Negative Keyword Conflict Finder

Identifies every place a negative keyword is blocking a positive keyword you bid on, across all accounts under an MCC, at every level Google supports — ad group, campaign, account-level shared lists, and MCC-level shared lists.

This is an **ADS-SCRIPT skill**: one Google Ads Script (`scripts/mcc-neg-keyword-conflict.js`), pasted into the MCC's Scripts editor and run there. There is no CLI, no local install, and no separate rules/reference files — the judgment layer for reading and resolving its output lives inline below.

## When to Use

- User asks to find or audit negative keyword conflicts
- User suspects old negatives are silently blocking active keywords
- User wants a portfolio-wide negative keyword health check
- User wants to know which positives are being blocked and where the negative lives

## Deliberately Does NOT Do

- **No removals, no mutations.** The script writes rows to a Google Sheet and touches nothing in any account. Resolution is a human in the UI.
- **No query-level analysis.** Detection runs on keyword *text*, not live search queries — the sheet is a floor, not a ceiling (see "What a flag means" below).
- **No paused entities.** Positives and negatives are collected from enabled campaigns/ad groups/criteria only.
- **No PMax / Display / Video.** Search keyword inventory only.
- **No prioritization in the output.** Rows arrive unranked; the triage order below is the operator's judgment layer, not a sheet column.

## What It Does

Runs as a Google Ads Script inside an MCC. For each labeled account it:

1. Pulls all positive keywords (ad group level, enabled only)
2. Pulls all negative keywords from every level Google supports:
   - Ad group negatives
   - Campaign negatives
   - Account-level shared lists
   - MCC-level shared lists (fetched while the manager account is selected, then matched to each child campaign through its `campaign_shared_set` associations)
   - Account-level negative keywords (when the API supports the field path; degrades gracefully when not)
3. Runs blocking detection keyed on the **negative's** match type — the plain-terms semantics are in "How the script decides" below
4. Writes one row to a Google Sheet per conflicting negative, per ad group it blocks keywords in — with the negative, where it lives, and which positive(s) it blocks

**Output Sheet columns:**

| Column | Description |
|--------|-------------|
| Account Name | Google Ads account name |
| Conflicting Negative Keyword | The negative that's blocking (display form: `[exact]`, `"phrase"`, bare broad) |
| Level & Location | Where the negative lives, e.g. `Campaign: Brand - Search`, `Ad Group: Bathroom Remodel (Campaign: Remodel - Search)`, `Shared List: Global Negatives (Applied to Campaign: Services - Search)`, `MCC Shared List: Brand Protection (Applied to Campaign: Services - Search)`, `Account Level` |
| Blocked Positive Keywords | The positive keyword(s) being blocked, comma-separated |

A clean scanned account still gets a row: `NO CONFLICT` in the second column. An account **absent** from the sheet was skipped (spend filter) or errored mid-processing — the run logs say which. Absence is not cleanliness.

## How the Script Decides "Blocked"

The question the script asks for every negative/positive pair: **would this negative stop the positive keyword's own text if it were searched word-for-word?** Only the *negative's* match type picks the test (all comparisons case-insensitive, on normalized text — wrappers, `+` modifiers, and extra spaces stripped):

- **Exact negative** — flags only when the texts are identical. `[reviews]` does **not** flag `[acme reviews]`; `[acme]` flags any positive whose text is exactly `acme`, whatever its match type.
- **Phrase negative** — flags when the negative's words appear inside the positive **in order, as a contiguous whole-word run**. `"acme"` flags `[acme apartments]` (this is the fix the script's v4 changelog describes — an equality check used to miss it). `"acme repair"` does **not** flag `[acme auto repair]` — the words aren't contiguous. Whole-word means `"car"` never flags `carpet cleaning`.
- **Broad negative** — flags when **every** word of the negative appears somewhere in the positive, any order. Broad `diy` flags `"diy bathroom remodel cost"`.

**What a flag means, by the positive's type** (the positive's match type is never consulted for detection, but it sets the damage):

- Blocked **exact** positive → dead. Its one query is blocked.
- Blocked **phrase/broad** positive → at minimum, its own text can no longer get through as a query. A broad positive may still serve on reordered or peripheral queries.

**Floor, not ceiling:** because detection runs on keyword text, a negative can block real traffic to a broad positive without ever appearing in the sheet — phrase-neg `"24 hour"` blocks the query *24 hour emergency plumber* without flagging broad positive `emergency plumber`. Zero rows means no text-level conflicts, not zero blocked queries.

## Reading the Sheet — Triage Order

1. **Blocked exact positives first.** Every one is a fully dead keyword you're deliberately bidding on — and exact positives are usually your most intentional bids.
2. **Brand terms in the blocked column**, at any level. Blocked brand traffic is the most expensive kind.
3. **Shared-list and MCC-shared-list rows.** One negative here blocks across every campaign (or account) the list touches — one fix clears many rows, and one careless removal changes many campaigns. MCC lists have the widest blast radius: coordinate before editing.
4. **Campaign and ad-group singletons last** — smallest blast radius, usually stale leftovers.

Two reading notes:

- **Seemingly duplicate rows are per-ad-group hits.** The same campaign-level (or shared-list, or account-level) negative produces one row per ad group where it blocks something — same negative, same location, different blocked keywords. It's one negative; fix it once and every row clears next run.
- The sheet is **overwritten each run** (one tab, cleared first), so it always shows current state — resolve-and-rerun is the verification loop.

## Shared List vs Campaign Level — Choosing the Fix

Google has no override: a positive can never punch through a negative. So every real conflict has exactly four resolutions — pick by where the negative lives and what job it's doing:

| Fix | When it's right | Blast radius |
|---|---|---|
| Remove the keyword from the shared list | The negative is stale everywhere (old strategy, dead product) | Every campaign in every account applying the list |
| Detach the list from the one campaign | The campaign is a genuine exception to the list's policy | That campaign loses **all** the list's protection, not just this keyword |
| Move the positive to a campaign without the list | The negative is doing its job and the positive is in the wrong place (the brand-routing case below) | One keyword moves; the negative keeps working |
| Keep the negative, drop the positive | The positive was speculative or low-value; the negative protects more than the positive earns | One keyword dies, deliberately |

Campaign-level and ad-group-level negatives are cheap to remove — blast radius is one campaign or one ad group. Shared lists deserve the decision table; MCC shared lists deserve it twice.

**The brand-routing case (why "move the positive" exists):** a generic campaign carries phrase-neg `"acme"` so brand queries route to the Brand campaign. If someone later adds a brand positive like `"acme apartments"` to that generic campaign, it gets flagged — and the negative is *right*. Deleting it would let the generic campaign cannibalize brand traffic. Move the positive to the Brand campaign instead.

## Setup

1. **Open the Google Ads Scripts editor** at the MCC level (Tools → Bulk actions → Scripts in the legacy UI, or Tools → Scripts under the modern MCC UI)
2. **Create a new script** and paste the contents of `scripts/mcc-neg-keyword-conflict.js`
3. **Edit the configuration block** at the top:
   - `ACCOUNT_LABEL` — set to a label you've applied to the accounts you want to process. **Required.** The script only iterates labeled accounts.
   - `SHEET_URL` — optional. Leave blank to have the script create a fresh sheet on each run, or paste an existing Sheet URL to overwrite it. (An unreadable URL doesn't stop the run — the script logs the failure and creates a fresh spreadsheet instead; the log prints where the results actually went.)
   - `REQUIRE_RECENT_SPEND` — optional spend filter (default `true`). Skips accounts with no spend in the last 7 days. Set to `false` to process every labeled account.
4. **Authorize the script** when Google prompts (first run only)
5. **Run** — manually first, then schedule daily/weekly under Frequency

## Run the Script

There are no CLI commands — this is a Google Ads Script. After pasting and configuring:

1. Click **Preview** to check authorization and config. Note: Ads Scripts preview only suppresses *account* changes — this script makes none anyway — so **the Sheet write still happens in preview**, including the tab clear. Leave `SHEET_URL` blank (fresh spreadsheet) or point it somewhere disposable for the first run.
2. Click **Run** to execute fully
3. Open the linked Sheet (URL is printed at the end of the logs) to review conflicts
4. Set a Frequency (Daily, Weekly, etc.) for ongoing monitoring

## Worked Read

Four accounts labeled `kw-conflict-audit`; spend filter on. The sheet after the run:

| Account Name | Conflicting Negative Keyword | Level & Location | Blocked Positive Keywords |
|---|---|---|---|
| Acme Co | "acme" | MCC Shared List: Brand Protection (Applied to Campaign: Services - Search) | [acme apartments], "acme apartments reviews" |
| Beta LLC | diy | Campaign: Bathroom Remodel - Search | "diy bathroom remodel cost", "diy shower installation" |
| Beta LLC | diy | Campaign: Bathroom Remodel - Search | "diy tile ideas" |
| Gearline Auto Repair | NO CONFLICT | | |

- **Row 1** is the brand-routing case at MCC blast radius: the manager-owned Brand Protection list negates `"acme"` across generic campaigns, and someone added brand positives — including an exact `[acme apartments]`, fully dead — to Services - Search. Triage rank #1 (blocked exact + brand). Fix: move the brand positives to the Brand campaign; the list is doing its job.
- **Rows 2–3** are one negative, not two: the same campaign-level broad `diy`, hit from two ad groups. Beta LLC now *bids* on DIY-cost content terms, so the old anti-DIY negative is stale — remove it once (Campaign → Bathroom Remodel - Search → negative keywords) and both rows clear next run.
- **Row 4**: Gearline scanned clean. The fourth labeled account (Tolliver HVAC) is absent — the logs show why:

```
Skipping Tolliver HVAC (ID: 456-789-0123) -- spend 0 <= 0 over LAST_7_DAYS.
```

Log excerpt for one account, with the two lines newcomers misread:

```
--- Processing Account: Acme Co (ID: 123-456-7890) ---
Fetching positive and ad group negative keywords...
Running sample keyword query for structure check...
Sample Row (Keyword View): {…}
Finished processing 412 positive/ad group negative keywords for 6 campaigns. (Fetch Duration: 3.90s)
Fetching campaign negative keywords...
Running sample campaign negative query for structure check...
Sample Row (Campaign Criterion): {…}
Finished processing 38 campaign negatives. (Fetch Duration: 1.12s)
Fetching shared negative keyword lists and associations...
Processing shared negative lists and their keywords...
Finished processing 0 keywords across 1 shared lists. (Fetch Duration: 0.84s)
Fetching campaign associations for shared lists...
Finished processing 2 campaign-shared list associations. (Fetch Duration: 0.51s)
Fetching account-level negative keywords...
Processing account-level negative keywords...
Warning: fetchAccountNegatives threw (...). Skipping account-level negatives for this account; ad-group, campaign, and shared-list conflicts will still be detected.
Starting conflict analysis for the current account...
Conflict analysis complete for current account. Found 1 potential conflicts. (Analysis Duration: 0.06s)
Found 1 conflicts in account Acme Co.
Successfully wrote 1 conflicts to the sheet.
--- Finished Processing Account: Acme Co (Duration: 9.84 seconds) ---
```

(Each `Sample Row` line is followed by per-field `Sample …` structure dumps, trimmed
here — `{…}` stands in for the raw JSON the script logs.)

- `0 keywords across 1 shared lists` is **normal, not a failure**: MCC-owned lists are cached once up front, so the per-account pass counts only account-owned list keywords — the denominator includes the MCC list, the numerator doesn't re-process it.
- The `fetchAccountNegatives threw` warning is the **expected, documented degradation**: Google's runtime currently rejects the account-level negative keyword fields, the script continues, and every other level still detects (see Limitations). It is not the reason an account would be missing from the sheet.

## How to Resolve Conflicts

The script identifies — it doesn't remove. Resolution is manual review (intentionally — automated removal of negatives is high-risk). For each row, run the decision table above, then find the negative at the level shown in `Level & Location`:

- Ad group level → Ad Group → Negative Keywords tab
- Campaign level → Campaign → Negative Keywords tab
- Shared list → Tools → Shared Library → Negative keyword lists → [list name]
- MCC shared list → MCC level → Tools → Shared Library

If the conflicting negative came from a search-query pipeline upload, remove it through that pipeline (so its records stay true) — see the routing table below.

## Limitations

- **Search campaigns only.** Performance Max, Display, and Video campaigns don't use traditional negatives the same way.
- **Enabled keywords only.** Paused positives won't show as blocked.
- **Text-level detection only.** Query-level partial blocks of broad positives don't appear (the floor-not-ceiling note above).
- **Account-level negatives may be skipped** if Google's `customer_negative_criterion` API rejects the keyword field path. Other levels still detect normally — the script logs a warning and continues.
- **A campaign with no enabled ad-group keywords is invisible** — its campaign negatives are ignored for conflict checks (there's nothing they could block; the log notes each one).
- **Read-only.** The script writes to a Sheet but never modifies any account. Review and remove negatives in the UI yourself.

## What NOT to Do

- Do NOT remove a negative just because it shows up as a conflict. Some conflicts are structural-by-design — the brand-routing case above flags a *correct* negative; the fix is moving the positive, not deleting the router.
- Do NOT auto-remove negatives based on this output without reviewing each one.
- Do NOT run on every account in the MCC at once. Use the label filter — narrow to a portfolio or service tier first (Ads Scripts executions are time-limited; serial account processing on a huge label set risks an incomplete run).
- Do NOT treat a missing account as a clean account. `NO CONFLICT` means scanned clean; absence means skipped or errored — check the logs.

## When to Load Other Skills

| Skill | When |
|---|---|
| [sqr-pipeline](../sqr-pipeline/) | The conflicting negative came from an SQR upload and should go — its remove branch un-negates with preview/approve, keeping the pipeline's records true |
| [add-account-negative-keywords](../add-account-negative-keywords/) | The conflict lives in an account-level SharedSet that skill manages — and run this finder after every baseline roll it performs |
| [non-serving-keyword-scanner](../non-serving-keyword-scanner/) | You want the blocked positive's serving history — its 180-day view shows whether the keyword ever served or has been suppressed all along |
| [account-diagnostic](../account-diagnostic/) | This finder is the deep-dive behind its check 36 (negatives blocking active keywords); run the full diagnostic when conflicts turn out to be one symptom of a messier account |
