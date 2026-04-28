# Mutation Safety

A two-step approval system that prevents accidental changes to live Google Ads accounts.

**The pain point:** AI is fast. Too fast. One wrong API call can pause a live campaign, overwrite conversion settings, or rename 50 ad groups. By the time you notice, the damage is done. This skill forces a mandatory dry-run → approve → execute workflow for every mutation.

**Featured as a community skill in Mike Rhodes' Ads to AI community.**

---

## What It Prevents

Real mistakes this skill was built to catch:

- Renaming "Form_Submit" when you meant "Form_Submit_BC" (one character difference, wrong conversion action)
- Modifying account `1234567890` when you meant `1234567809` (transposed digits)
- Pausing all campaigns in an account because a script had the wrong scope
- Uploading negative keywords to the wrong shared list
- Overwriting a Google Sheet tab with live client data

---

## How It Works

### Step 1: Dry Run
Before any mutation executes, the skill forces a preview showing exactly what will change:
- Which account(s)
- Which entities (campaigns, keywords, ads, etc.)
- What the current values are
- What the new values will be
- How many entities are affected

### Step 2: User Approval
The user reviews the preview and explicitly approves before anything is written. No auto-execution, ever.

### Step 3: Execute
Only after approval does the mutation run against the live account.

---

## Installation

Copy `SKILL.md` into your Claude Code project:

```bash
mkdir -p .claude/skills/mutation-safety
cp SKILL.md .claude/skills/mutation-safety/SKILL.md
```

Once installed, Claude will automatically enforce the two-step approval process whenever you ask it to make changes to Google Ads accounts or overwrite data in Google Sheets.

---

## When It Activates

The skill auto-invokes whenever Claude is about to:
- Add, update, or delete campaigns, ad groups, keywords, or ads
- Change budgets or bid strategies
- Modify conversion action settings
- Upload negative keywords
- Overwrite or delete Google Sheets data
- Any other write operation against the Google Ads API

---

## Design Philosophy

- **Dry-run first, always.** No mutation executes without a preview.
- **Exact match by default.** Entity names and IDs must match exactly — no fuzzy matching for mutations. Pattern matching is opt-in and only for read-only operations.
- **User controls execution.** The skill never auto-approves. The user must explicitly say to proceed.
- **Scope verification.** Before mutations run, the skill confirms the account is one you actually manage.

---

## Prerequisites

None. This is a protocol skill — it works with just Claude Code installed. No API keys or external dependencies required.

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage 118 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
