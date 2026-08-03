---
name: add-account-negative-keywords
description: Add account-level negative keywords (Admin → Account Settings → Negative Keywords) to Google Ads accounts using the 3-step SharedSet approach. Auto-invoke when user says "add account negatives", "add account-level negatives", "set up account negative keywords for [account(s)]", or "roll the negative-list baseline to [accounts]". Supports single-account and bulk-portfolio operations.
allowed-tools: [Read, Bash, Grep, Glob]
---

# Add Account-Level Negative Keywords

**Purpose:** Roll a curated baseline of account-level negative keywords (the ones in
Admin → Account Settings → Negative Keywords) across one or many Google Ads accounts,
using the confirmed 3-step SharedSet approach.

**Type:** MUTATION skill. This writes to live accounts. The
[`mutation-safety`](../mutation-safety/) two-step protocol is not a step in this
workflow — it *is* the workflow: dry-run preview → human reads the plan → approval code
generated → human gives the go → execution. Never chain code generation and execution
in a single action, and never skip the preview read.

**This skill deliberately does NOT:**
- Delete or detach anything — no keyword removals, no SharedSet deletion, no list
  detachment. Removals are a separate, explicitly-gated act you perform outside this
  skill (UI or a dedicated script you review on its own).
- Add campaign-level negatives — that altitude belongs to
  [`sqr-pipeline`](../sqr-pipeline/) (query-evidence negatives) or your campaign build.
- Choose your baseline for you — the shipped sample is a starting point; curation
  against your portfolio (`rules.md`) is your judgment call.
- Verify which set an attachment points to — the API can't read that back (quirk table
  in the contract); final confirmation is always the UI.
- Analyze keyword performance — no metrics are pulled anywhere in this skill.

---

## Background — Why 3 Steps, Not 2

Account-level negatives are backed by a `SharedSet` of type
`ACCOUNT_LEVEL_NEGATIVE_KEYWORDS`. Most external guidance describes a 2-step setup that
*appears* to work in the API and even renders in the UI, but leaves the data model
fragile. The correct, confirmed pattern is **3 steps**:

```
Step 1: Create SharedSet (type=ACCOUNT_LEVEL_NEGATIVE_KEYWORDS)
Step 2: Add keywords as SharedCriterion entries (PHRASE match, batched up to 1000)
Step 3: Create CustomerNegativeCriterion with negative_keyword_list.shared_set
        pointing to the SharedSet  ← the step most guides miss
```

If a set already exists for an account, **only Step 2 runs** — the skill adds just the
missing keywords to the existing set. Re-running against a compliant portfolio is a safe
no-op. One honest limit to know: the attachment (Step 3) is created only when the skill
builds the set itself — a pre-existing set that was never attached stays unattached, and
only the session JSON tells you (`references/mutation-contract.md` § Categorization).

## Per-Account State Categorization

For each target account, the script queries all 3 layers and routes one of three ways:

| State | Path | Mutations |
|---|---|---|
| **NO_SET** | Full 3-step setup | 1 SharedSet + N SharedCriteria + 1 CustomerNegativeCriterion |
| **PARTIAL** | Step 2 only | M SharedCriteria (only the keywords not already in the set) |
| **COMPLIANT** | Skip | None |

A `Layer N query error:` line above a categorization invalidates it — see `rules.md`
invariant 5 before trusting any preview that printed one.

---

## The Two-Step Mutation Flow

### Step 1 — Dry-run preview (default; mutates nothing, writes nothing)

```bash
# Single account by name
python scripts/add_account_negative_keywords.py "Example Account"

# Multiple accounts (comma-separated names or CIDs)
python scripts/add_account_negative_keywords.py "Example Account, 1234567890, Another Account"

# All accounts in a portfolio (resolved via your accounts.json)
python scripts/add_account_negative_keywords.py --portfolio my-portfolio
```

Output: per-account state query, categorization (NO_SET / PARTIAL / COMPLIANT), the
summary table with the `Add` column, and total mutation counts. **Read it.** The
curation and conflict checks in `rules.md` happen before or alongside this step.

### Step 2 — Generate approval code

```bash
python scripts/add_account_negative_keywords.py "Example Account" --execute
```

Re-queries state fresh, prints the same preview, generates a unique `APPROVE-XXXXXXXX`
code, and snapshots the resolved plan to a session JSON. Accounts that became compliant
since your dry-run drop out of the fresh plan.

### Step 3 — Execute with approval code

```bash
python scripts/add_account_negative_keywords.py "Example Account" --execute --approval-code APPROVE-XXXXXXXX
```

Executes **the saved session plan** (the CLI account list is re-validated but the
snapshot governs — see the contract), skips COMPLIANT accounts, logs every per-account
result, and continues past per-account failures.

---

## CLI Reference

| Flag | Default | Purpose |
|------|---------|---------|
| `accounts` (positional) | — | Comma-separated names or CIDs (optional if using `--portfolio`) |
| `--portfolio NAME` | — | Resolve all accounts in a portfolio from `accounts.json` (combines with positional) |
| `--keywords-file PATH` | `sample_baseline_keywords.txt` | Baseline list, one per line. Bare-name default resolves against your working directory first, then falls back to the script's own folder — which is where the shipped sample lives (`scripts/sample_baseline_keywords.txt`). Details in the contract. |
| `--set-name NAME` | `"Account Negative Keywords"` | Name for **newly created** sets only — delta adds go to whichever ENABLED account-level set already exists |
| `--exclude-cid CID` | — | Skip a specific CID (repeatable) |
| `--execute` | off | Generate approval code + save session (without this, the script is dry-run) |
| `--approval-code APPROVE-XXX` | — | Execute the saved session for the given code |
| `--accounts-json PATH` | `accounts.json` (current dir) | Path to your `accounts.json` |
| `--log-sheet-id ID` | *(off)* | Optional Google Sheet ID for central mutation log |
| `--credentials PATH` | `google-ads.yaml` | Google Ads API credentials |
| `--log-dir` / `--session-dir` | skill folder's `logs/` and `sessions/` | Runtime output locations (derived from the script's own path, not your cwd) |

## accounts.json Format

The skill resolves account names → CIDs via a local `accounts.json` you maintain:

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

Pass a `name`, an `alias`, or a raw CID. Name matching falls through to substring, and
unknown CIDs pass through as raw targets — the resolution ladder and its traps are in
the contract; read the preview's resolved-account lines, not just the totals.

---

## Files in This Skill

| File | Role |
|---|---|
| `SKILL.md` | This workflow — identity, flow, routing |
| `rules.md` | Judgment layer: baseline curation, account-vs-campaign altitude, conflict awareness, false alarms |
| `examples.md` | Three worked reads, including the two dry-run reads that prevent bad executions |
| `references/mutation-contract.md` | Line-derived script mechanics: the three passes, resolution ladders, state/categorization semantics, logging, console anatomy, API quirks |
| `scripts/add_account_negative_keywords.py` | The tool — all three passes |
| `scripts/sample_baseline_keywords.txt` | Shipped 131-row property-management baseline (curate before use) |
| `logs/`, `sessions/` *(runtime, created on demand)* | JSONL audit trail; approval-code-keyed plan snapshots. Contain account names + CIDs — keep out of version control |

## After a Run

- **Dry-runs leave no trace** — nothing on disk, nothing mutated.
- **Code generation** leaves one file: `sessions/account_negs_APPROVE-XXXXXXXX.json`
  (the plan snapshot, including each account's `cnc_attached` — the only place that
  surfaces).
- **Execution** appends one JSONL row per account to
  `logs/account_negs_mutations.jsonl` (timestamp, account, CID, action, details,
  success, error, approval code) — your audit trail — plus optional Sheet rows.
- **Always finish in the UI:** Admin → Account Settings → Negative Keywords on at least
  one mutated account. The API's read-back quirks make this the only true confirmation.

## When to Load Other Skills

| Load | When |
|---|---|
| [`mutation-safety`](../mutation-safety/) | Before any `--execute` — this skill implements its Rule 1 two-step approval protocol (preview/approve/execute); the protocol rules live there |
| [`neg-conflict-finder`](../neg-conflict-finder/) | After every roll (and before, if you suspect existing conflicts) — finds negatives silently blocking positives at every level |
| [`sqr-pipeline`](../sqr-pipeline/) | When the ask is query-evidence negatives ("negate these search terms") — that's campaign-level with its own review gate, not baseline material |
| [`google-ads-query`](../google-ads-query/) | Pre-flight: pull an account's positive keywords to grep against the baseline before the first roll |
| [`fair-housing-compliance`](../fair-housing-compliance/) | PM portfolios: before deciding baseline rows touching age, family status, or income |
| [`dgen-automation-disable`](../dgen-automation-disable/) | Same preview/execute mutation pattern in a different domain — useful as a second reference implementation |
| [`google-ads-api-setup`](../google-ads-api-setup/) | First-time credential setup (`google-ads.yaml`) |

---

## Prerequisites

1. **Google Ads API credentials** — `google-ads.yaml` (see [`google-ads-api-setup`](../google-ads-api-setup/))
2. **Python:** `pip install google-ads google-auth google-api-python-client pyyaml`
3. **An `accounts.json`** mapping names → CIDs (or pass CIDs directly)
4. **A curated baseline keyword list** (the skill ships a generic property-management
   sample; curate per `rules.md`, replace with your own)
5. **For `--log-sheet-id`:** the refresh token in `google-ads.yaml` must include the
   `https://www.googleapis.com/auth/spreadsheets` scope

## Installation

```bash
mkdir -p .claude/skills/add-account-negative-keywords/scripts \
         .claude/skills/add-account-negative-keywords/references
for f in SKILL.md README.md rules.md examples.md references/mutation-contract.md \
         scripts/add_account_negative_keywords.py scripts/sample_baseline_keywords.txt; do
  curl -o ".claude/skills/add-account-negative-keywords/$f" \
    "https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/add-account-negative-keywords/$f"
done
```

---

## Known API Quirks

Four documented-but-easy-to-trip-on API behaviors (zero member counts, empty
attachment read-back, the `id` field name) shape how this script verifies its own
work. The full quirk table — and how the script responds to each — lives in
`references/mutation-contract.md` § The API quirks this script is built around.
