# Underspending Investigation

Diagnose root causes of Google Ads account underspending and produce a specific, data-backed budget recommendation (or an explicit no-action call when a budget increase would make things worse).

**The pain point:** "Account X is underspending" is one of the most repeated tickets in any managed-portfolio PPC shop, and the wrong answer ("just raise the budget") burns money on accounts that are rank-constrained, quality-constrained, demand-constrained, or in a smart-bidding ramp-up window. This skill encodes the diagnostic discipline — a six-framework decision tree applied against standard script output — so the recommendation is always traceable to evidence, and budget increases only happen when they will actually convert into spend at an acceptable CPA / ROAS.

---

## What's Inside

- Six-framework diagnostic protocol (campaign filtering → pacing rules → pacing-data lookups → GAQL → impression share → budget calc) — the three core frameworks ship as required companion skills in this repo and auto-load at investigation start; the rest are inlined in the protocol or optional references
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
mkdir -p .claude/skills/underspending-investigation/scripts
curl -o .claude/skills/underspending-investigation/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/underspending-investigation/SKILL.md
curl -o .claude/skills/underspending-investigation/README.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/underspending-investigation/README.md
curl -o .claude/skills/underspending-investigation/scripts/investigate_underspend.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/underspending-investigation/scripts/investigate_underspend.py
```

Then install the three required companion skills (also in this repo):

```bash
for skill in portfolio-pacing-rules impression-share-diagnostics budget-recommendation-calculator; do
  mkdir -p .claude/skills/$skill
  curl -o .claude/skills/$skill/SKILL.md \
    https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/$skill/SKILL.md
done
```

Optional — the GAQL reference used when extending the shipped script:

```bash
mkdir -p .claude/skills/gaql-query-patterns
curl -o .claude/skills/gaql-query-patterns/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/gaql-query-patterns/SKILL.md
```

---

## The Investigation Script (Ships With This Skill)

[`scripts/investigate_underspend.py`](scripts/investigate_underspend.py) — self-contained, read-only, Google Ads API only (no sheet or database dependencies):

```bash
# By account name (resolved via accounts.md, or by walking your MCC)
python scripts/investigate_underspend.py "Acme Plumbing - Search"

# By customer ID
python scripts/investigate_underspend.py --cid 1234567890

# Pace against the contracted monthly budget instead of the daily-budget estimate
python scripts/investigate_underspend.py --cid 1234567890 --monthly-budget 5000
```

**Output sections** (the data contract the skill's diagnostic steps consume):

1. **Campaign Spend Analysis (last 7 days)** — per-campaign budget, utilization %, status, bidding strategy, spend / impressions / clicks / conversions / value
2. **Impression Share Analysis** — Search IS, Budget Lost IS, Rank Lost IS with a threshold-based root-cause readout per campaign (Pmax is flagged separately — its Search IS metrics are not diagnostically meaningful)
3. **Month-to-Date Pacing Analysis** — monthly budget, MTD spend, expected spend at current day-of-month, variance %

**Prerequisites:** `google-ads.yaml` at project root (see [google-ads-api-setup](../google-ads-api-setup/)) and `pip install google-ads pyyaml`. Optional: an `accounts.md` registry at project root for name→CID resolution (format documented in the script header).

The SKILL.md's "Script Contract" section documents how to adapt the script to your own infrastructure — pacing dashboard reads, optimization logs, custom account registries.

---

## Usage

**Inline (single account, manual):**

> "Use the underspending-investigation skill to investigate `Example Property - Pmax`. Pacing variance: +12.5%."

The skill will:

1. Auto-load the three required companion skills via the Skill tool
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

This skill auto-loads three required companion skills via the Skill tool. All three are in this repo, and the investigation will not work correctly without them — the core diagnostic frameworks live inside:

- `portfolio-pacing-rules`
- `impression-share-diagnostics`
- `budget-recommendation-calculator`

Optional, also in this repo: `gaql-query-patterns` (GAQL templates, useful when extending the shipped script) and `change-history-checker` (API-based recent-changes lookup for the recent-optimizations step).

The protocol's other two frameworks — campaign-line filtering and pacing-data lookups — come from internal, portfolio-specific skills that don't publish; their diagnostic content is fully inlined in SKILL.md, so nothing is missing. Supply your own account-naming conventions and budget/pacing data sources.

---

## License

MIT — use freely in your own brain / repo / agency.
