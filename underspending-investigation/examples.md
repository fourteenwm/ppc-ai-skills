# Worked Examples — three investigations, two that end without a budget change

Synthetic accounts and numbers throughout. Console excerpts are trimmed to
the decision-bearing lines; formats match what the script prints. The point
of each example is the read, not the run.

---

## Example 1 — The routine one: budget-constrained, conservative increase

**Setup:** "Halstead Dental - Search" flagged 12% under pacing tolerance.
Companions loaded, script run on July 18.

```
STEP 2: IMPRESSION SHARE ANALYSIS (Last 7 Days)
...
Campaign: Halstead Dental - Search
  Type: SEARCH
  Search Impression Share: 61.42%
  Budget Lost IS: 33.87%
  Rank Lost IS: 4.71%
  Total Impressions (7-day): 6,214

  ROOT CAUSE ANALYSIS:
    [!] SEVERE BUDGET CONSTRAINT (Budget Lost IS > 30%)
    -> Recommendation: Increase budget significantly

STEP 3: MONTH-TO-DATE PACING ANALYSIS
...
Month: July 2026
Days Elapsed: 18 / 31

Total Monthly Budget: $3,100.00
MTD Spend: $1,576.80
Expected Spend (Day 18): $1,800.00
Variance: $-223.20 (-12.40%)

STATUS: UNDERSPENDING by 12.40%
```

**The read:** Step 1 first — the budget-change log (none kept, so a
`change-history-checker` pull) shows no budget edits in 14 days: not
ramp-up. STEP 1 of the output shows 7-day utilization at 90.9% with 21
conversions at $30.31 CPA against a $35 goal — performance guardrails pass.
The IS readout says the constraint is budget (Budget Lost IS 33.87%, Rank
Lost IS under 5% — quality is not the problem), and day 18 clears the
early-month gate.

**The call:** every gate in `budget-recommendation-calculator` passes —
variance beyond tolerance, Budget Lost IS well above 10%, CPA acceptable, no
recent increase, past day 5. Conservative calculation at the standard 0.5
adjustment factor: $3,100 × (1 + 0.1240 × 0.5) = $3,292 → recommend
**$3,290/month (+6.1%, daily $106.13)** — inside the 10% single-change cap.
Expected outcome: variance back inside tolerance over 3-5 ramp days at
roughly current CPA; monitor Budget Lost IS, which should fall from the
34% range.

---

## Example 2 — The explicit no-action: low demand wearing an underspend costume

**Setup:** "Copper Hollow Storage - Search" shows −16% pacing variance.
The obvious move — raise the budget — is queued up in the ticket. Run on
July 20.

```
Campaign: Copper Hollow Storage - Search
  Type: SEARCH
  Search Impression Share: 87.31%
  Budget Lost IS: 2.14%
  Rank Lost IS: 6.02%
  Total Impressions (7-day): 2,807

  ROOT CAUSE ANALYSIS:
    [OK] LOW DEMAND / HIGH CAPTURE RATE
    -> Account is capturing most available impressions
    -> Underspending is normal for this search volume

...
Variance: $-194.40 (-16.20%)

STATUS: UNDERSPENDING by 16.20%
```

**The read:** no recent budget changes (Step 1 clean). Performance is fine
(9 conversions, $37.99 CPA against a $45 goal). But the IS pattern is the
low-demand signature from the decision tree: Search IS 87%, Budget Lost IS
2%, Rank Lost IS 6%. The account already wins nearly every auction it can
enter — there is no impression inventory left for new budget to buy. A
budget increase here wouldn't even spend: Budget Lost IS at 2% means the
current budget isn't the thing turning impressions away.

**The call — explicitly no action, written as a complete answer:**

> ❌ Do NOT Increase Budget
>
> Reason: Low demand / high capture (Search IS 87.31%, Budget Lost IS
> 2.14%). The −16.20% variance reflects available search volume, not a
> delivery problem. An increase would sit unspent and misstate the plan.
>
> Instead: (1) accept the variance and note demand as the ceiling in this
> month's report, (2) raise the question of whether budget should shift to
> another channel or down to demand, (3) monitor weekly — revisit only if
> Search IS drops below ~80% or Budget Lost IS rises above 10%, which would
> mean demand returned.

No-action closes the ticket as firmly as an increase would. The trap is
treating 87% impression share as "room to grow 13%" — the remainder is
mostly rank-lost and unreachable at any budget.

---

## Example 3 — The edge case: a −60% "emergency" that is three artifacts stacked

**Setup:** "Brightwell Plumbing" pages the morning check with a huge
underspend. Run July 4 at 8:12am. Two Search campaigns share one $80/day
budget.

```
Campaign: Brightwell Plumbing - Search - Service
  Status: ENABLED
  Type: SEARCH
  Bidding: MAXIMIZE_CONVERSIONS
  Budget Type: SHARED
  Daily Budget: $80.00
  7-Day Budget: $560.00
  7-Day Spend: $391.20
  Utilization: 69.9%
...
Campaign: Brightwell Plumbing - Search - Brand
  Budget Type: SHARED
  Daily Budget: $80.00
  7-Day Budget: $560.00
  7-Day Spend: $128.40
  Utilization: 22.9%
...
OVERALL 7-DAY SUMMARY:
  Total 7-Day Budget: $1,120.00
  Total 7-Day Spend: $519.60
  Overall Utilization: 46.4%
...
[Monthly budget estimated from current daily budgets x days in month]
[If your contracted monthly budget differs, re-run with --monthly-budget]

Month: July 2026
Days Elapsed: 4 / 31

Total Monthly Budget: $4,960.00
MTD Spend: $255.14
Expected Spend (Day 4): $640.00
Variance: $-384.86 (-60.13%)

STATUS: UNDERSPENDING by 60.13%
```

**The read — the contract, applied three times:**

1. **Shared-budget double-count.** Both campaigns carry the same $80/day
   budget, so the totals count it twice: the $1,120 "7-day budget" is really
   $560, and the $4,960 "monthly budget" is really $2,480. Recomputed by
   hand: $519.60 ÷ $560 = **92.8% utilization** — the budget is nearly
   maxed, the opposite of what 46.4% suggested.
2. **Morning-run bias.** Expected spend counts July 4 as fully elapsed at
   8am. Expected through *yesterday* is 3 × $80 = $240 against $255.14
   actually spent — slightly **ahead** of pace.
3. **Early-month denominator.** Day 4 of 31 — even a real gap this early is
   inside the calculator's own "wait until day 5" gate.

A verification re-run at 4:30pm with the contracted budget confirms it:

```
[Monthly budget supplied via --monthly-budget]

Total Monthly Budget: $2,480.00
MTD Spend: $307.50
Expected Spend (Day 4): $320.00
Variance: $-12.50 (-3.91%)

STATUS: UNDERSPENDING by 3.91%
```

**The call:** no action on budget — the account is on pace. Two process
fixes instead: record the $2,480 contracted budget wherever pacing variance
is computed (this alarm came from the doubled estimate), and schedule pacing
checks after business hours or correct for the current day by hand. Worth
one extra beat: utilization at 92.8% with on-pace delivery means this
account has little headroom — if demand rises later in the month, THAT
becomes a real budget conversation, and you'll want the shared-budget
arithmetic from this read again.
