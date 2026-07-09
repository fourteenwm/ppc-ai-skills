---
name: underspending-investigation
description: Investigate Google Ads accounts with significant underspending (pacing variance beyond your portfolio's tolerance). Auto-invoke when user says "investigate [account] underspending", "[account] underspending", "why is [account] underspending", or "diagnose underspend for [account]". Runs a universal investigation script, applies six diagnostic frameworks, and synthesizes a root-cause diagnosis with a budget recommendation (or explicit no-action call). Read-only — no mutations.
allowed-tools: [Read, Bash, Grep, Glob, Skill]
---

# Underspending Investigation

**Purpose:** Investigate why a Google Ads account is underspending and determine the root cause with actionable, data-backed recommendations.

**Type:** Read-only investigation skill. Reads campaign, impression share, and pacing data; never writes to Google Ads.

---

## Inputs

The skill expects:

- **`{ACCOUNT_NAME}`** — full account name (e.g., `Example Property - Pmax`)
- **`{ADDITIONAL_CONTEXT}`** (optional) — pacing variance or other prior context (e.g., `Underspending by +12.5%`)

When invoked via `Task(subagent_type="general-purpose", prompt="Use the underspending-investigation skill to investigate <account>…")`, the orchestrator substitutes both values into the prompt.

---

## Auto-Load Domain Knowledge Skills

**CRITICAL:** At the start of every investigation, auto-invoke these companion skills via the Skill tool to load the frameworks, formulas, and decision trees:

1. `campaign-line-filtering` — Which campaigns to analyze based on account designation (Pmax / Demand Gen / Search by name suffix)
2. `portfolio-pacing-rules` — Pacing thresholds and budget management philosophy for your portfolios
3. `google-sheets-lookups` — Reference for budget and pacing data sources
4. `google-ads-query-patterns` — GAQL patterns for data extraction
5. `impression-share-diagnostics` — Root-cause diagnosis framework for Search campaigns
6. `budget-recommendation-calculator` — Conservative budget calculation methodology

Do this BEFORE analyzing script output. These six companion skills are each shipped as standalone skills in this repo.

---

## Prerequisites

1. **Google Ads API credentials** — `google-ads.yaml` at project root (see [`google-ads-api-setup`](../google-ads-api-setup/))
2. **Python packages** — `pip install google-ads pyyaml`
3. **Optional: `accounts.md`** at project root — a name→CID registry so investigations can be invoked by account name (format documented in the script header). Without it, the script falls back to walking your MCC via the `login_customer_id` in `google-ads.yaml`.

---

## Investigation Protocol

### STEP 0: Run the Universal Investigation Script

The script ships with this skill at [`scripts/investigate_underspend.py`](scripts/investigate_underspend.py):

```bash
# By account name (resolved via accounts.md, or by walking the MCC)
python scripts/investigate_underspend.py "{ACCOUNT_NAME}"

# By customer ID
python scripts/investigate_underspend.py --cid 1234567890

# Pace against the contracted monthly budget instead of the daily-budget estimate
python scripts/investigate_underspend.py "{ACCOUNT_NAME}" --monthly-budget 5000
```

The script:

1. Resolves the customer ID for the account (`accounts.md` registry, MCC walk, or `--cid`)
2. Runs a 7-day campaign spend analysis (budget utilization, performance)
3. Pulls impression share metrics (Search IS, Budget Lost IS, Rank Lost IS) with a threshold-based root-cause readout per campaign (Pmax is flagged separately — its Search IS metrics are not meaningful)
4. Computes month-to-date pacing (MTD spend vs. expected spend at today's day-of-month, variance %) from campaign daily budgets — or from the true contracted budget when `--monthly-budget` is supplied

The script handles data collection. The skill's job is to read/interpret the script output, apply the diagnostic frameworks from the auto-loaded companion skills, and synthesize findings into actionable recommendations. To wire the script into your own pacing dashboard or optimization logs, see "Script Contract" below.

---

### Step 1: Recent Optimizations Check

**Reference Skill:** `google-sheets-lookups`

**Goal:** Determine if recent budget changes explain the underspending.

**Decision Point (from `portfolio-pacing-rules`):**

- **IF recent budget increase found (last 3-7 days):**
  - Diagnosis: "Normal ramp-up period after budget increase"
  - Recommendation: "Monitor over next 3-5 days, no action needed"
  - **STOP investigation here** ✅
- **IF budget increase 7-14 days ago:**
  - Note in findings; CONTINUE to Step 2 (should be ramped up by now)
- **IF no recent budget changes:**
  - CONTINUE to Step 2

---

### Step 2: Campaign Spend Pattern Analysis

**Reference Skill:** `campaign-line-filtering`

**Goal:** Understand which campaigns are spending and how budgets are structured.

**Key Analysis:**

- **Budget structure:** Shared vs. individual budgets
- **Budget utilization %:** MTD spend ÷ MTD budget allocation
- **Campaign status:** ENABLED, PAUSED (with MTD spend), vs. ENDED (excluded)
- **Bidding strategy:** Smart bidding type (Max Conversions, Max Conversion Value, etc.)

**What the script output gives you:**

- Per-campaign 7-day budget, spend, utilization %, status, and bidding strategy (campaigns with $0 spend in the window are excluded from display)
- Shared vs. individual budget type per campaign
- MTD spend and pacing variance (STEP 3 of the script output)

**Skill analysis:**

- Filter the campaign list by line designation per `campaign-line-filtering` (Pmax / Demand Gen / Search by account name suffix)
- Set aside ENDED / REMOVED campaigns when diagnosing current pacing
- Note unusual patterns (paused campaigns with spend, shared-budget imbalances)
- Identify primary spending campaigns

---

### Step 3: Impression Share Analysis (Root Cause Diagnosis)

**Reference Skill:** `impression-share-diagnostics`

**Goal:** Diagnose WHY underspending is happening using impression share metrics.

**Diagnostic Framework (from `impression-share-diagnostics`):**

| Search IS | Budget Lost IS | Rank Lost IS | Diagnosis | Next Step |
|-----------|----------------|--------------|-----------|-----------|
| <70% | >30% | >50% | Budget too low | Step 4: Calculate budget recommendation |
| <70% | <10% | >60% | Quality issues | Recommend quality improvements |
| >80% | <10% | <10% | Low demand | Normal (or consider reducing budget) |
| Any | Any | Any | Recent budget ↑ (if Step 1 found this) | Monitor, no action |

**Critical Context (from `impression-share-diagnostics`):**

- **Rank Lost IS is informational**, not a primary optimization target
- High Rank Lost IS (60-80%) is common in competitive auctions
- Primary focus: Budget Lost IS (indicates spend potential)
- **Do NOT optimize TO a Rank Lost IS target**

**Performance Guardrails (from `portfolio-pacing-rules`):**

- Check if CPA is acceptable (within goal or <20% over)
- Check if ROAS is acceptable (within goal or >80% of target)
- If performance is failing, do NOT recommend budget increase

**Performance Max caveat:** Pmax campaigns do NOT expose meaningful Search IS / Budget Lost IS / Rank Lost IS. For Pmax, use alternative diagnostics: budget utilization %, performance vs. goal, asset performance scores, auction insights (when available).

---

### Step 4: Budget Recommendation (If Applicable)

**Reference Skill:** `budget-recommendation-calculator`

**Goal:** Calculate a specific, conservative budget recommendation.

**When to recommend a budget increase:**

- ✅ Pacing variance exceeds your portfolio's tolerance
- ✅ Budget Lost IS >10% (spend potential exists) — or for Pmax, low budget utilization with strong performance
- ✅ CPA / ROAS performance acceptable
- ✅ No recent budget increase in last 7 days
- ✅ At least 5 days into the month

**Calculation Method (from `budget-recommendation-calculator`):**

```
Target Monthly Budget = Current Monthly Budget × (1 + (Pacing Variance × Adjustment Factor))

Where:
- Pacing Variance = from script output
- Adjustment Factor = 0.5 (standard conservative — only close half the gap)

HARD CAP: Never exceed 10% increase in a single change
```

**Example:**

```
Current Monthly Budget: $1,000
Pacing Variance:        +13.18%
Adjustment Factor:      0.5

Target = $1,000 × (1 + (0.1318 × 0.5))
       = $1,000 × 1.0659
       = $1,065.90

Recommended: $1,065 (6.5% increase)
Daily Budget: $1,065 ÷ 31 days = $34.35/day
```

**When NOT to recommend a budget increase:**

- ❌ CPA significantly above goal (>20% over)
- ❌ Recent budget increase within last 7 days
- ❌ Search IS >80% + Budget Lost IS <10% (low demand scenario)
- ❌ Less than 5 days into month (early-month variance)

---

### Adaptive Investigation

The skill is NOT required to run all steps. Use judgment:

- **Stop early** if Step 1 fully explains the underspending (e.g., recent budget increase)
- **Add extra steps** if you find something unexpected (e.g., paused campaigns, ad schedule restrictions)
- **Pivot** if the data suggests a different investigation path
- **Skip Step 4** if diagnosis is NOT "budget too low"

**Additional checks (if needed):**

- Ad schedule restrictions (only running certain hours?)
- Geographic targeting (too narrow?)
- Negative keyword conflicts
- Disapproved ads/assets
- **Display remarketing campaigns:** check for "Bid setting limited" status (see below)

---

### Display Campaign Diagnostic (When Applicable)

**When to check:** Account has Display / GDN remarketing campaigns with low spend.

**Key Diagnostic:** Look for "Bid setting limited" status in the Google Ads UI.

**Pattern:**

- Campaign status shows "Bid setting limited"
- Very low click volume (e.g., 7 clicks over 18 days)
- Spending well below daily budget
- Bidding strategy: Maximize Clicks with max CPC limit

**Root Cause:** Max CPC bid cap (e.g., $2-3) is too low for Display network auctions — campaign can't compete for impressions.

**Standard Fix Pattern:**

- Increase max CPC bid limit to a floor that gives the algorithm headroom (often around $4.00 for managed-portfolio remarketing — tune to your inventory)
- Provides headroom to compete while maintaining a reasonable ceiling

**Verification Steps:**

1. Check campaign settings → Bidding → "Maximum CPC bid limit"
2. If under your floor, recommend increasing
3. Expected outcome: spend increases toward budget within 2-3 days
4. Expected CPCs settle below your new cap after auctions normalize

**Note:** This is a separate diagnostic from Search campaign IS analysis — Display campaigns don't have Search IS metrics.

---

## Tools Used

- **Skill** — Auto-invoke the six domain knowledge companion skills (CRITICAL — use at start)
- **Read** — Read sheet exports, read script output
- **Bash** — Run the investigation script
- **Grep / Glob** — Find supporting scripts if a deep dive is needed

---

## Script Contract (Adapting to Your Own Data Sources)

This skill ships with a working investigation script at `scripts/investigate_underspend.py` — Google Ads API only, no sheet or database dependencies. The contract below documents what any implementation must output, so you can extend the shipped script (or swap in your own) and the skill's diagnostic steps keep working.

**Required script behavior:**

- Accept `{ACCOUNT_NAME}` as a positional argument (and / or `--cid <numeric_id>` as fallback)
- Resolve customer ID for the account
- Output a 7-day campaign spend section (per-campaign budget, utilization %, status, bidding strategy, performance metrics)
- Output an impression share section for Search / Pmax campaigns (Search IS, Budget Lost IS, Rank Lost IS)
- Output a month-to-date pacing section (monthly budget, MTD spend, variance %, days elapsed)
- Optionally output recent optimization log entries

**Extension hooks (where the shipped script is designed to be adapted):**

- **Pacing dashboard:** the shipped script computes MTD pacing from campaign daily budgets, with `--monthly-budget` as the manual override. If you maintain a pacing dashboard (Google Sheet or otherwise) that holds contracted monthly budgets, replace the STEP 3 budget lookup with a read against it — the highest-value adaptation, because contracted budgets and daily-budget math diverge whenever budgets change mid-month.
- **Optimization log:** if you keep a budget-change log, print recent entries as an extra output section — Step 1 of the protocol consumes it directly. (`change-history-checker` in this repo is an API-based alternative for the same question.)
- **Account registry:** swap `accounts.md` for your own registry (JSON, sheet, or database) inside the script's `resolve_account_name()`.

---

## Output Format

Return findings in this exact structure:

```
================================================================================
UNDERSPENDING INVESTIGATION: {ACCOUNT_NAME}
================================================================================

INVESTIGATION SUMMARY:
- Account: {Full account name}
- Customer ID: {CID}
- Date: {Current date}
- Investigation time: {How long it took}

================================================================================
ROOT CAUSE DIAGNOSIS
================================================================================

Primary Issue: {Budget Constraint | Quality Issues | Low Demand | Ramp-Up Period | Other}

Evidence:
- Pacing Variance: +X.X% (from pacing dashboard)
- Search Impression Share: XX%
- Budget Lost IS: XX%
- Rank Lost IS: XX%
- CPA: $XX.XX (Goal: $XX.XX) {✅ or ❌}

Explanation:
{2-3 sentence explanation of WHY underspending is happening}
{Reference the diagnostic framework from impression-share-diagnostics}

================================================================================
DETAILED FINDINGS
================================================================================

Step 1: Recent Optimizations
{Summary from script output — any recent budget changes?}

Step 2: Campaign Spend Analysis
{Filtered campaigns, budget structure, utilization %}
{Note: Apply line-designation filtering per campaign-line-filtering}

Step 3: Impression Share Analysis
{IS metrics per campaign, interpreted using impression-share-diagnostics decision tree}

{Any additional investigation steps taken}

================================================================================
RECOMMENDATIONS
================================================================================

{Use budget-recommendation-calculator framework}

BUDGET RECOMMENDATION:
{If recommending increase:}
✅ Increase Monthly Budget: $X,XXX → $X,XXX (+X.X%)
✅ New Daily Budget: $XX.XX/day

Rationale:
- Pacing variance (+X.X%) exceeds your portfolio's tolerance
- Budget Lost IS (XX%) indicates spend potential
- CPA performance acceptable (within goal)
- Conservative X.X% increase per budget-recommendation-calculator methodology

Expected Outcome:
- Reduce pacing variance from +X.X% to within tolerance range
- Maintain acceptable CPA/ROAS performance
- Algorithm will ramp up over 3-5 days

{If NOT recommending increase:}
❌ Do NOT Increase Budget

Reason: {CPA over goal / Recent budget change / Low demand / etc.}
{Explanation using budget-recommendation-calculator decision tree}

QUALITY IMPROVEMENTS (if applicable):
{Secondary recommendations for quality score, ad relevance, etc.}

MONITORING:
{Items to watch over next 5-7 days}

Confidence Level: {High | Medium | Low}

================================================================================
```

---

## Success Criteria

Investigation is successful if:

1. ✅ All six domain-knowledge companion skills auto-invoked at the start
2. ✅ Clear root cause identified with evidence
3. ✅ Diagnostic frameworks from the companion skills applied correctly
4. ✅ Specific, actionable recommendations (exact budget amounts, not "increase budget")
5. ✅ WHY the underspending is happening is explained (not just WHAT)
6. ✅ Diagnosis backed by data from script output
7. ✅ Investigation path adapted based on findings (stopped early if appropriate)

---

## Important Notes

- **Auto-invoke companion skills FIRST** — load all six frameworks before analyzing script output
- **Be autonomous** — don't ask for permission at each step, just investigate
- **Be adaptive** — if Step 1 explains everything (ramp-up period), stop there
- **Be specific** — "Increase budget from $1,000 to $1,065 (+6.5%)" not just "increase budget"
- **Be data-driven** — every conclusion references script output metrics
- **Be efficient** — the script does the heavy lifting; you interpret and synthesize
- **Reference frameworks** — when explaining decisions, cite which framework was used

---

## Invocation Patterns

**Inline (single account, manual):**

> "Use the underspending-investigation skill to investigate `Example Property - Pmax`. Pacing variance: +12.5%."

**Parallel orchestration (used by a morning briefing orchestrator):**

The orchestrator launches N parallel `Task(subagent_type="general-purpose", …)` calls in a single message, each with a prompt that invokes this skill against one account. Parallelism + per-investigation context isolation are preserved at the Task layer; the skill itself runs identically.

---

## Companion Skills (Required)

All six are shipped in this repo as standalone skills:

- `campaign-line-filtering` — account-suffix → campaign-line filtering rules
- `portfolio-pacing-rules` — pacing thresholds and budget management philosophy (configure for your portfolios)
- `google-sheets-lookups` — sheet read patterns for pacing dashboards
- `google-ads-query-patterns` — GAQL templates for spend, IS, pacing, settings queries
- `impression-share-diagnostics` — IS decision tree and Pmax / Display caveats
- `budget-recommendation-calculator` — conservative budget calc methodology with decision tree

Install all six alongside this skill for full functionality.
