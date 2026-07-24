# Mutation Contract — exactly what `fix_dgen_ad_automation.py` selects, hashes, and changes

> **Source of truth:** `scripts/fix_dgen_ad_automation.py` wins wherever this
> file and the script disagree — the contract documents shipped behavior, it
> doesn't define it. Revised 2026-07-24; update this file and the CHANGELOG
> together whenever the script changes.

## The settings taxonomy

| Ad type | Settings controlled | Google's default |
|---|---|---|
| `DEMAND_GEN_MULTI_ASSET_AD` | `GENERATE_DESIGN_VERSIONS_FOR_IMAGES` (adds design elements to images), `GENERATE_VIDEOS_FROM_OTHER_ASSETS` (generates videos from images/text) | ON |
| `DEMAND_GEN_VIDEO_RESPONSIVE_AD` | `GENERATE_VERTICAL_YOUTUBE_VIDEOS` (horizontal→vertical), `GENERATE_SHORTER_YOUTUBE_VIDEOS` (shortens videos), `GENERATE_LANDING_PAGE_PREVIEW` (landing-page screenshot in ads) | ON, ON, **OFF** |
| `DEMAND_GEN_CAROUSEL_AD`, `DEMAND_GEN_PRODUCT_AD` | none — skipped | — |

`GENERATE_LANDING_PAGE_PREVIEW` defaulting OFF matters at read time: seeing
it in a dry-run diff means someone or something turned it ON — or the API
response simply omitted the row, since absent settings are seeded `OPTED_IN`
(selection, below) and print the identical `OPTED_IN -> OPTED_OUT` line; the
change-history attribution step is what separates the two
([`rules.md`](../rules.md), reading the diff).

## Selection — which ads enter the pending set

Query filter: Demand Gen channel + **campaign status ENABLED** + **ad status
ENABLED** + campaign end date today-or-later (campaigns with no end date
pass via the API's far-future sentinel; ended campaigns drop out).

- **Ad-group status is NOT checked.** An enabled ad inside a *paused ad
  group* of an enabled campaign IS selected and mutated. Harmless — the
  settings ride the ad, serving or not — but it can make the diff bigger
  than the "active ads" you had in mind.
- **Paused campaigns and paused ads are invisible** to every run. Re-enable
  one later and it arrives with whatever automation settings it always had —
  re-run the fix after re-enabling (rules, cadence).
- An ad's settings default to `OPTED_IN` when absent from the API response;
  anything not already `OPTED_OUT` queues as a fix. Carousel/Product ads
  never queue (no settings exist).
- **Per-account query errors drop the account from the run.** `ERROR
  querying account {cid}: …` prints, the batch continues, and that account
  contributes nothing to the pending set OR the approval code. See the
  false-compliance trap below.
- **CIDs are used exactly as typed — no dash-stripping** (unlike most
  sibling scripts' flags). `--cid 123-456-7890` reaches the API dashed,
  fails the account query, and the run proceeds as if that account had
  nothing to fix.

**The false-compliance trap** (the two bullets above combined): a run whose
only account errors out prints the per-account `ERROR …` line and then
`All accounts are compliant - no changes needed!` — a summary computed over
zero audited ads. Always read per-account error lines before believing the
compliant summary.

## The approval code

`APPROVE-` + the first 8 hex chars (uppercase) of a SHA-256 over the sorted
`cid|ad_id|sorted-settings-to-fix` lines of the entire pending set.

- **Deterministic, stateless.** Same pending work → same code, on any
  machine, with no state file. The code encodes WHAT will change, not when
  or who asked.
- **Recomputed from current account state at execute time.** The provided
  code must equal the recomputed one, else the run refuses (exit 1, printing
  `Provided:` / `Expected:`). ANY drift breaks it: a new ad launched,
  Google re-enabling a setting, someone else fixing one ad, an account
  dropping out on an error, or a different account list on the execute
  command. There is no partial execution — a mismatch means re-run the
  dry-run and **re-read the new diff** (the delta between the two dry-runs
  is itself information).
- A stale code against a now-compliant account never gets validated — the
  run exits at `All accounts are compliant` before the code check. Clean
  exit, not an error.

## Dry-run vs execute

**Dry-run (no code argument):** per-account report blocks always print —
compliant accounts show `No DGen ads need fixing (all compliant or no DGen
campaigns)`. Each pending ad prints campaign, ad group, ad type, and
per-setting `{current} -> OPTED_OUT` lines. The SUMMARY counts accounts
with changes, ads, and individual settings. Then the `APPROVAL CODE:` block
with the exact re-run command echoed. **Nothing is written to disk on a
dry-run — no log, no state.**

**Execute (code argument present):** after validation, one
`mutate_ad_group_ads` call per account — **all-or-nothing within an
account** (a failed call prints `ERROR executing mutation: …` + `Failed`,
logs `success: false`, and the batch continues to the next account). Each
operation sets **every applicable setting** for the ad type to `OPTED_OUT`
with a field mask on `ad_group_ad_asset_automation_settings` — required,
because the API replaces the whole list: updating only one setting would
silently reset the unspecified ones to their `OPTED_IN` defaults. Any
tooling you write against this field must do the same.

Counters at the end: `Successfully updated: N ads` counts API results;
`Failed: N ads` counts the ads of failed accounts (ads, not settings).

## Account resolution

- `--cid` / `--cids`: used verbatim (names display as `Account {cid}` —
  the script never looks up display names for explicit CIDs).
- `--all`: reads `login_customer_id` from the config (missing → hard exit),
  walks `customer_client` for **ENABLED non-manager** accounts with their
  display names. A walk failure is a hard exit (unlike per-account errors).
- Missing config file: `ERROR: Google Ads credentials not found at {path}`
  + a pointer to `google-ads-api-setup`, exit 1.

## Logging

- **Local JSONL — always on for executes:** every per-account attempt
  (success AND failure) appends one line to
  `{--log-dir}/mutations_log.jsonl` (default `./logs/`, auto-created):
  `timestamp_utc`, `approval_code`, `account_cid`, `account_name`,
  `action_type: "DISABLE_DGEN_AUTOMATION"`, `details` (`ads_updated`,
  `settings_changed` list, `ad_types`), `success`, `error`.
- **Google Sheet — opt-in** (`--log-sheet-id`): appends a row (A:H —
  Timestamp | Account | CID | Action Type | Details | Success | Error |
  Approval Code) using the **refresh token inside your `google-ads.yaml`**,
  which must carry the spreadsheets scope (the `google-ads-api-setup`
  generator's default token does). Any sheet failure prints
  `Warning: Could not log to Google Sheet: …` and the run continues —
  **a sheet-log warning never means the mutation failed** (the JSONL row is
  the authority).

## `--verify`

An **execute-mode rider, single-account only** — it re-queries after
mutations and reports `All N DGen ads are now compliant`, or lists
non-compliant campaigns with their offending settings, or `No DGen ads
found`. Three no-op cases to know — two silent, one noted:

1. Dry-run + `--verify`: ignored (the run returns before verification).
2. Already-compliant account + `--verify`: ignored (same early return).
3. Multi-account execute + `--verify`: prints `Note: --verify runs on
   single-account invocations only.`

"Single-account" means the *resolved* list has one entry — `--all` against
an MCC that resolves to one account also qualifies. Verification covers ALL
in-scope ads, not just the ones this run touched. To check compliance
WITHOUT mutating, don't use `--verify` — run a dry-run and read
`No DGen ads need fixing`.

## Reading run state cold

`mutations_log.jsonl` is the durable record — append-only across runs, one
line per account per execute. No JSONL row = no mutation happened through
this script (dry-runs leave zero disk trace by design). The API-side record
is the account's change history
([`change-history-checker`](../../change-history-checker/) inside its windows,
the UI beyond them).
