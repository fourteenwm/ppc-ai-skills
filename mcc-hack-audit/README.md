# MCC Hack Audit

Scans your full Google Ads MCC tree and identifies every manager (MCC) that has access to any account. Classifies each link as INTERNAL (in your tree), HOSTILE (your threat list), or EXTERNAL (potential exposure).

**The pain point:** Manager-link fraud is rising. Hostile MCCs gain access through compromised client-side admin credentials, link themselves into the tree, and start mutating campaigns before anyone notices. The Google Ads UI shows manager access one account at a time. Across a portfolio of dozens or thousands of accounts, you can't audit it manually. This skill walks the entire tree in one run, outputs a CSV of every (account, manager) pair, and surfaces the non-internal links for review.

This skill was built in direct response to a real-world incident where three hostile external MCCs accessed two client accounts via compromised admin credentials. The audit ran across ~10,000 accounts in under five minutes and made the access map visible.

---

## What's Inside

- Walks your full MCC tree from `login_customer_id` (auto-detects every internal account and sub-MCC)
- Pulls `customer_manager_link` for every account using parallel API calls (20 workers by default)
- Classifies each link as INTERNAL, HOSTILE, or EXTERNAL — no "trusted partner" auto-clearance
- Optional `--trusted-cids` flag if you want to suppress long-standing trusted external MCCs
- Outputs two CSVs: all links + suspicious-only subset
- Optional Google Sheets upload with four organized tabs
- Handles CANCELED/CLOSED accounts (they hold security-relevant link history too)

---

## Installation

```bash
mkdir -p .claude/skills/mcc-hack-audit/scripts
curl -o .claude/skills/mcc-hack-audit/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/mcc-hack-audit/SKILL.md
curl -o .claude/skills/mcc-hack-audit/scripts/mcc_hack_audit.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/mcc-hack-audit/scripts/mcc_hack_audit.py
```

---

## Prerequisites

- Google Ads API credentials YAML with MCC access (`google-ads.yaml`)
- `login_customer_id` set in the YAML — the script reads this to detect your tree
- Python packages: `google-ads`, `pyyaml`
- Optional: `gspread` if you want Google Sheets upload (`pip install gspread google-auth`)

---

## Quick Start

```bash
# Run the audit (writes CSVs to ./output/)
python scripts/mcc_hack_audit.py

# Review the suspicious-only CSV first
cat output/mcc_link_scan_*_SUSPICIOUS.csv
```

Open the suspicious CSV. Every EXTERNAL row is a manager outside your tree with access to one of your accounts. For each one, decide: legitimate (former agency, integration partner), expected (parent company), or unknown (investigate).

---

## When to Run

- **Quarterly** as a baseline scrubdown
- **Immediately** when a client reports unexpected campaign activity
- **After onboarding** a new client account to verify their existing manager access
- **After offboarding** to verify your access has been correctly removed

---

## What This Skill Does NOT Do

- It does NOT remove manager links (manual UI action)
- It does NOT notify clients
- It does NOT send alerts to Slack/email
- It does NOT auto-judge external MCCs as legitimate or malicious

Identification is the entire scope. Action is yours.

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage 118 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
