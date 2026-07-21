---
name: portfolio-pacing-rules
description: Portfolio-specific pacing thresholds, budget tolerances, and brand caps. Auto-invoke when analyzing pacing variance, checking if accounts are on pace, investigating underspending/overspending, or discussing portfolio-specific rules (Portfolio A ±5%, Portfolio B ±8%, Portfolio C). Also loads when user mentions specific portfolios by name.
allowed-tools: [Read]
---

# Portfolio Pacing Rules Skill

**Purpose:** Provides portfolio-specific pacing thresholds, budget tolerances, brand caps, and performance targets that auto-load when analyzing account performance.

**Type:** Domain knowledge skill (auto-invoked)

---

## Quick Reference: Pacing Thresholds by Portfolio

### Portfolio A
- **Budget Pacing:** ±5% monthly tolerance (95%-105%)
- **Brand Campaign Cap:** 15% maximum of total account spend
- **Primary KPI:** ROAS (Conversion Value / Cost)
- **Warning Zone:** >±5% (investigate)
- **Critical Zone:** >±10% (immediate action)

### Portfolio B
- **Budget Pacing:** ±8% monthly tolerance (92%-108%)
- **Brand Campaign Cap:** None (no restriction)
- **Primary KPI:** Cost per Conversion (testing ROAS on some accounts)
- **Warning Zone:** >±8% (investigate)
- **Critical Zone:** >±10% (immediate action)

### Portfolio C
- **Budget Pacing:** ±8% monthly tolerance (92%-108%)
- **Brand Campaign Cap:** None (no restriction)
- **Primary KPI:** Cost per Conversion
- **Warning Zone:** >±8% (investigate)
- **Critical Zone:** >±10% (immediate action)

---

## Universal Pacing Rules (All Portfolios)

### Critical Thresholds
- **Critical:** >±15% variance = Immediate investigation required (KPI miss, client escalation)
- **High Priority:** >±10% variance = Requires investigation
- **Warning:** >±8% variance = Monitor closely
- **On Pace:** Within portfolio tolerance = Acceptable

### Month-Start Normalization (Days 1-5)
- Early-month variance is expected (budget ramp-up period)
- Reduce severity tier for pacing variance in first 5 days
- Full threshold rules apply after Day 5
- Note: "Early-month variance expected to normalize by Day 7"

---

## Portfolio Constraints

### Portfolio A Accounts
**Strategic Context:**
- Budget pacing is non-negotiable (strict client KPI)
- ROAS optimization happens WITHIN pacing constraint
- Brand campaigns capped at 15% despite high efficiency (30-40x ROAS)
- AI campaigns (Pmax/DGen) are workhorses (60-70% of spend)
- Budget reallocation > budget cuts (maintain spend, improve efficiency)
- No shared budgets (need granular control for tight pacing)

**Account Examples:**
- Acme Plumbing (CID: [CUSTOMER_ID])
- Best HVAC (CID: [CUSTOMER_ID])
- City Dental (CID: [CUSTOMER_ID])
- Account D (multiple accounts)

**When to flag:**
- Pacing variance >±5%
- Brand spend >15% of total
- Any variance >±10% with <1 week left in month

### Portfolio B Accounts
**Strategic Context:**
- More relaxed pacing tolerance (±8% vs Portfolio A's ±5%)
- No brand campaign cap
- Primary metric: Cost per Conversion (some testing ROAS)
- Shared budgets common (GEO + Bedroom campaigns)
- Budget flexibility allows for performance optimization

**Account Structure:**
- Original "Core 4": Brand, GEO, Bedroom, GDN Remarketing
- Current: Added Pmax/Demand Gen, paused GDN Remarketing
- Shared budgets: GEO + Bedroom campaigns use shared budget

**When to flag:**
- Pacing variance >±8%
- Any variance >±10% with <1 week left in month
- Shared budget imbalance (one campaign taking >80%)

### Portfolio C
**Strategic Context:**
- Mid-tier accounts (single metro area)
- Similar constraints to Portfolio B (±8% pacing tolerance)
- 3 accounts total

**Accounts:**
- Portfolio C - Multi-region (CID: [CUSTOMER_ID])
- ProClean (CID: [CUSTOMER_ID])
- Quick Fix (CID: [CUSTOMER_ID])

**When to flag:**
- Pacing variance >±8%
- Any variance >±10% with <1 week left in month

---

## Performance Targets by Portfolio

### Portfolio A (ROAS Focus)

**Campaign ROAS Targets:**
- **Brand Campaigns:** 25-40x ROAS (elite, but capped at 15% spend)
- **Performance Max:** 15-20x ROAS (workhorse, scalable)
- **Demand Gen:** 15-20x ROAS (efficient, visual/discovery)
- **YouTube/Video:** 10-15x ROAS (supporting role)
- **GEO/Keyword Campaigns:** 5-10x ROAS (acceptable minimum)
- **Underperformers:** <5x ROAS (candidates for cuts/optimization)
- **Money Losers:** <1x ROAS (immediate action required)

**Format for Portfolio A reports:**
- Show ROAS (not "conversion value per cost")
- Example: "16.9x ROAS" (not "$16.90 per $1 spent")

### Portfolio B (CPA Focus)

**Cost per Conversion Targets:**
- Varies by property (based on lease value and market)
- Primary metric: Target CPA (not ROAS)
- Testing ROAS on select accounts as alternative metric
- Campaign hierarchy: Brand (lowest CPA) → Pmax → GEO/Bedroom → Demand Gen

**Format for Portfolio B reports:**
- Show Cost per Conversion (e.g., "$125 CPA")
- Only show ROAS if specifically testing that metric

---

## When to Use This Skill

### Auto-Invoked When:
- Checking if account is on pace
- Analyzing pacing variance
- Investigating underspending or overspending
- Evaluating campaign performance vs. targets
- User mentions "Portfolio A", "Portfolio B", or "Portfolio C"
- User asks "what's the pacing threshold for [portfolio]"
- Creating performance reports or summaries

### Data Sources Referenced:
- Your own budget/pacing tracking sheet — one pacing dashboard tab per portfolio (the Pacing Calculation section below shows what it needs to contain)
- Google Ads API: Campaign performance data
- Your own portfolio context files — strategic context and constraints

---

## Integration with Agents

### Agents/workflows that use this skill:
- Your portfolio settings audit agent/workflow — applies portfolio thresholds to pacing analysis
- Your underspending investigation workflow — uses pacing tolerances for diagnosis
- Your account-level error analysis — flags accounts outside portfolio-specific thresholds

All agent references above are internal — replace with your own equivalents. This skill is protocol-only and works with any agent setup.

### How to reference:
Agents and skills can reference this skill's rules directly. Claude will auto-load this skill when portfolio-specific pacing rules are needed.

---

## Budget Management Context (Smart Bidding)

### Primary Control Lever: Monthly Budget
- **YOU CANNOT MANUALLY ADJUST BIDS** with smart bidding (Max Conversions, Max Conversion Value)
- **Monthly budget is the primary lever** for controlling spend
- **Budget increases are conservative:** 5-10% monthly increases (not aggressive jumps)

### Budget Philosophy Hierarchy:
1. **#1 Priority:** Hit monthly spend targets (pacing within tolerance)
2. **#2 Priority:** Maintain acceptable CPA/ROAS goals
3. **Algorithm safety:** Avoid shocking smart bidding with large changes

### Why Conservative Increases (5-10%)?
- Smart bidding algorithms need 3-7 days to ramp up after budget changes
- Large budget jumps risk CPA spikes during adjustment period
- Multiple small increases > one large increase (safer, more controllable)
- Client trust requires predictable, controlled spend changes

---

## Pacing Calculation (Reference)

**Data Source:** Pacing Dashboard sheet (auto-calculated daily)

**Formula:**
```
Pacing Variance = % Through Month - % Spent

Where:
- % Through Month = (Current Day ÷ Days in Month) × 100
- % Spent = (MTD Spend ÷ Monthly Budget) × 100
```

**Example:**
- Day 21 of 31 → % Through Month = 67.74%
- MTD Spend: $513 / Monthly Budget: $1,000 → % Spent = 51.30%
- Pacing Variance: 67.74% - 51.30% = +16.44% (UNDERSPENDING)

**Interpretation:**
- **Positive variance (+X%):** UNDERSPENDING (spent less than expected by now)
- **Negative variance (-X%):** OVERSPENDING (spent more than expected by now)
- **Zero variance (0%):** PERFECT PACING (spent exactly as expected)

**IMPORTANT:** This calculation is already done in Pacing Dashboard sheet (Column E). You don't need to recalculate it manually - just reference the sheet value.

---

## Related Documentation

- Your own portfolio context files — strategic context (names, pacing rules, client KPIs)
- Your own accounts map — account name → CID → portfolio mapping
- Your own dashboard/sheet config — tab schemas for pacing data

---

**Created:** 2025-10-28
**Last Updated:** 2025-11-01
**Status:** Active
