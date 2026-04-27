---
name: sqr-upload
description: Upload approved negative keywords from a Google Sheet "Uploader" tab to Google Ads shared negative keyword lists. Auto-invoke when user says "upload negatives", "run sqr upload", "upload search queries", or "sqr uploader". Two-step mutation safety — always dry-run first, execute only with deterministic approval code.
allowed-tools: [Bash, Read]
---

# SQR Upload — Negative Keyword Uploader

Upload approved negative keywords from a Google Sheet Uploader tab to shared negative keyword lists via the Google Ads API. Downstream step of the SQR Pipeline (after classification in [`offbrand-analyzer`](../offbrand-analyzer/) and conflict checking in [`geo-conflict-analyzer`](../geo-conflict-analyzer/)).

---

## Triggers

- "upload negatives"
- "run sqr upload"
- "upload search queries"
- "sqr uploader"

---

## What It Does

1. Reads the **Uploader** tab from a Google Sheet
2. Filters rows where **Query** (col B) is non-empty AND **Uploaded** (col E) is empty
3. Groups pending keywords by account (**Trunc CID**, col D)
4. **Dry-run:** shows preview + prints a deterministic **APPROVAL CODE**
5. **Execute:** user re-runs the script with the approval code
6. Adds each query as a PHRASE match negative to the specified shared set
7. Stamps "X" in col E for successfully uploaded rows

---

## Two-Step Mutation Flow

This skill follows the [`mutation-safety`](../mutation-safety/) pattern. Every upload is a two-step flow — **never skip the dry-run, never auto-approve**.

### Step 1 — Dry-run preview (no changes)

```bash
python scripts/sqr_upload_negatives.py --sheet-id YOUR_SHEET_ID
```

Output includes:
- Count of pending keywords
- Per-account and per-shared-set breakdown
- Sample keywords
- An **APPROVAL CODE** like `APPROVE-A3F9B2C1`

Present the preview to the user and **wait for explicit approval** before running Step 2.

### Step 2 — Execute with approval code

```bash
python scripts/sqr_upload_negatives.py --sheet-id YOUR_SHEET_ID APPROVE-A3F9B2C1
```

The script:
- Re-computes the approval code from the current sheet state
- Refuses to execute if the code doesn't match (safety net if the sheet changed since the dry-run)
- Uploads keywords via `SharedCriterionService`
- Stamps "X" in col E for successfully uploaded rows
- Reports upload and failure counts per account

### How the approval code works

The code is a SHA-256 hash of the sorted `(trunc_cid, shared_set_id, query)` tuples across all pending rows, truncated to 8 hex chars and prefixed with `APPROVE-`.

- **Deterministic:** same pending data → same code. No state file needed.
- **Safe against drift:** if anyone edits the Uploader tab between the dry-run and execute, the code changes and execution is refused.
- **Self-expiring:** if the user adds more rows and comes back later, the old code is no longer valid.

---

## Uploader Tab Column Schema (required)

| Column | Letter | Purpose |
|--------|--------|---------|
| CID | A | Full format customer ID (e.g., `123-456-7890`) — informational only |
| Query | B | Search term to add as negative — **required** |
| Neg List ID | C | Shared negative keyword list ID — **required** |
| Trunc CID | D | Numeric customer ID (e.g., `1234567890`) — **required** |
| Uploaded? | E | Empty = pending, `X` = done (script writes here) |

Row 1 is treated as a header and skipped.

---

## CLI Reference

| Flag | Default | Purpose |
|------|---------|---------|
| `--sheet-id` | **required** | Google Sheet ID (from sheet URL between `/d/` and `/edit`) |
| `--tab-name` | `Uploader` | Tab name |
| `--config` | `google-ads.yaml` | Google Ads credentials YAML at project root |
| `--sheets-token` | `token-sheets.json` | Sheets OAuth token. If not found, falls back to refresh token in `--config` |
| `approval_code` (positional) | — | `APPROVE-XXXXXXXX` from dry-run. Omit for dry-run mode. |

---

## Prerequisites

1. **Google Ads API credentials** — `google-ads.yaml` at project root (see [`google-ads-api-setup`](../google-ads-api-setup/))
2. **Google Sheets access** — either a `token-sheets.json` at project root OR a `google-ads.yaml` whose refresh token includes the spreadsheets scope
3. **Python dependencies:** `pip install google-ads google-auth google-api-python-client pyyaml`

---

## Error Modes

| Error | Cause | Fix |
|-------|-------|-----|
| `Approval code mismatch` | Sheet changed between dry-run and execute | Re-run dry-run to get a fresh code |
| `keyword is N chars (max 80)` | Query exceeds Google Ads 80-char limit | Shorten or remove from sheet |
| `Cannot authenticate to Sheets` | Neither token-sheets.json nor google-ads.yaml with spreadsheets scope | See google-ads-api-setup and add spreadsheets scope |
| `No pending rows found` | Either no queries in col B or all already stamped | Verify sheet has rows with Query + empty Uploaded |

---

## Installation

```bash
mkdir -p .claude/skills/sqr-upload/scripts
curl -o .claude/skills/sqr-upload/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/sqr-upload/SKILL.md
curl -o .claude/skills/sqr-upload/scripts/sqr_upload_negatives.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/sqr-upload/scripts/sqr_upload_negatives.py
```

---

## Related Skills

- Upstream — [`offbrand-analyzer`](../offbrand-analyzer/) — Step 1 of SQR Pipeline (query categorization)
- Upstream — [`geo-conflict-analyzer`](../geo-conflict-analyzer/) — Step 2 of SQR Pipeline (geo conflict detection)
- Upstream — [`sqr-3run`](../sqr-3run/) — 3-run consensus orchestration across offbrand + geo classifiers
- Foundational — [`mutation-safety`](../mutation-safety/) — two-step approval pattern this skill implements
