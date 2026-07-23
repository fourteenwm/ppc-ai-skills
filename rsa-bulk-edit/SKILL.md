---
name: rsa-bulk-edit
description: Find and replace text across RSA ads at scale, outputting to Google Sheet in Google Ads Editor format for review before manual import. Auto-invoke when user says "RSA bulk edit", "find and replace in RSA ads", "edit RSA ads at scale", or "bulk RSA changes". Supports single account, multiple CIDs, dry-run preview, and case-sensitive matching.
allowed-tools: [Bash, Read]
---

# RSA Bulk Edit Skill

Find-and-replace **literal text** across RSA ads in one or more accounts,
outputting a Google Ads Editor-ready review sheet. One operator owns the
workflow end to end: scope the swap → dry-run → sheet → the review
checklist in [`rules.md`](rules.md) (length audit, casing scan, collateral
read) → per-account Editor paste → post.

The tool is deliberately dumb: it moves text you already decided on. If the
change needs judgment about meaning or new copy, it's not bulk work —
`rules.md` has the boundary table.

## Auto-Invocation Triggers

- "RSA bulk edit"
- "find and replace in RSA ads"
- "edit RSA ads at scale"
- "bulk RSA changes"

## Prerequisites

- **`google-ads.yaml`** at project root — see the [google-ads-api-setup](../google-ads-api-setup/) skill if you don't have one. The `--sheet-id` output step reuses this same file's OAuth credentials for the Sheets API — its refresh token must carry the `spreadsheets` scope, which the setup skill's generator grants by default (token predates that? re-run the generator once)
- **Run from the directory holding `google-ads.yaml`** — the script loads it by literal filename; there is no `--config` flag
- Python packages: `pip install google-ads gspread google-auth pyyaml`

## Usage

### Single Account

```bash
python scripts/rsa_bulk_edit.py \
  --cid 1234567890 \
  --search "color" \
  --replace "colour" \
  --sheet-id YOUR_SHEET_ID
```

### Multiple Accounts

```bash
python scripts/rsa_bulk_edit.py \
  --cids "1234567890,2345678901,3456789012" \
  --search "color" \
  --replace "colour" \
  --sheet-id YOUR_SHEET_ID
```

### Custom Tab Name

```bash
python scripts/rsa_bulk_edit.py \
  --cid 1234567890 \
  --search "color" \
  --replace "colour" \
  --sheet-id YOUR_SHEET_ID \
  --tab-name "RSA - QA"
```

### Dry Run (Preview Only)

```bash
python scripts/rsa_bulk_edit.py \
  --cid 1234567890 \
  --search "color" \
  --replace "colour" \
  --dry-run
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--cid` | At least one of cid/cids (both combine) | Single customer ID (dashes stripped) |
| `--cids` | At least one of cid/cids (both combine) | Comma-separated customer IDs |
| `--search` | Yes | Literal text to find (substring match — no regex, no word boundaries) |
| `--replace` | Yes | Replacement text, inserted exactly as typed (`""` = delete) |
| `--sheet-id` | No | Google Sheet ID for output |
| `--tab-name` | No | Tab name (default: RSA Edits) |
| `--case-sensitive` | No | Enable case-sensitive matching |
| `--dry-run` | No | Console preview only (first 10 matches), no sheet write |

Match semantics, the sheet's exact column layout, and every run mode:
[`references/edit-contract.md`](references/edit-contract.md). Scope in one
line: ENABLED RSAs in ENABLED campaigns (any ad-group status), searching
**headlines and descriptions only** — paths and final URLs are carried to
the sheet but never edited.

## Post-Script Workflow

1. Review sheet, filter by "Has Match" = YES
2. **Run the `rules.md` checklist** — length audit (the script writes
   over-limit text unflagged), casing scan, collateral read
3. Filter to ONE account; copy columns C onwards (Campaign through Final URL)
4. Paste into Google Ads Editor with that account open
5. Review changes in Editor's preview (pasted rows carry no ad identity)
6. Post changes; repeat per account

## What this skill deliberately does NOT do

- **No API mutations, ever.** The only write is the review sheet; text
  reaches Google Ads solely through your Editor paste-and-post.
- **No copy generation.** Literal replacement only. Rewriting weak copy is
  [`rsa-refresh`](../rsa-refresh/); net-new ad sets are
  [`rsa-single-account`](../rsa-single-account/).
- **No validation.** No length checks, no casing adaptation, no meaning
  checks — the `rules.md` review checklist is the validation layer, by
  design in front of a human.
- **No paths or extensions.** Headlines 1–15 and Descriptions 1–4 are the
  only searched fields.

## Files in this skill

| File | Purpose |
|------|---------|
| `SKILL.md` | This file — workflow + routing |
| `README.md` | Zero-context setup: install, prerequisites, first run |
| `rules.md` | Judgment layer: when bulk is wrong, pre-flight, review checklist, false alarms |
| `examples.md` | Worked reads: a rebrand with catches, substring collateral, the ask that isn't bulk work |
| `references/edit-contract.md` | Exact match semantics, sheet columns, run modes, Editor-paste contract |
| `scripts/rsa_bulk_edit.py` | The engine: GAQL query → find/replace → sheet write |

The output tab lives in a sheet you own — no runtime data in this folder.

## When to load a sibling skill

| Situation | Load |
|---|---|
| The "edit" changes meaning or quality — rewriting LOW performers, tone work, per-context judgment | [`rsa-refresh`](../rsa-refresh/) |
| A full RSA set for an account from scratch | [`rsa-single-account`](../rsa-single-account/) |
| Replacement text introduces any claim (services, hours, credentials) | [`ad-copy-verification-standard`](../ad-copy-verification-standard/) — verify before running the swap |
| The task turns out to be writing new copy into slots | [`ad-copy-generation-framework`](../ad-copy-generation-framework/) |
| Confirming what actually changed in the account after an Editor post | [`change-history-checker`](../change-history-checker/) |
| No `google-ads.yaml` yet | [`google-ads-api-setup`](../google-ads-api-setup/) |

## Examples

### UK Spelling Corrections

```bash
# Color -> Colour
python scripts/rsa_bulk_edit.py \
  --cids "1234567890,2345678901" \
  --search "color" \
  --replace "colour" \
  --sheet-id YOUR_SHEET_ID

# Center -> Centre
python scripts/rsa_bulk_edit.py \
  --cids "1234567890,2345678901" \
  --search "center" \
  --replace "centre" \
  --sheet-id YOUR_SHEET_ID
```

Title-Case portfolios: run case-sensitive passes per casing variant
(`Color`→`Colour`, then `color`→`colour`) — the replacement is inserted
exactly as typed (`rules.md` pre-flight #3).

### Customizer Replacement

```bash
python scripts/rsa_bulk_edit.py \
  --cid 1234567890 \
  --search "{CUSTOMIZER.Price}" \
  --replace "Contact For Rent Pricing" \
  --sheet-id YOUR_SHEET_ID \
  --tab-name "RSA - QA"
```

Search the **whole token** — matching text inside the braces corrupts the
customizer instead of retiring it.

## Safety

Read-only against Google Ads — one GAQL SELECT per account, and the only
write is the review tab in a sheet you own. Nothing changes in any account
until a human reviews and posts through Google Ads Editor.
