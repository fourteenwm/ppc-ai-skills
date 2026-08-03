---
name: investigation-methodology
description: Structured hypothesis-driven investigation framework for diagnosing Google Ads performance issues. Auto-invoke when user says "investigate," "why is [account] performing poorly," "dig into," or asks to diagnose a performance issue.
---

# Investigation Methodology

Structured framework for diagnosing Google Ads performance issues. Follow this process for every investigation — no exceptions.

## What This Skill Deliberately Does NOT Do

- **Replace domain judgment.** Step 4's recommendation must be specific, but the domain rules that make it safe live in their own skills — a budget fix still goes through [`budget-recommendation-calculator`](../budget-recommendation-calculator/)'s conservative caps; a live-account change still goes through [`mutation-safety`](../mutation-safety/)'s approval gate.
- **Pull data for you.** The framework sequences WHICH evidence to gather at each layer; it works with the API, exports, or screenshots — whatever access exists.
- **Format the client deliverable.** Findings presented to a client go through [`client-communication-standards`](../client-communication-standards/) (Background → Analysis → Conclusions); Step 4 here is the internal analytical output that feeds it.
- **Guarantee an answer.** Inconclusive is a valid verdict — the Rules require saying so over inventing a cause.

## Step 1: Define the Problem Statement

Start with the specific question. Do not generalize.

**Bad:** "Account is performing poorly"
**Good:** "CPA increased from $37.97 (December) to $59.04 (January) — why?"

**Bad:** "Spend is off"
**Good:** "Account is 22% under monthly budget pace as of day 15"

If the user gives a vague problem statement, ask clarifying questions:
- What metric changed?
- What was it before vs. now?
- Over what time period?
- Which campaigns or the whole account?

## Step 2: Generate Hypotheses BEFORE Analysis

List 5-8 possible causes BEFORE pulling any data. This prevents confirmation bias.

Always include hypotheses from these categories:

### Internal Changes (Things You Control)
- Budget changes (increases, decreases, shared budget reallocation)
- Targeting changes (geo, audience, device, demographics)
- Keyword changes (additions, pauses, match type changes)
- Ad copy changes (new RSAs, paused ads, asset performance shifts)
- Bid strategy changes (switching strategies, target changes)
- Landing page changes (new pages, broken pages, speed issues)
- Negative keyword additions (too aggressive, blocking good traffic)

### External Factors (Things You Don't Control)
- Seasonality (industry cycles, holidays, weather)
- Competitive shifts (new competitors, competitor promotions)
- Market changes (demand shifts, economic factors)
- Google algorithm or auction changes

### Measurement Issues (The Data Itself)
- Conversion tracking changes (new actions, removed actions, tag issues)
- Attribution model changes
- Data lag (conversions that haven't reported yet)
- Comparing different date ranges or campaign structures

Assign initial probability estimates to each hypothesis (gut feel is fine at this stage):
```
Hypothesis 1: Budget was reduced — 30% likely
Hypothesis 2: New competitor entered auction — 20% likely
Hypothesis 3: Conversion tracking broke — 15% likely
...
```

## Step 3: Gather Evidence One Layer at a Time

Pull data sequentially, not all at once. Each layer narrows the investigation.

### Layer 1: Performance Metrics (Top-Level)
- Cost, conversions, CPA by month or week
- Compare the same campaigns across time periods (apples-to-apples)
- If campaigns were restructured, combine them for fair comparison

**After Layer 1, update hypothesis probabilities.**

### Layer 2: Traffic Quality
- Impressions, clicks, conversion rate
- Is traffic volume down, or is conversion rate down?
- If traffic is down: budget or targeting issue
- If conversion rate is down: landing page, ad relevance, or tracking issue

**After Layer 2, update hypothesis probabilities.**

### Layer 3: Segmentation
- Device breakdown (mobile vs. desktop)
- Geographic breakdown
- Campaign / ad group breakdown
- Day-of-week or hour-of-day patterns

**After Layer 3, update hypothesis probabilities.**

### Layer 4: Change History
- Keyword additions / pauses
- Targeting changes
- Bid strategy changes
- Budget changes
- Ad changes

**After Layer 4, update hypothesis probabilities.**

### Layer 5: Attribution and Tracking (If Relevant)
- Conversion action changes
- Tag health (are tags firing correctly?)
- Attribution model differences
- Data lag for recent conversions

**After Layer 5, you should have a clear diagnosis.**

## Step 4: Present Findings

Structure the conclusion as:

### Root Cause
State the primary cause clearly. One sentence.

### Evidence
List the 3-5 data points that prove it.

### Hypothesis Scorecard
Show which hypotheses were confirmed, eliminated, or remain uncertain:
```
✅ Confirmed: Budget was reduced 15% on Jan 3 (60% → 95% confidence)
❌ Eliminated: No competitor changes in auction insights
❌ Eliminated: Conversion tracking verified working
⚠️ Uncertain: Seasonal demand shift (possible contributing factor)
```

### Recommendation
What to do about it. Be specific:
- **Bad:** "Consider increasing the budget"
- **Good:** "Increase daily budget from $50 to $58 (15% increase to restore previous spend level). Monitor CPA for 7 days before further changes."

## Rules

### Do Not Skip Steps
Even if you think you know the answer at Step 1, go through the hypothesis generation. You might be wrong, and the structured process catches what assumptions miss.

### Do Not Dump Data
Each layer should produce a concise finding, not a raw data table. "Conversion rate dropped 30% on mobile while desktop held steady" is a finding. A 200-row table is not.

### Update Probabilities
After each layer, explicitly update which hypotheses are more or less likely. This keeps the investigation focused and prevents wandering.

### One Root Cause
The conclusion should identify the PRIMARY cause. There may be contributing factors, but lead with the main one. If there are genuinely two independent causes, state that explicitly.

### Ask When Stuck
If the data doesn't point to a clear root cause after Layer 4, say so. "The data is inconclusive — here's what I've eliminated, and here are the remaining possibilities that need manual investigation" is better than making up an answer.

## Worked Example (Synthetic Data)

**Step 1 — Problem statement:** "Metro Auto's CPA rose from $42 to $67 (+60%) between June and July, same campaigns both months."

**Step 2 — Hypotheses before any data:**
```
H1: Budget or bid strategy changed — 25%
H2: Conversion tracking broke or changed — 20%
H3: New competitor / auction pressure — 20%
H4: Seasonality (summer slowdown) — 15%
H5: Negative keywords blocking good traffic — 10%
H6: Landing page issue — 10%
```

**Step 3 — Evidence, one layer at a time:**

- **Layer 1 (performance):** Cost roughly flat ($3.1k → $3.2k); conversions fell 74 → 48. The CPA rise is conversion-driven, not spend-driven. → H1 down, H2/H5/H6 up.
- **Layer 2 (traffic quality):** Clicks and CTR flat; conversion rate 4.1% → 2.7%. Traffic held — the drop is post-click. → H3 down (auction pressure would show in CPCs and volume), H2/H6 up.
- **Layer 3 (segmentation):** Mobile conversion rate fell 4.4% → 1.6% while desktop held (3.8% → 4.0%). → H6 now leading, mobile-specific. H4 down — seasonality wouldn't pick a device.
- **Layer 4 (change history):** Website relaunched July 2; zero keyword, bid, budget, or negative changes in the account. → H1/H5 eliminated.
- **Layer 5 (tracking):** Conversion actions unchanged; tags verified firing on the new site. → H2 eliminated.

**Step 4 — Findings:**

Root cause: the July 2 site relaunch broke the mobile experience — mobile conversion rate fell ~64% while desktop held, and the timing matches change history.

```
✅ Confirmed: Mobile CVR 4.4% → 1.6% after the relaunch; desktop stable (90% confidence)
❌ Eliminated: No account changes (Layer 4); tracking verified working (Layer 5)
⚠️ Uncertain: Minor seasonal contribution possible — but seasonality isn't device-specific, so secondary at most
```

Recommendation: Fix the mobile landing experience (test the form on the relaunched template), then re-check mobile conversion rate over the following 7-10 days. No bidding or budget changes until the site issue is resolved — the account didn't cause this.

## When to Load Other Skills

| Skill | When |
|-------|------|
| [`change-history-checker`](../change-history-checker/) | At Layer 4 — it pulls the account change history (up to 90 days back) that this layer interrogates |
| [`impression-share-diagnostics`](../impression-share-diagnostics/) | When the problem statement is underspending — IS analysis is the specialized layer for budget vs. quality vs. demand |
| [`budget-recommendation-calculator`](../budget-recommendation-calculator/) | When the root cause is a budget constraint and the recommendation needs conservative sizing |
| [`client-communication-standards`](../client-communication-standards/) | When Step 4's findings become a client-facing report (Background → Analysis → Conclusions) |
