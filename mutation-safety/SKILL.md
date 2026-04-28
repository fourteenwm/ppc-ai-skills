---
name: mutation-safety
description: MANDATORY safety system for ALL Google Ads mutations AND destructive Google Sheets writes. Auto-invoke whenever ANY agent, skill, or script attempts to modify Google Ads accounts or overwrite Google Sheets data. Enforces two-step approval to prevent accidental changes.
allowed-tools: [Read]
---

# Mutation Safety

**Purpose:** Enforce two-step approval for ALL mutations to Google Ads accounts AND destructive Google Sheets writes.

**Type:** Safety enforcement skill (MANDATORY — auto-invokes for all mutations)

---

## Core Rules

### Rule 1: No Mutations Without Two-Step Approval

Any operation that writes, updates, or deletes data in Google Ads or Google Sheets MUST follow this flow:

1. **Dry Run** — Show exactly what will change, with current and proposed values
2. **User Approval** — Wait for explicit user confirmation before executing
3. **Execute** — Only after approval, run the mutation

**Never skip the dry run. Never auto-approve.**

### Rule 2: Exact Match Required for All Identifiers

ALL mutations MUST use exact matching for identifiers to prevent accidental modifications.

**Identifiers requiring exact match:**
- Customer IDs (CIDs)
- Conversion action names
- Campaign names
- Ad group names
- Keyword text
- Shared set names
- Any other named entity

**Implementation rules:**
- Default to exact match for all mutations (no flag needed)
- Pattern matching requires an explicit opt-in flag
- GAQL queries for mutations MUST use `= 'value'` instead of `LIKE '%value%'`
- Fuzzy/partial matching is ONLY allowed for read-only queries (reports, audits)

**Why this matters:**
- "Form_Submit" and "Form_Submit_BC" are different conversion actions
- CID `1234567890` and `1234567809` are different accounts
- One character difference can affect the wrong entity

### Rule 3: Scope Verification Before Execution

Before executing any mutation:
1. Confirm the target account is one the user actually manages
2. If an account is not in the known accounts list, STOP and ask
3. When asked to modify "this account," confirm which specific account is meant
4. When asked to modify "all accounts," clarify the exact scope before proceeding

### Rule 4: Show What Will Change

The dry-run preview MUST include:
- **Target:** Which account(s) and entities
- **Current state:** What the values are now
- **Proposed state:** What they will be after the mutation
- **Count:** How many entities are affected
- **Reversibility:** Whether this change can be undone (and how)

### Rule 5: Never Generate Approval Codes

If your system uses approval codes or confirmation tokens:
- The USER must provide the approval code
- Claude/AI must NEVER generate, guess, or auto-fill approval codes
- The approval code exists so the human controls execution

---

## What Counts as a Mutation

### Google Ads API Mutations
- Creating campaigns, ad groups, keywords, or ads
- Updating budgets, bids, or bid strategies
- Pausing or enabling campaigns/ad groups/keywords
- Adding or removing negative keywords
- Modifying conversion action settings (values, attribution, counting)
- Updating ad copy (headlines, descriptions)
- Any `mutate` call to the Google Ads API

### Google Sheets Destructive Writes
- Clearing a sheet tab
- Overwriting existing data
- Deleting rows or columns
- Replacing tab contents

### NOT Mutations (No Approval Needed)
- Reading/querying Google Ads data (SELECT queries)
- Reading Google Sheets data
- Writing to a NEW (empty) sheet tab
- Appending rows to the end of existing data
- Local file operations

---

## Dry-Run Output Format

When presenting the dry-run preview, use this structure:

```
MUTATION PREVIEW
================
Target: [Account Name] (CID: XXXXXXXXXX)
Operation: [What will change]
Entities affected: [Count]

Current → Proposed:
  - [Entity 1]: [current value] → [new value]
  - [Entity 2]: [current value] → [new value]

Reversibility: [Yes/No — how to undo if needed]

Type APPROVE to execute, or CANCEL to abort.
```

---

## Revert Knowledge

If a mutation needs to be undone:

- **Budget changes:** Use `op.update` with the original budget value
- **Paused entities:** Use `op.update` to set status back to ENABLED
- **Renamed entities:** Use `op.update` with the original name
- **Added negative keywords:** Use `op.remove` with the keyword criterion resource name
- **Conversion action changes:** Use `op.update` with original values (name, default_value, lookback windows)
- **Deleted/removed conversion actions:** Cannot be restored via API — these are permanent

**Important:** Some operations are irreversible. Always flag irreversible mutations in the dry-run preview.

---

## Common Mistakes This Prevents

1. **Wrong account scope** — Script meant for one account runs across the entire MCC
2. **Partial name match** — LIKE query matches 3 conversion actions instead of 1
3. **Transposed CID** — Digits swapped, mutation hits wrong account entirely
4. **Auto-approve in batch** — Script processes 50 accounts without stopping for review
5. **Overwrite vs. append** — Sheet write replaces existing data instead of adding to it
6. **Test vs. production** — Mutation runs against live account instead of test account
