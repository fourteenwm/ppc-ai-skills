---
name: rsa-bulk-edit
description: Find and replace text across RSA ads at scale, outputting to Google Sheet in Google Ads Editor format for review before manual import. Auto-invoke when user says "RSA bulk edit", "find and replace in RSA ads", "edit RSA ads at scale", or "bulk RSA changes". Supports single account, multiple CIDs, dry-run preview, and case-sensitive matching.
allowed-tools: [Bash, Read]
---

# RSA Bulk Edit Skill

Find and replace text across RSA ads, outputting to Google Sheet in Google Ads Editor format.

## Auto-Invocation Triggers

- "RSA bulk edit"
- "find and replace in RSA ads"
- "edit RSA ads at scale"
- "bulk RSA changes"

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
  --cids "123456789,987654321,456789123" \
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
| `--cid` | One of cid/cids | Single customer ID (no dashes) |
| `--cids` | One of cid/cids | Comma-separated customer IDs |
| `--search` | Yes | Text to find |
| `--replace` | Yes | Replacement text |
| `--sheet-id` | No | Google Sheet ID for output |
| `--tab-name` | No | Tab name (default: RSA Edits) |
| `--case-sensitive` | No | Enable case-sensitive matching |
| `--dry-run` | No | Preview only, no sheet write |

## Output Format (Google Ads Editor Ready)

One row per ad, copy-paste ready for Google Ads Editor:

| Columns A-D | E-S | T-W | X-Z | AA-AC |
|-------------|-----|-----|-----|-------|
| Account Name, Customer ID, Campaign, Ad Group | Headline 1-15 | Description 1-4 | Path 1, Path 2, Final URL | Has Match, Changes Made, Ad ID |

## Post-Script Workflow

1. Review sheet, filter by "Has Match" = YES
2. Copy columns C onwards (Campaign through Final URL)
3. Paste into Google Ads Editor
4. Review changes in Editor
5. Post changes

## Scope

- Queries all ad groups (enabled or paused) in ENABLED campaigns
- Only includes ENABLED ads
- Case-insensitive search by default

## Examples

### UK Spelling Corrections

```bash
# Color -> Colour
python scripts/rsa_bulk_edit.py \
  --cids "111222333,444555666" \
  --search "color" \
  --replace "colour" \
  --sheet-id 1ABC123xyz

# Center -> Centre
python scripts/rsa_bulk_edit.py \
  --cids "111222333,444555666" \
  --search "center" \
  --replace "centre" \
  --sheet-id 1ABC123xyz
```

### Customizer Replacement

```bash
python scripts/rsa_bulk_edit.py \
  --cid 1234567890 \
  --search "{CUSTOMIZER.Price}" \
  --replace "Contact For Rent Pricing" \
  --sheet-id YOUR_SHEET_ID \
  --tab-name "RSA - QA"
```
