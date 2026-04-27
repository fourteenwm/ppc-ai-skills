---
name: portfolio-health-prioritization
description: Account prioritization criteria for portfolio health monitoring and daily briefings. Auto-invoke when determining which accounts need investigation, prioritizing daily actions, running portfolio health checks, or deciding investigation order. Provides 5-tier priority system with portfolio-specific thresholds (Portfolio A ±5%, Portfolio B ±8%).
allowed-tools: [Read]
---

# Portfolio Health Prioritization Skill

**Purpose:** Provides standardized criteria for prioritizing Google Ads accounts that need investigation or action in portfolio health monitoring workflows.

**Type:** Domain knowledge skill (auto-invoked)

---

## Quick Reference: Priority Tiers

### 🚨 Tier 1: CRITICAL (Investigate First)
**Criteria:**
- Pacing variance >±15% (any portfolio)
- Account completely off pace (2x expected or 50% of expected)
- Major performance degradation (CPA doubled, ROAS halved)

**Action Required:** Same day, immediately
**Typical Count:** 0-3 accounts per portfolio per day
**Investigation:** Mandatory deep dive

---

### ⚠️ Tier 2: HIGH PRIORITY (Investigate Today)
**Criteria:**
- **Portfolio B/Portfolio C:** Pacing variance >±8% (outside tolerance)
- **Portfolio A:** Pacing variance >±5% (stricter SLA)
- Zero spenders (campaigns with $0 spend MTD)
- Recent pacing deterioration (variance worsening >5% in 7 days)

**Action Required:** Within 24 hours
**Typical Count:** 3-10 accounts per portfolio per day
**Investigation:** Recommended deep dive

---

### ℹ️ Tier 3: MEDIUM PRIORITY (Investigate This Week)
**Criteria:**
- Pacing near threshold (Portfolio B: 5-8%, Portfolio A: 3-5%)
- Conversion tracking issues (sudden drops)
- Ad disapprovals (multiple ads affected)
- Campaign end dates (ending in 7-14 days)

**Action Required:** Within 7 days
**Typical Count:** 5-15 accounts per portfolio
**Investigation:** Optional, based on capacity

---

### ✅ Tier 4: LOW PRIORITY (Monitor)
**Criteria:**
- Within tolerance but near threshold
- Historical patterns (seasonal, expected variance)
- Stable performance with minor fluctuations

**Action Required:** Monitor for 3-5 days
**Typical Count:** Most of portfolio
**Investigation:** Not needed unless pattern changes

---

### ⭕ Tier 5: NO ACTION NEEDED
**Criteria:**
- Pacing within tolerance (Portfolio B: <±8%, Portfolio A: <±5%)
- Performance acceptable (CPA on goal, ROAS meeting targets)
- No recent issues or alerts

**Action Required:** None
**Typical Count:** 70-85% of portfolio
**Investigation:** Not applicable

---

## Portfolio-Specific Thresholds

### Portfolio A Portfolio
**Pacing Tolerance:** ±5% monthly (stricter SLA)
**Rationale:** High-visibility client, frequent reporting, strict budget accountability

**Priority Thresholds:**
- 🚨 Critical: >±15%
- ⚠️ High: >±5%
- ℹ️ Medium: 3-5%
- ✅ Low: 2-3%
- ⭕ On Pace: <±2%

**Special Considerations:**
- Brand campaign cap: 15% of total spend (flag if exceeded)
- ROAS-focused (primary KPI)
- No shared budgets (need granular control)

**Accounts:**
- Acme Plumbing (CID: [CUSTOMER_ID])
- Best HVAC (CID: [CUSTOMER_ID])
- City Dental (CID: [CUSTOMER_ID])
- Account D (multiple accounts)

---

### Portfolio B Portfolio
**Pacing Tolerance:** ±8% monthly (standard)
**Rationale:** More flexible pacing, focus on cost efficiency

**Priority Thresholds:**
- 🚨 Critical: >±15%
- ⚠️ High: >±8%
- ℹ️ Medium: 5-8%
- ✅ Low: 3-5%
- ⭕ On Pace: <±3%

**Special Considerations:**
- CPA-focused (primary KPI, some testing ROAS)
- Shared budgets common (GEO + Bedroom campaigns)
- Campaign line filtering (Pmax/Dgen/Search account designations)

**Campaign Structure:**
- Original "Core 4": Brand, GEO, Bedroom, GDN Remarketing
- Current: Added Pmax/Demand Gen, paused GDN Remarketing

---

### Portfolio C Portfolio
**Pacing Tolerance:** ±8% monthly (same as Portfolio B)
**Rationale:** Mid-tier accounts, similar to Portfolio B management style

**Priority Thresholds:**
- 🚨 Critical: >±15%
- ⚠️ High: >±8%
- ℹ️ Medium: 5-8%
- ✅ Low: 3-5%
- ⭕ On Pace: <±3%

**Accounts:**
- Portfolio C - Multi-region (CID: [CUSTOMER_ID])
- ProClean (CID: [CUSTOMER_ID])
- Quick Fix (CID: [CUSTOMER_ID])

---

## Prioritization Decision Tree

### Step 1: Check Critical Thresholds

```
START: New account flagged in portfolio health check

Is pacing variance >±15%?
 └─ YES → 🚨 TIER 1 CRITICAL (investigate immediately)
 └─ NO → Continue to Step 2
```

### Step 2: Check Portfolio-Specific Thresholds

```
Which portfolio is this account in?
 ├─ Portfolio A → Is variance >±5%?
 │ └─ YES → ⚠️ TIER 2 HIGH PRIORITY
 │ └─ NO → Continue to Step 3
 │
 └─ Portfolio B/Portfolio C → Is variance >±8%?
 └─ YES → ⚠️ TIER 2 HIGH PRIORITY
 └─ NO → Continue to Step 3
```

### Step 3: Check Secondary Indicators

```
Does account have any of these issues?
 ├─ Zero spender (MTD spend = $0) → ⚠️ TIER 2 HIGH PRIORITY
 ├─ Recent deterioration (variance +5% worse in 7 days) → ⚠️ TIER 2 HIGH PRIORITY
 ├─ Conversion tracking issues → ℹ️ TIER 3 MEDIUM PRIORITY
 ├─ Ad disapprovals → ℹ️ TIER 3 MEDIUM PRIORITY
 ├─ Campaign ending soon (7-14 days) → ℹ️ TIER 3 MEDIUM PRIORITY
 └─ None of the above → Continue to Step 4
```

### Step 4: Check Proximity to Threshold

```
Is variance approaching threshold?
 ├─ Portfolio A: 3-5% → ℹ️ TIER 3 MEDIUM PRIORITY
 ├─ Portfolio B/Portfolio C: 5-8% → ℹ️ TIER 3 MEDIUM PRIORITY
 ├─ Any portfolio: 2-3% → ✅ TIER 4 LOW PRIORITY (monitor)
 └─ Within tolerance → ⭕ TIER 5 NO ACTION NEEDED
```

---

## Focus Rules (Investigation Order)

### Rule 1: Underspending > Overspending

**Why:**
- Underspending issues typically have **quick fixes** (budget increase, remove bid caps)
- Overspending issues often require **strategic changes** (pause campaigns, reduce bids, improve quality)

**Exception:** Overspending >±15% = critical (may exceed client budget)

**Practical Application:**
```
Accounts to investigate:
1. Account A: +12% underspending (Portfolio B)
2. Account B: -10% overspending (Portfolio B)
3. Account C: +9% underspending (Portfolio B)

Investigation Order:
1st: Account A (+12% underspending - highest variance, quick fix potential)
2nd: Account C (+9% underspending - quick fix potential)
3rd: Account B (-10% overspending - needs strategic review)
```

---

### Rule 2: Portfolio A > Other Portfolios

**Why:**
- **Stricter client SLA** (±5% vs ±8%)
- **Higher visibility** accounts (larger spend, more frequent reporting)
- **Client escalation risk** (Portfolio A has tighter requirements)

**Practical Application:**
```
Accounts to investigate:
1. Account A: +6% underspending (Portfolio A)
2. Account B: +9% underspending (Portfolio B)
3. Account C: +6% underspending (Portfolio B)

Investigation Order:
1st: Account A (Portfolio A +6% - outside ±5% tolerance)
2nd: Account B (Portfolio B +9% - higher variance)
3rd: Account C (Portfolio B +6% - within ±8% tolerance, lower priority)
```

---

### Rule 3: Recent Changes > Historical Patterns

**Why:**
- Accounts with **recent budget changes** may be in ramp-up period (normal, monitor only)
- Accounts with **sudden variance shifts** indicate new issues (investigate)
- Accounts with **historical patterns** (seasonal) may not need intervention

**Practical Application:**
```
Accounts to investigate:
1. Account A: +10% underspending (budget increased 3 days ago)
2. Account B: +10% underspending (was on pace 7 days ago, suddenly shifted)
3. Account C: +10% underspending (historically underspends in Q1 every year)

Investigation Order:
1st: Account B (sudden shift - new issue, investigate root cause)
2nd: Account A (recent budget increase - check if ramp-up on track, may just need monitoring)
3rd: Account C (historical pattern - seasonal, may not need action)
```

---

### Rule 4: High Variance > Near Threshold

**Why:**
- **High variance** (>±10%) = significant impact, needs immediate attention
- **Near threshold** (5-8% Portfolio B, 3-5% Portfolio A) = monitor, may self-correct

**Practical Application:**
```
Accounts to investigate:
1. Account A: +12% underspending (Portfolio B)
2. Account B: +6% underspending (Portfolio B)
3. Account C: +5% underspending (Portfolio A)

Investigation Order:
1st: Account A (+12% - high variance, well outside tolerance)
2nd: Account C (+5% Portfolio A - exactly at Portfolio A threshold)
3rd: Account B (+6% Portfolio B - within ±8% tolerance, monitor)
```

---

## Daily Briefing Workflow Integration

### Daily Health Check Use Case

**Typical workflow:**

1. **Run your portfolio health check** (a script that flags issues like pacing variance, zero-spenders, conversion drops, etc. — replace with your own equivalent)
 - Returns 50-100 accounts with various issues

2. **Apply Portfolio Health Prioritization Skill**
 - Classify all accounts into 5 tiers
 - Identify top 3-5 accounts for deep investigation

3. **Launch Investigation Agents** (parallel)
 - Tier 1 accounts: All investigated (0-3 accounts)
 - Tier 2 accounts: Top 3-5 investigated
 - Tier 3+: Listed in briefing, not investigated

4. **Generate Briefing**
 - Critical: {count} accounts
 - High Priority: {count} accounts
 - Investigated: {count} accounts (with findings)
 - Other Issues: {count} accounts (monitoring only)

---

## Selection Algorithm for Daily Prioritization

**Goal:** Select **3-5 accounts** for deep investigation from potentially 20-30 flagged accounts

**Algorithm:**

```python
# Pseudocode for account selection
accounts = get_all_flagged_accounts()

# Step 1: Separate by tier
tier_1 = [acc for acc in accounts if acc.variance > 15]
tier_2_a = [acc for acc in accounts if acc.portfolio == 'Portfolio A' and acc.variance > 5]
tier_2_other = [acc for acc in accounts if acc.portfolio != 'Portfolio A' and acc.variance > 8]
tier_2_zero = [acc for acc in accounts if acc.mtd_spend == 0]

# Step 2: Prioritize within tiers
tier_2_underspend = [acc for acc in (tier_2_a + tier_2_other) if acc.variance > 0]
tier_2_overspend = [acc for acc in (tier_2_a + tier_2_other) if acc.variance < 0]

# Step 3: Build investigation list (max 5)
investigation_list = []

# All Tier 1 (critical) get investigated
investigation_list.extend(tier_1)

# Fill remaining slots with Tier 2, prioritizing:
# 1. Portfolio A accounts
# 2. Underspending accounts
# 3. Highest variance
remaining_slots = 5 - len(investigation_list)

candidates = (
 sorted(tier_2_a, key=lambda x: abs(x.variance), reverse=True) +
 sorted(tier_2_underspend, key=lambda x: abs(x.variance), reverse=True) +
 sorted(tier_2_overspend, key=lambda x: abs(x.variance), reverse=True) +
 tier_2_zero
)

investigation_list.extend(candidates[:remaining_slots])

return investigation_list[:5] # Max 5 accounts
```

---

## Real-World Example: Daily Prioritization

### Scenario: AI Error Analysis Returns 25 Flagged Accounts

**Input Data:**
```
Tier 1 (Critical >±15%): 2 accounts
- Portfolio B - ProClean: +18.5% underspending
- Portfolio A - Best HVAC: -16.2% overspending

Tier 2 (High Priority):
- Portfolio A (>±5%): 3 accounts
 - City Dental: +6.8% underspending
 - Account E: +5.3% underspending
 - Acme Plumbing PCV: -5.1% overspending

- Portfolio B (>±8%): 8 accounts
 - Quick Fix: +12.3% underspending
 - Metro Auto: +9.7% underspending
 - Account G: -10.2% overspending
 - [5 more accounts between ±8-10%]

- Zero Spenders: 3 accounts

Tier 3 (Medium Priority): 9 accounts (near threshold, ad disapprovals, etc.)
```

**Apply Prioritization:**

1. **All Tier 1 accounts** (2 accounts):
 - Portfolio B - ProClean (+18.5%)
 - Portfolio A - Best HVAC (-16.2%)

2. **Top 3 from Tier 2** (using focus rules):
 - Priority 1: Portfolio B - Quick Fix (+12.3% underspending - high variance + underspending)
 - Priority 2: Portfolio A - City Dental (+6.8% underspending - Portfolio A priority)
 - Priority 3: Portfolio B - Metro Auto (+9.7% underspending - underspending focus)

**Investigation List (5 accounts):**
1. Portfolio B - ProClean (+18.5%) - CRITICAL
2. Portfolio A - Best HVAC (-16.2%) - CRITICAL
3. Portfolio B - Quick Fix (+12.3%) - HIGH PRIORITY
4. Portfolio A - City Dental (+6.8%) - HIGH PRIORITY (Portfolio A)
5. Portfolio B - Metro Auto (+9.7%) - HIGH PRIORITY

**Not Investigated (mentioned in briefing only):**
- 5 other Portfolio B accounts with ±8-10% variance
- 2 other Portfolio A accounts with ±5% variance
- 3 zero spenders
- 9 Tier 3 accounts

**Briefing Summary:**
- Investigated: 5 accounts (with root cause + recommendations)
- Other High Priority: 10 accounts (listed, not investigated)
- Medium Priority: 9 accounts (listed by category)
- On Pace: ~70 accounts (count only)

---

## When to Use This Skill

### Auto-Invoked When:
- Running daily portfolio health checks
- Determining which accounts need investigation
- Prioritizing daily actions across portfolio
- User asks "what needs my attention today"
- Portfolio health check workflows
- Selecting accounts for batch optimizations

### Manual Invocation:
- Custom portfolio queries ("Show me high priority Portfolio B accounts")
- Weekly/monthly portfolio reviews
- Client reporting (prioritized account lists)
- Ad-hoc "what should I look at first?" questions

---

## Integration with Other Skills

### Skills This Prioritization Feeds Into:

**Directly Used By:**
- Your portfolio settings audit agent/workflow (external — replace with your own)

**Indirectly Impacts:**
- Your underspending investigation workflow (external)
- [`portfolio-pacing-rules`](../portfolio-pacing-rules/) - References same thresholds
- [`budget-recommendation-calculator`](../budget-recommendation-calculator/) - Urgency affects recommendation timing

### Skills Referenced By This Skill:

- [`portfolio-pacing-rules`](../portfolio-pacing-rules/) - Pacing thresholds (±8% Portfolio B, ±5% Portfolio A)
- Your sheets-lookup helper (external — internal data plumbing, replace with your own sheet-reading code)

---

## Related Skills & Documentation

**Related Skills:**
- [`portfolio-pacing-rules`](../portfolio-pacing-rules/) - Pacing thresholds and budget management philosophy
- [`budget-recommendation-calculator`](../budget-recommendation-calculator/) - Used after prioritization to generate recommendations

**External (replace with your own):**
- Sheets-lookup helper — data source for pacing variance
- Underspending investigation agent/workflow — investigates accounts flagged by prioritization

---

**Created:** 2025-11-01
**Based On:** Portfolio health monitoring best practices
**Status:** Active
