---
name: add-account-negative-keywords
description: Add account-level negative keywords (Admin → Account Settings → Negative Keywords) to Google Ads accounts using the 3-step SharedSet approach. Auto-invoke when user says "add account negatives", "add account-level negatives", "set up account negative keywords for [account(s)]", or "roll the negative-list baseline to [accounts]". Supports single-account and bulk-portfolio operations.
allowed-tools: [Read, Bash, Grep, Glob]
---

# Add Account-Level Negative Keywords

**Purpose:** Add account-level negative keywords (the ones that show in Admin → Account Settings → Negative Keywords) to one or more Google Ads accounts using the confirmed 3-step SharedSet approach.

**Type:** Mutation skill (two-step approval required)

---

## Auto-Invoke When

- "add account negatives for [account]"
- "add account-level negatives to [accounts]"
- "set up account negative keywords for [account(s)]"
- "roll the [name] negatives to [accounts]"
- "add the baseline negatives to [account]"

---

## Background — Why 3 Steps, Not 2

Account-level negatives (the ones in Admin → Account Settings → Negative Keywords) are backed by a `SharedSet` of type `ACCOUNT_LEVEL_NEGATIVE_KEYWORDS`. Most external guidance describes a 2-step setup that *appears* to work in the API and even renders in the UI, but leaves the data model fragile. The correct, confirmed pattern is **3 steps**:

```
Step 1: Create SharedSet (type=ACCOUNT_LEVEL_NEGATIVE_KEYWORDS)
Step 2: Add keywords as SharedCriterion entries (PHRASE match, batched up to 1000)
Step 3: Create CustomerNegativeCriterion with negative_keyword_list.shared_set
        pointing to the SharedSet  ← the step most guides miss
```

If a SharedSet + CNC already exists for an account, **only Step 2 runs** — the skill adds just the missing SharedCriteria to the existing set. No duplicate SharedSet, no duplicate CNC.

---

## Per-Account State Categorization

For each target account, the script queries all 3 layers and routes one of three ways:

| State | Path | Mutations |
|---|---|---|
| **NO_SET** | Full 3-step setup | 1 SharedSet + N SharedCriteria + 1 CustomerNegativeCriterion |
| **PARTIAL** | Step 2 only | M SharedCriteria (only the keywords not already in the set) |
| **COMPLIANT** | Skip | None |

This means re-running against an already-compliant portfolio is a safe no-op, and partial accounts only get the delta.

---

## Two-Step Mutation Flow

This skill follows the [`mutation-safety`](../mutation-safety/) pattern. **Never skip the dry-run, never auto-approve.**

### Step 1 — Dry-run preview

```bash
# Single account by name
python scripts/add_account_negative_keywords.py "Example Account"

# Multiple accounts (comma-separated names or CIDs)
python scripts/add_account_negative_keywords.py "Example Account, 1234567890, Another Account"

# All accounts in a portfolio (resolved via your accounts.json)
python scripts/add_account_negative_keywords.py --portfolio my-portfolio
```

Output includes:
- Per-account state query (which layer exists, how many keywords are present)
- Per-account categorization (NO_SET / PARTIAL / COMPLIANT)
- Account-level summary table with `Add` column showing keywords to be added
- Total mutations across the batch
- Command to run for execution

### Step 2 — Generate approval code

```bash
python scripts/add_account_negative_keywords.py "Example Account" --execute
```

Generates a unique `APPROVE-XXXXXXXX` code and saves a session JSON with the resolved plan. The session is keyed by approval code — re-running execute produces a fresh code (and a fresh state query, so accounts that became compliant since the dry-run drop out).

### Step 3 — Execute with approval code

```bash
python scripts/add_account_negative_keywords.py "Example Account" --execute --approval-code APPROVE-XXXXXXXX
```

The script:
- Loads the saved session for that approval code
- Re-runs the appropriate path per account (full 3-step or Step 2 only)
- Skips COMPLIANT accounts
- Logs each per-account result to a local JSONL file and (optionally) a Google Sheet
- Continues on per-account failures — one bad account doesn't stop the batch

---

## CLI Reference

| Flag | Default | Purpose |
|------|---------|---------|
| `accounts` (positional) | — | Comma-separated names or CIDs (optional if using `--portfolio`) |
| `--portfolio NAME` | — | Resolve all accounts in a portfolio from `accounts.json` |
| `--keywords-file PATH` | `data/sample_baseline_keywords.txt` | Path to baseline keyword list (one per line) |
| `--set-name NAME` | `"Account Negative Keywords"` | SharedSet name to create |
| `--exclude-cid CID` | — | Skip a specific CID (repeatable) |
| `--execute` | off | Generate approval code + save session (without this, the script is dry-run) |
| `--approval-code APPROVE-XXX` | — | Execute the saved session for the given code |
| `--accounts-json PATH` | configurable | Path to your `accounts.json` |
| `--log-sheet-id ID` | *(off)* | Optional Google Sheet ID for central mutation log |
| `--credentials PATH` | `google-ads.yaml` | Google Ads API credentials |

---

## accounts.json Format

The skill resolves account names → CIDs via a local `accounts.json` you maintain. Example shape:

```json
{
  "accounts": {
    "example-account": {
      "name": "Example Account",
      "id": "1234567890",
      "portfolio": "my-portfolio",
      "aliases": ["EA", "Example"]
    }
  }
}
```

You can pass either the account `name`, an `alias`, or the raw CID — the script accepts all three.

---

## Mutation Logging

### Local (always on)

Every per-account result appends to `./logs/account_negs_mutations.jsonl` with timestamp, account, CID, action type, details, success flag, error string, and approval code. This is your audit trail.

### Google Sheet (opt-in)

Pass `--log-sheet-id YOUR_SHEET_ID` to also log to a central Sheet with columns:
`Timestamp | Account | CID | Action Type | Details | Success | Error | Approval Code`

Uses the refresh token in `google-ads.yaml` — that token must include the spreadsheets scope.

---

## Known API Quirks

These three quirks are documented in the Google Ads API but easy to trip on. The skill is built around them:

| Quirk | Impact | How the skill handles it |
|---|---|---|
| `shared_set.member_count` always reports 0 | You can't trust the count field to verify keywords were added | Skill re-queries `shared_criterion` directly |
| `shared_set.reference_count` always reports 0 | You can't trust this to verify CNC attachment | Skill checks `customer_negative_criterion` directly |
| `negative_keyword_list.shared_set` reads back empty in GAQL | The write succeeds; the read doesn't return the field | Skill confirms via UI; CNC existence is the signal |
| GAQL uses `customer_negative_criterion.id`, not `criterion_id` | Wrong field name returns no results | Skill uses the correct field |

---

## CRITICAL Rules

- **NEVER delete existing keywords** — only ADD missing ones
- **NEVER delete a SharedSet** automatically — a separate cleanup script handles that, gated by explicit user request
- **Always PHRASE match** for account-level negatives (broad-match account negatives have surprising side effects)
- **Verify in UI after execution:** Admin → Account Settings → Negative Keywords
- **Mutation-safety is mandatory** — do not bypass

---

## Prerequisites

1. **Google Ads API credentials** — `google-ads.yaml` (see [`google-ads-api-setup`](../google-ads-api-setup/))
2. **Python:** `pip install google-ads google-auth google-api-python-client pyyaml`
3. **An `accounts.json`** mapping names → CIDs (or pass CIDs directly)
4. **A baseline keyword list** (the skill ships a generic property-management sample; replace with your own)
5. **For `--log-sheet-id`:** the refresh token in `google-ads.yaml` must include `https://www.googleapis.com/auth/spreadsheets` scope

---

## Installation

```bash
mkdir -p .claude/skills/add-account-negative-keywords/scripts
curl -o .claude/skills/add-account-negative-keywords/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/add-account-negative-keywords/SKILL.md
curl -o .claude/skills/add-account-negative-keywords/scripts/add_account_negative_keywords.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/add-account-negative-keywords/scripts/add_account_negative_keywords.py
curl -o .claude/skills/add-account-negative-keywords/scripts/sample_baseline_keywords.txt \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/add-account-negative-keywords/scripts/sample_baseline_keywords.txt
```

---

## Related Skills

- [`mutation-safety`](../mutation-safety/) — two-step approval pattern this skill implements
- [`dgen-automation-disable`](../dgen-automation-disable/) — same Pattern B preview/execute approach for a different mutation domain
