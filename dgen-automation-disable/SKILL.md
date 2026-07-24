---
name: dgen-automation-disable
description: Bulk-disable Demand Gen ad-level asset automation settings. Auto-invoke when user says "disable dgen automation", "fix dgen asset settings", "turn off dgen auto assets", "dgen automation fix", or "fix demand gen automation".
allowed-tools: [Bash, Read]
---

# DGen Ad-Level Automation Disable

**Purpose:** Programmatically set all Demand Gen ad-level asset automation
settings to `OPTED_OUT` across one or many accounts — the auto-generated
design versions, generated videos, and landing-page previews that trade
creative control for Google's guesses.

**Type:** Mutation skill — two-step approval required, always. The
[`mutation-safety`](../mutation-safety/) pattern (dry-run preview → human
reads → execute with the code from that preview) is implemented directly in
the shipped script.

This skill deliberately does NOT:

- **Decide whether disabling is right for the account** — that judgment
  (accounts leaning on generated video, shared management, mid-flight
  experiments) lives in [`rules.md`](rules.md) § "When NOT to disable" and
  belongs to the operator.
- **Touch campaign-level automation** — PMax automation is campaign-level
  and belongs to [`pmax-asset-automation`](../pmax-asset-automation/); DGen
  automation is per-ad, which is why this tool exists separately.
- **Enable anything, ever** — one direction only, toward `OPTED_OUT`.
- **Execute without a human-read dry-run** — no code, no mutation; and the
  code only proves the account hasn't changed since the preview you read.
- **Normalize CIDs** — dashes are NOT stripped; a dashed CID errors rather
  than matching (contract).

---

## Background (one paragraph)

Demand Gen asset automation operates at the **ad level** — settings live on
each ad, new ads arrive with automation ON, and two ad types carry five
settings between them (the exact taxonomy and defaults:
[`references/mutation-contract.md`](references/mutation-contract.md)). One
default matters at read time: `GENERATE_LANDING_PAGE_PREVIEW` ships OFF, so
finding it ON in a diff means someone turned it on — attribute before you
overwrite ([`rules.md`](rules.md), reading the diff).

---

## Two-Step Mutation Flow

### Step 1 — Dry-run preview (free, writes nothing)

```bash
# Single account
python scripts/fix_dgen_ad_automation.py --cid 1234567890

# Multiple accounts (comma-separated CIDs)
python scripts/fix_dgen_ad_automation.py --cids "1234567890,2345678901"

# All enabled accounts under the MCC
python scripts/fix_dgen_ad_automation.py --all
```

Prints per-account diffs (each ad's settings with `current -> OPTED_OUT`
lines), a summary (accounts / ads / settings), and an **APPROVAL CODE**.

**Then READ the diff** — the five checks in [`rules.md`](rules.md) § "Reading
the dry-run diff": error lines (an erroring account silently drops out —
`All accounts are compliant` can be false), ad counts vs. expectation,
settings-per-ad sanity, the landing-page-preview tell, and unexpected
current values. Approve only what you can explain.

### Step 2 — Execute with the approval code

```bash
python scripts/fix_dgen_ad_automation.py --cid 1234567890 APPROVE-A3F9B2C1
```

The code is a deterministic hash of the pending work, recomputed from
current account state at execute time — ANY drift since your dry-run
(new ads, a Google-side reset, a colleague's fix) refuses with a mismatch.
A mismatch is information, not an error: re-run the dry-run and read what
changed ([`rules.md`](rules.md), "the mismatch is a feature"). Full hash
semantics: the contract.

Execution is one all-or-nothing mutation per account; failed accounts log
and the batch continues. Every execute appends to
`./logs/mutations_log.jsonl` (success and failure) — dry-runs write
nothing.

### Step 3 — Verify (optional, execute-mode, single account)

```bash
python scripts/fix_dgen_ad_automation.py --cid 1234567890 APPROVE-A3F9B2C1 --verify
```

Re-queries and confirms every in-scope DGen ad is `OPTED_OUT`. Three no-op
cases for `--verify` (silent on dry-run and already-compliant runs; a
printed note on multi-account runs) are in the contract — for a
no-mutation compliance check, use a plain dry-run instead.

---

## CLI Reference

| Flag | Default | Purpose |
|------|---------|---------|
| `--cid CID` | — | Single account (mutually exclusive with `--cids`/`--all`) |
| `--cids CID1,CID2,...` | — | Multiple accounts (used exactly as typed — no dash-stripping) |
| `--all` | — | All enabled non-manager accounts under `login_customer_id` from google-ads.yaml |
| `approval_code` (positional) | — | `APPROVE-XXXXXXXX` from dry-run. Omit for dry-run mode. |
| `--config` | `google-ads.yaml` | Path to Google Ads credentials YAML |
| `--log-dir` | `logs` | Directory for the local JSONL mutation log |
| `--log-sheet-id` | *(off)* | Optional Google Sheet ID for a central mutation log |
| `--verify` | off | Post-execute re-query (single account only) |

Selection scope (what "in scope" means — enabled campaigns and ads, ended
campaigns excluded, paused ad groups' enabled ads INCLUDED), logging shapes,
and the sheet-log token requirement are all in
[`references/mutation-contract.md`](references/mutation-contract.md).

One implementation fact worth knowing even if you never read the contract:
the API **replaces the whole settings list** on update — the script always
sends every applicable setting per ad type, and any tooling you write
against this field must do the same, or unspecified settings silently reset
to `OPTED_IN`.

---

## Prerequisites

1. **Google Ads API credentials** — `google-ads.yaml` at project root (see
   [`google-ads-api-setup`](../google-ads-api-setup/))
2. **Python:** `pip install google-ads google-auth google-api-python-client pyyaml`
3. **For `--log-sheet-id` only:** the refresh token inside `google-ads.yaml`
   must carry the spreadsheets scope (the api-setup generator's default
   token does). The local JSONL log needs nothing extra.

---

## Installation

```bash
mkdir -p .claude/skills/dgen-automation-disable/scripts .claude/skills/dgen-automation-disable/references
for f in SKILL.md README.md rules.md examples.md; do
  curl -o .claude/skills/dgen-automation-disable/$f \
    https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/dgen-automation-disable/$f
done
curl -o .claude/skills/dgen-automation-disable/references/mutation-contract.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/dgen-automation-disable/references/mutation-contract.md
curl -o .claude/skills/dgen-automation-disable/scripts/fix_dgen_ad_automation.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/dgen-automation-disable/scripts/fix_dgen_ad_automation.py
```

---

## Files in This Skill

| File | Role |
|---|---|
| `SKILL.md` | This workflow — the two-step flow, CLI surface, routing |
| `rules.md` | Judgment layer: the five dry-run reads, when NOT to disable, mismatch handling, cadence, false alarms, escalation |
| `examples.md` | Three worked runs — clean execute, the drift mismatch, the false compliance |
| `references/mutation-contract.md` | Exact selection/hash/mutation/logging/verify mechanics (source of truth: the script) |
| `scripts/fix_dgen_ad_automation.py` | The tool — dry-run by default, mutates only with a fresh approval code |
| `README.md` | Zero-context install and orientation |

Runtime artifacts (gitignore them): `logs/mutations_log.jsonl` — appended
on every execute; dry-runs write nothing.

## After a Run

`logs/mutations_log.jsonl` is the durable record — one line per account per
execute, success or failure. No row = no mutation through this script. The
API-side record is the account's change history. When a run mutated
anything, calendar the follow-ups from [`rules.md`](rules.md) § Cadence:
the monthly drift re-run, and a re-run after any paused campaign
re-enables.

## When to Load Something Else

| Trigger | Load |
|---|---|
| A diagnostic flagged DGen automation ON ([`account-diagnostic`](../account-diagnostic/) check 44, or [`ads-checker`](../ads-checker/)'s ad-level automation check) | This skill is the fixer those finders route to — run the dry-run |
| The finding is campaign-level automation on PMax | [`pmax-asset-automation`](../pmax-asset-automation/) — the campaign-level twin |
| A setting is ON that nobody in your shop enabled | [`change-history-checker`](../change-history-checker/) — inside 30 days it names the actor; attribute before overwriting |
| You're about to respond to ANY mutation-shaped work | [`mutation-safety`](../mutation-safety/) — the pattern this skill implements; read it once so the two-step flow is philosophy, not ritual |
| Why "empty beats auto-generated" is the house default | [`ad-copy-verification-standard`](../ad-copy-verification-standard/) — *Empty > Inaccurate* |
| No working `google-ads.yaml` yet | [`google-ads-api-setup`](../google-ads-api-setup/) — one-time credential setup |
