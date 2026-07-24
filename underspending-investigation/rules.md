# Rules — when to recommend, when to say no, and what not to trust

Decision logic for the investigation. The script collects evidence;
[`references/investigation-contract.md`](references/investigation-contract.md)
defines exactly what each printed line means; the three companion skills own
their frameworks. This file owns the judgment: reading order, the no-action
calls, the false alarms, and when to stop.

## Invariants (never break these)

- **Read-only.** The investigation never touches the account. Budget changes
  happen in your own execution layer, after human sign-off — this skill's
  product is a diagnosis and a recommendation, never a mutation.
- **Diagnosis before dollars.** No budget number leaves the report until the
  evidence names WHY the account underspends. "Raise it and see" is the
  failure mode this skill exists to prevent.
- **No-action is a first-class outcome.** Low demand, ramp-up, performance
  failure, and data artifacts all end in "do not raise the budget" — written
  with the same rigor as an increase, so nobody re-litigates it next week.
- **Every claim traces to a printed line or a named framework.** If the
  evidence section can't quote it, the diagnosis can't use it.
- **One account per investigation.** Portfolio sweeps are the caller's job
  (parallel orchestration); cross-account conclusions don't belong in a
  single-account report.

## The framework load-map

Six frameworks drive the protocol. Three ship as companion skills in this
repo — load them via the Skill tool **at investigation start, before reading
script output**:

| Load | It answers |
|---|---|
| [`portfolio-pacing-rules`](../portfolio-pacing-rules/) | Is this variance outside tolerance? What are the performance guardrails? (Step 1 + the verdict) |
| [`impression-share-diagnostics`](../impression-share-diagnostics/) | WHY — budget-constrained vs quality-constrained vs low demand; the Pmax and Display caveats (Step 3) |
| [`budget-recommendation-calculator`](../budget-recommendation-calculator/) | HOW MUCH — the conservative calculation, the hard 10% single-change cap, the don't-recommend gates (Step 4) |

The other three are bring-your-own, inlined in the protocol: campaign-line
filtering (Step 2 — your naming convention decides which campaigns are in
scope), pacing-data lookups (Step 1 — your budget-change log, or
[`change-history-checker`](../change-history-checker/) as the API-based
substitute), and [`gaql-query-patterns`](../gaql-query-patterns/) (optional —
only when extending the shipped script or running follow-up pulls).

## Stop-early ladder (the adaptive protocol)

1. **Step 1 finds a budget increase 3-7 days old** → diagnosis is "ramp-up
   period", recommendation is "monitor 3-5 days", investigation OVER. Don't
   run the IS analysis to decorate a finished answer.
2. **Step 1 finds an increase 7-14 days old** → note it and continue — the
   account should be ramped by now, so persistent underspend is real.
3. **The "underspend" traces to campaigns that ended or paused by design**
   (end dates passed, planned pauses) → pacing artifact, not a diagnosis
   target. The script doesn't print end dates — check them (UI, or a
   [`google-ads-query`](../google-ads-query/) campaigns pull) before
   diagnosing an account whose delivery simply stopped on schedule.
4. Otherwise run the full protocol — and add steps freely when the data
   points somewhere (ad schedules, geo restrictions, disapprovals, negative
   conflicts). Skip Step 4 entirely unless the diagnosis is
   budget-constrained.

## The no-action calls (each is a complete answer, not a shrug)

| Evidence pattern | Verdict | What you write |
|---|---|---|
| Budget increase within the last 7 days | Ramp-up | Monitor 3-5 days, re-check variance after; no change |
| Search IS > 80%, Budget Lost IS < 10%, Rank Lost IS < 10% | Low demand | The account already captures most of its market — more budget buys nothing. Consider whether budget should move DOWN or to another channel |
| CPA > 20% over goal, or ROAS materially under target | Performance failure | An increase would scale a losing position. Name the quality/conversion fix that comes first |
| Fewer than 5 days into the month | Early-month noise | Denominators too small; re-check after day 5 |
| Variance shrinks when you re-derive expected spend through yesterday | Intraday artifact | Re-run late in the day, or state the corrected variance (contract, STEP 3) |
| High Rank Lost IS with low Budget Lost IS | Quality-constrained | Budget can't buy back rank-lost impressions — bids/quality work, not money. High RLIS (60-80%) is common in competitive auctions; treat it as informational and never optimize TO a rank target |

The low-demand call is the most misread: 80%+ Search IS with idle budget
FEELS like headroom. It's the opposite — the auction is exhausted.

## False-alarm table

| Signal | Likely cause | Verify by | Then |
|---|---|---|---|
| Big underspend on a morning run | Expected spend counts today in full; MTD spend has only today's partial (contract, STEP 3) | Recompute expected through yesterday | If variance collapses, it was the clock, not the account |
| Variance alarms on days 1-4 of the month | Tiny denominator amplifies normal daily wobble | Day of month in the output | Re-check after day 5 (the calculator's own gate) |
| Overall utilization far below every visible campaign's own line | Shared-budget double-count, or zero-spend campaigns counted in totals but hidden above the line (contract, STEP 1) | `Budget Type: SHARED` rows; per-campaign figures | Diagnose from per-campaign lines; discard the overall figure on shared-budget accounts |
| Odd utilization right after a budget change | Utilization divides window spend by TODAY'S budget (contract, STEP 1) | Budget-change log / `change-history-checker` | Re-read at the old budget; ramp-up rules apply |
| New campaign underspending | Smart-bidding ramp — 7-14 days is normal | Campaign start date | Note and monitor; don't diagnose mid-ramp |
| A campaign missing from STEP 1 | Zero activity in the window — absent, not deleted (contract, STEP 1) | Campaign list in the UI or a `google-ads-query` pull | If it SHOULD be spending, that absence is the finding — check status, end date, approvals |
| STEP 2 prints nothing useful | Display/Video/DGen-only account — the IS section covers Search + Pmax only (contract, STEP 2) | Campaign types in STEP 1 | Diagnose via utilization + performance; run the Display check below |
| Ticket says "+15% underspending", script says −15% | Sign conventions differ (contract, STEP 3) | Compare magnitudes | Normal — state one convention in your report |
| Variance implausible vs the contracted budget | Estimate built from daily budgets × days, not the contract (contract, STEP 3) | Re-run with `--monthly-budget` | Always prefer the contracted number when one exists |
| Seasonal account pacing under | The demand curve, not a defect | Known seasonality, year-over-year volume | Low-demand verdict with a seasonal note; plan budget shaping, not a reactive raise |

## The Display "Bid setting limited" check

When a Display/GDN remarketing campaign shows low spend, look for **"Bid
setting limited"** in the Google Ads UI. The pattern: Maximize Clicks with a
max CPC cap too low for Display auctions (a $2-3 cap starves impressions),
very low click volume, spend far under budget. The fix pattern: raise the cap
to a floor that gives the algorithm headroom (tune to your inventory — a ~$4
floor is a common managed-portfolio starting point), expect spend to move
within 2-3 days and CPCs to settle below the new cap. This is a settings
diagnosis, not a budget one — Display campaigns have no Search IS metrics.

## Escalation default

When the evidence is mixed — the `[?] MIXED FACTORS` readout, or frameworks
pointing different directions — present the evidence, name the two or three
candidate causes, recommend the CHEAPEST discriminating check next (a
settings read, an ad-schedule look, a `change-history-checker` pull — each
closes a branch), and hold the budget where it is. A wrong no-action costs a
few days of underdelivery; a wrong increase spends real money at a bad CPA.
When in doubt, monitor — and say exactly what you're watching and for how
long.
