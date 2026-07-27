# Audit Contract — what `audit_pmax_asset_automation.py` actually does

> **Source of truth:** `scripts/audit_pmax_asset_automation.py`. Every claim
> below is derived from that file; if the script changes, this contract and
> the CHANGELOG must change with it. Line references point at the script.

## The five settings, and what ON means

The audit checks exactly these five campaign-level asset-automation types
(`:44-50`), printed with these descriptions in this order:

| API setting | Printed as | Google's behavior when OPTED_IN |
|---|---|---|
| `TEXT_ASSET_AUTOMATION` | Auto-created text (headlines/descriptions) | Generates new headlines/descriptions it predicts will perform |
| `FINAL_URL_EXPANSION_TEXT_ASSET_AUTOMATION` | Final URL expansion | Sends traffic to pages you didn't select, with matching auto-copy |
| `GENERATE_ENHANCED_YOUTUBE_VIDEOS` | Auto-created videos | Trims, remixes, or generates YouTube video variants |
| `GENERATE_IMAGE_ENHANCEMENT` | Auto image enhancement (cropping) | Auto-crops images into new aspect ratios |
| `GENERATE_IMAGE_EXTRACTION` | Auto image extraction from URLs | Pulls images off your landing pages into new ad assets |

**Fixed scope:** the override loop keeps only types in that dict (`:113`) —
any automation type Google adds later is invisible to this audit until the
list is extended. Which of the five matters most, and when ON is legitimate:
[rules.md](../rules.md).

## Campaign selection

- `PERFORMANCE_MAX` channel type, **status IN ('ENABLED', 'PAUSED')**
  (`:88`) — REMOVED campaigns are excluded; **paused campaigns ARE audited**
  and count toward compliance totals. A paused campaign's ON settings only
  bite when it re-enables — but they are already on the report.
- Campaigns print in name order (API-side `ORDER BY campaign.name`, `:89`).

## The seeded-default mechanic (read this before trusting OPTED_IN)

For every campaign, all five settings are first **seeded to `OPTED_IN`**
(`:106-107`) — because that is Google's default — and then overwritten by
whatever settings the API response actually carries (`:110-113`).
Consequence: a setting the response omits entirely and a setting someone
explicitly switched ON print **identically** as `OPTED_IN`. The report
cannot distinguish "configured on" from "never configured"; change-history
attribution can (see rules.md's escalation ladder).

Compliance is a strict string test: `status == "OPTED_OUT"` gets `[OK]`,
anything else gets `[!]` and prints its literal enum name (`:148-154`) — an
`UNSPECIFIED` or unknown status counts non-compliant, visibly.

## Account resolution and CID handling

- `--cid` — dash-stripped for the query, but the display name keeps your
  typing (`:194`): `--cid 123-456-7890` reports as `ACCOUNT: CID 123-456-7890`
  over `CID: 1234567890`.
- `--cids` — each entry stripped for both query and display name (`:197`).
  **No dedup:** the same CID listed twice is audited twice and double-counts
  in every total.
- `--all` — reads `login_customer_id` from the credentials yaml **directly**
  (`:53-62`; missing → `ERROR: login_customer_id not set in <path> — cannot
  use --all`, exit 1), then walks ENABLED, non-manager client accounts in
  name order (`:64-73`). Only `--all` shows real account names (the API's
  `descriptive_name`); `--cid`/`--cids` accounts display as `CID <n>` — so
  summary lines like `- CID 1234567890 (1234567890)` are the name-derivation
  rule, not a bug.
- No selection flag at all → help text + three usage examples, exit 1
  (`:177-184`).
- `--config <path>` points both the API client (`:186`) **and** the `--all`
  yaml read (`:191`) at the same credentials file; default `./google-ads.yaml`.

## Error isolation — and the false-compliance trap

A `GoogleAdsException` on one account prints one line and drops the account
(`:118-122`, `:212-213`):

```
  ERROR querying account 2345678901: <first error message>
```

- The errored account produces **no account block** and contributes nothing
  to the settings totals or the needs-attention list.
- It **still counts in `Total accounts audited:`** (`:228` — the line
  reports the input list length, not successes).
- `All accounts fully compliant!` prints whenever the needs-attention list
  is empty (`:239`) — which an *unaudited* account cannot join. The error
  line is the ONLY trace. Count account blocks against the audited total
  before certifying a portfolio (rules.md, triage step 1).

Distinct failure shapes: a missing/unreadable credentials file kills ANY
run mode at client load (`:186` runs before mode handling — unhandled
traceback, no audit output); `--all` with a yaml that loads but lacks
`login_customer_id` exits cleanly with the ERROR line above. Only
per-account `GoogleAdsException`s skip-and-continue; any other exception
type propagates and ends the run.

## Vacuous compliance

An account with zero PMax campaigns prints `  No PMAX campaigns found`
(`:133`) and contributes **0/0** — it can never appear in the
needs-attention list, and a portfolio of such accounts still ends
`All accounts fully compliant!`. "No campaigns in scope" and "audited clean"
are different facts; the per-account blocks tell you which one you have.

## Console anatomy (all emitted verbatim)

Separators are exactly 80 `=` characters. Shapes:

```
================================================================================
PERFORMANCE MAX ASSET AUTOMATION AUDIT
================================================================================
Accounts to audit: 3
================================================================================
```

(`--all` additionally prints `Listing all accounts under MCC...` and
`Found N accounts to audit` *above* this header, `:189-192`.)

Per account (`:127-163`):

```
================================================================================
ACCOUNT: CID 1234567890
CID: 1234567890
================================================================================

  Campaign: Pmax: Sample
  Status: ENABLED
  Asset Automation Settings:
    [OK] Auto-created text (headlines/descriptions): OPTED_OUT
    [!] Final URL expansion: OPTED_IN
    ...
  -> NEEDS ATTENTION (3/5 opted out)
```

Fully compliant campaigns end `-> FULLY COMPLIANT (5/5)` (`:161`). Summary
(`:224-241`): audited/checked/compliant/non-compliant counts, then either
the needs-attention list — one line per account,
`  - <name> (<cid>): <n>/<m> (<p>%)` with the percentage rounded to whole
digits (`:236-237`) — or `All accounts fully compliant!`.

## Run state and artifacts

The script writes **nothing to disk** — console only (the sole `open()` in
the file is the read of the credentials yaml). A cold session cannot tell
from the filesystem that an audit ran; redirect stdout
(`... --all > pmax-audit-$(date +%Y%m%d).txt`) when you need a durable
record, e.g. as the before/after pair around a fix.

## What this skill ships vs what it describes

The **audit is shipped code**; the **fix is a documented pattern**
(SKILL.md § "How to Fix via the API") — a `CampaignService.mutate_campaigns`
update on `asset_automation_settings`, run under
[mutation-safety](../../mutation-safety/) discipline. There is no fix script
in this folder; nothing here can modify an account.
