# Add Account-Level Negative Keywords

Bulk-add account-level negative keywords (Admin → Account Settings → Negative Keywords) to one or many Google Ads accounts using the confirmed 3-step SharedSet approach.

**The pain point:** Account-level negatives are backed by `SharedSets` of type `ACCOUNT_LEVEL_NEGATIVE_KEYWORDS` — but the official guidance and most tutorials describe a 2-step setup that *appears* to work in the API and yet leaves the data model fragile. The correct path is 3 steps: SharedSet → SharedCriteria → CustomerNegativeCriterion attachment. This skill encodes the correct 3-step pattern and applies it idempotently across a baseline keyword list, so you can roll a single negative-list standard out across a managed portfolio.

---

## What's Inside

- Confirmed 3-step API flow (SharedSet → SharedCriteria → CustomerNegativeCriterion)
- Per-account state categorization — automatically routes each account to NO_SET, PARTIAL, or COMPLIANT
- Idempotent: re-running against compliant accounts is a no-op; partial accounts only get the missing keywords added
- Dry-run preview by default — shows the full plan before any mutation
- Two-step approval workflow with unique approval codes (mutation-safety protocol)
- Per-account error handling — one failure doesn't stop the batch
- Optional dual logging: local JSONL plus a Google Sheets central log
- Multi-account support (comma-separated names/CIDs or portfolio filter via `accounts.json`)
- Sample 131-keyword property-management baseline included (replace with your own)

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

## Prerequisites

- Google Ads API credentials (YAML config) with write access
- Python with `google-ads`, `google-auth`, `google-api-python-client`, `pyyaml` packages
- An `accounts.json` mapping account names → CIDs for multi-account resolution (or pass CIDs directly)
- The `mutation-safety` skill (for the two-step approval protocol)
- Optional: Google Sheets API credentials, for opt-in central mutation logging

---

## Known API Quirks

The Google Ads API has three reporting bugs that affect this domain. The skill is built defensively around them:

- `shared_set.member_count` always reports `0` — ignore
- `shared_set.reference_count` always reports `0` — ignore
- `negative_keyword_list.shared_set` reads back empty in GAQL — the write works, the read doesn't. Don't rely on read-back to verify attachment; verify in the UI.

The skill documents these in detail.

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
