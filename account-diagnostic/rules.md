# Rules — reading and triaging an inspection report

Decision logic for what happens AFTER the script prints its verdicts.
`examples.md` has worked reads; `references/check-rubric.md` has per-check
criteria; `SKILL.md` is the run guide.

## Invariants (never break these)

- **Diagnosis only — the diagnostic never repairs.** This skill runs SELECT
  queries and stops. Every fix is a separate, human-approved step through the
  routing table below, gated by [`mutation-safety`](../mutation-safety/).
  "Immediate action needed" in a finding means *a human decides immediately*,
  not *mutate immediately*.
- **Never overrule a verdict — contextualize it.** If a RED matches a known
  false-alarm pattern, the check stays RED in the report; your triage note
  explains why no action follows. Rewriting verdicts destroys the checklist's
  value as a consistent instrument.
- **One account per run.** "Inspect this account" is not a portfolio sweep.
  Deciding *which* account to inspect first is
  [`portfolio-health-prioritization`](../portfolio-health-prioritization/)'s
  job.
- **Estimated waste is a ceiling, not a total.** Checks 5/6 measure the same
  pacing gap two ways; search-term waste (12–13) overlaps keyword waste (15).
  Never present the sum as recoverable savings.
- **N/A is not failure.** Checks that don't apply (no PMAX, no DGen, no
  Search) report N/A and don't count against the score. A 42-check run with
  10 N/As is a complete inspection of a simple account, not a broken run.
- **Budget changes are recommendations only.** Even when pacing checks fire
  with dollar gaps, the output is a diagnosis plus a conservative
  recommendation — never an executed budget edit.

## Triage order

Work the report top-down by severity, not by check number:

1. **Auto-red circuit breakers** (no conversion actions; budget-but-zero-spend;
   mass disapprovals). These invalidate everything else — an account with no
   conversion tracking can't be optimized, only fixed. Stop and route these
   before discussing anything downstream.
2. **REDs with dollar figures, largest first** — but check the false-alarm
   table below before recommending action on any of them.
3. **Structural REDs without dollar figures** (automation ON, targeting mode,
   auto-apply). Cheap to fix, compounding if left on — Google's automation
   defaults re-opt-in new campaigns, so these recur.
4. **YELLOWs** — batch into routine optimization; none justify an emergency.

Order fixes by dependency, not just dollars: eliminate waste before adding
budget (raising spend into a 20%-waste account scales the waste), and turn
off automation before refreshing creative (or the automation regenerates what
you removed).

## False-alarm table — rule these out before acting

| Fired | Benign cause to rule out | Verify by | If benign |
|-------|--------------------------|-----------|-----------|
| 5/6 pacing RED | Campaign launched mid-month, or smart bidding still in learning (first ~7–14 days) | Campaign start dates vs. day of month | Expected artifact — no budget change; re-inspect after a full calendar month |
| 5/6 pacing RED | Campaign end dates throttling or front-loading delivery | Campaign end dates | Variance is scheduled, not broken |
| 5/6 pacing RED | Estimated monthly budget (daily × days-in-month) ≠ the real contracted budget | Compare against the actual monthly figure | Recompute variance by hand before any recommendation |
| 2 recency RED | Low-volume or seasonal account where 2–4 week conversion gaps are normal | Historical conversion cadence | Note the cadence; only a break FROM it means a dead tag |
| 12/13 waste RED | Conversion lag — recent clicks haven't had time to convert | Account's typical click-to-conversion delay | Re-check with a longer `--days` window before negating |
| 21 seasonal RED/YELLOW | The promo is current and intentional | Promo end date with the owner | Fine — re-flag after the promo ends |
| 29 geo-exclusions RED/YELLOW | Radius-targeted local business with nothing to exclude | Targeting setup | Fine as-is (the local-service preset already softens this) |
| 35 coverage RED | Negatives live on shared lists, which this check can't count | Shared negative-list membership | Coverage may be fine — verify list contents instead |
| 14 serving RED | Keywords added recently, no time to serve | Keyword creation dates | Time, not action |
| 23 labels RED | Low-volume account — Google needs impressions before labeling assets | Impression volume | Time, not action |
| 10/11 QS RED | Very low impression volume makes QS sparse and unstable | Sample size in the finding | Don't overhaul ads over a handful of rated keywords |
| 39/40 extensions | Extensions attached at campaign level only (check counts account-level) | Where assets are linked | Placement question, not a missing-assets problem |
| 42 location YELLOW | Business-Profile-sourced location assets invisible to the scan | GBP linkage in the UI | Already why this is YELLOW, not RED |

Checks 33/34 are the inverse case: they can only confirm asset groups exist —
the API exposes neither search themes nor audience signals, so even GREEN
carries a "verify in UI" action. GREEN there means "structure present," not
"signals confirmed."

## Routing table — where each finding goes next

Every route below is read-only analysis or a human-gated mutation. Nothing
here executes off the back of a diagnostic without a human approving it.

| Checks | Finding | Route to |
|--------|---------|----------|
| 1–3 | Tracking missing, stale, or duplicated | [`conversion-tracking-health`](../conversion-tracking-health/) for the deep audit; tag fixes happen on the website/GTM side |
| 4–6, 8 | Underspend / pacing gaps / budget-capped delivery | [`underspending-investigation`](../underspending-investigation/) — root cause BEFORE any budget recommendation |
| 7, 9 | Low IS / rank-lost IS | [`impression-share-diagnostics`](../impression-share-diagnostics/) decision tree |
| 12–13, 35 | Search-term waste, thin negative coverage | [`sqr-pipeline`](../sqr-pipeline/) — classification with consensus + human review gate before any negative uploads |
| 36 | Negatives blocking active keywords | [`neg-conflict-finder`](../neg-conflict-finder/) |
| 14 | Non-serving keywords | [`non-serving-keyword-scanner`](../non-serving-keyword-scanner/) for the 180-day view |
| 15 | High-spend zero-conv keywords | Pause/restructure decision for the human — take the flagged list, don't act on it |
| 17–21, 23–25 | Disapprovals, DKI, dead URLs, seasonal copy, weak assets | [`rsa-refresh`](../rsa-refresh/) or [`rsa-single-account`](../rsa-single-account/) for rewrites (both enforce [`ad-copy-verification-standard`](../ad-copy-verification-standard/)); [`ads-checker`](../ads-checker/) for the recurring creative-compliance audit |
| 22, 28 | Auto-apply recommendations enabled | UI change (Recommendations → Auto-apply) — no API write path here; list exactly which types to switch off |
| 26–27, 29 | Targeting mode, content suitability, geo exclusions | UI changes — state the exact setting and target value |
| 30–32, 43 | PMAX automation ON | [`pmax-asset-automation`](../pmax-asset-automation/) |
| 33–34 | Asset-group structure | Verify themes/signals in UI (API can't read them) |
| 37–38 | Suspicious / brand-unsafe placements | [`youtube-placement-audit`](../youtube-placement-audit/) for the full sweep; exclusions are a gated mutation |
| 39–42 | Missing extensions | Build the missing assets — creation is a gated mutation |
| 44 | DGen ad-level automation ON | [`dgen-automation-disable`](../dgen-automation-disable/) — dry-run first, human approval code required |

## Preset selection

- Strict-pacing lead-gen portfolio (property management and similar) →
  `property-management` (the default).
- Phone-driven local business (auto repair, home services) →
  `local-service` — softer pacing, adds call/location checks 41-42.
- Neither → run `property-management` and adjust `--pacing-threshold`; for
  deeper tuning the eight preset knobs are documented at the bottom of
  [`references/check-rubric.md`](references/check-rubric.md).

## Escalation default

When a finding is ambiguous — can't tell false alarm from real, dollar figure
looks implausible, two checks contradict — report what you see and stop.
Never resolve ambiguity by mutating an account. The inspection's job is to
make problems visible; deciding what they're worth is the human's.
