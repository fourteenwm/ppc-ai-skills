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
- Sample 131-keyword property-management baseline included (curate against your portfolio before rolling — `rules.md` shows how)
- Operator docs: `rules.md` (baseline curation, when account-level is the wrong altitude, conflict awareness, false alarms), `examples.md` (worked reads including the two that prevent bad executions), and `references/mutation-contract.md` (line-derived script mechanics)

---

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

The full quirk table, and how the script responds to each, is in `references/mutation-contract.md`.

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
