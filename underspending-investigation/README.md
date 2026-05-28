# Underspending Investigation

Diagnose root causes of Google Ads account underspending and produce a specific, data-backed budget recommendation (or an explicit no-action call when a budget increase would make things worse).

**The pain point:** "Account X is underspending" is one of the most repeated tickets in any managed-portfolio PPC shop, and the wrong answer ("just raise the budget") burns money on accounts that are rank-constrained, quality-constrained, demand-constrained, or in a smart-bidding ramp-up window. This skill encodes the diagnostic discipline — a six-framework decision tree applied against standard script output — so the recommendation is always traceable to evidence, and budget increases only happen when they will actually convert into spend at an acceptable CPA / ROAS.

---

## What's Inside

- Six-framework diagnostic protocol (campaign filtering → pacing rules → sheet lookups → GAQL → impression share → budget calc) auto-loaded at investigation start
- Adaptive investigation — stop early if Step 1 explains the issue, pivot if data suggests a different path
- Decision tree for budget-too-low vs. quality-issues vs. low-demand vs. ramp-up scenarios
- Conservative budget calculation methodology with a hard 10% increase cap per single change
- Performance Max-specific handling (IS metrics don't apply; alternative diagnostics)
- Display / GDN remarketing diagnostic for "Bid setting limited" status
- Standardized output format so reports across the portfolio are directly comparable
- Read-only — never writes to Google Ads

---

## Installation

```bash
mkdir -p .claude/skills/underspending-investigation
curl -o .claude/skills/underspending-investigation/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/underspending-investigation/SKILL.md
curl -o .claude/skills/underspending-investigation/README.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/underspending-investigation/README.md
```

Then install the six companion skills (also in this repo):

```bash
for skill in campaign-line-filtering portfolio-pacing-rules google-sheets-lookups \
             google-ads-query-patterns impression-share-diagnostics budget-recommendation-calculator; do
  mkdir -p .claude/skills/$skill
  curl -o .claude/skills/$skill/SKILL.md \
    https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/$skill/SKILL.md
done
```

---

## Script Dependency (You Provide)

This skill calls a universal investigation script at `scripts/investigate_underspend.py` that you implement against your own data sources. The script is environment-specific — it lives where your Google Ads credentials, sheet IDs, and account registry live. The SKILL.md documents the data contract the script must satisfy.

**Required script output sections:**

1. **Campaign Spend Analysis (last 7 days)** — per-campaign budget, utilization %, status, bidding strategy, spend / impressions / clicks / conversions / value
2. **Impression Share Analysis** — Search IS, Budget Lost IS, Rank Lost IS for Search and Pmax (Pmax IS is not diagnostically meaningful — flag accordingly)
3. **Month-to-Date Pacing Analysis** — monthly budget, MTD spend, expected spend at current day-of-month, variance %
4. **(Optional) Recent Optimizations Log** — budget changes in the last 14 days

**Reference implementation hooks:**

- Google Ads API via `google-ads-python` (loads credentials from `google-ads.yaml`)
- Google Sheets read via Sheets API (configure your sheet ID via env var, e.g. `PACING_SHEET_ID`)
- Account registry for customer ID lookups (your `accounts.json` or equivalent)

A working reference script lives in the private brain this skill was extracted from; if you'd like a starter template to adapt, open an issue.

---

## Usage

**Inline (single account, manual):**

> "Use the underspending-investigation skill to investigate `Example Property - Pmax`. Pacing variance: +12.5%."

The skill will:

1. Auto-load the six companion skills via the Skill tool
2. Run `scripts/investigate_underspend.py "Example Property - Pmax"`
3. Apply the diagnostic decision trees to the script output
4. Produce a standardized investigation report with root cause, evidence, and a specific budget recommendation (or no-action call)

**Parallel (orchestrated by a morning briefing):**

A morning-briefing orchestrator can launch multiple investigations in parallel:

```
Task(subagent_type="general-purpose",
     description="Investigate Property A underspending",
     prompt="Use the underspending-investigation skill to investigate \"Property A - Pmax\". Pacing context: +19.08% underspending.")

Task(subagent_type="general-purpose",
     description="Investigate Property B underspending",
     prompt="Use the underspending-investigation skill to investigate \"Property B - Pmax\". Pacing context: +14.00% underspending.")

# ...launched in a single message for parallel execution
```

Each parallel investigation runs in an isolated context, so per-account findings don't bleed into each other.

---

## Output Example

```
================================================================================
UNDERSPENDING INVESTIGATION: Example Property - Pmax
================================================================================

INVESTIGATION SUMMARY:
- Account: Example Property - Pmax
- Customer ID: 1234567890
- Date: 2026-05-28
- Investigation time: 45 seconds

================================================================================
ROOT CAUSE DIAGNOSIS
================================================================================

Primary Issue: Smart-bidding under-allocation despite strong unit economics

Evidence:
- Pacing Variance: +19.08% UNDERSPENDING
- Pmax 7-day budget utilization: 38.5%
- Pmax 7-day ROAS: 19.04x (Goal: >5x) ✅
- Pmax 7-day CPA: $10.41 (Goal: <$25) ✅

Explanation:
Pmax campaign cannot spend its allocated budget at current bid pressure, even
though every conversion is profitable. Per impression-share-diagnostics, Pmax
campaigns do not expose meaningful Search IS metrics; alternative diagnostics
(budget utilization + performance) confirm the pattern.

================================================================================
RECOMMENDATIONS
================================================================================

BUDGET RECOMMENDATION:
✅ Increase Monthly Budget: $3,099 → $3,335 (+7.6%)
✅ New Daily Budget: $107.58/day

Rationale:
- Pacing variance (+19.08%) exceeds portfolio tolerance
- Performance is elite (19x ROAS, $10 CPA — far better than goal)
- Conservative 7.6% increase per budget-recommendation-calculator methodology
- Adjustment Factor 0.4 (conservative because >15% variance and late in month)

Confidence Level: Medium
================================================================================
```

---

## Companion Skills

This skill auto-loads six companion skills via the Skill tool. All are in this repo:

- `campaign-line-filtering`
- `portfolio-pacing-rules`
- `google-sheets-lookups`
- `google-ads-query-patterns`
- `impression-share-diagnostics`
- `budget-recommendation-calculator`

The investigation will not work correctly without these; the diagnostic frameworks live inside them.

---

## License

MIT — use freely in your own brain / repo / agency.
