# Rules — reading a conversion audit without panicking or shrugging

Decision logic for the audit output. A stale row is a QUESTION, not a
verdict — the table can't distinguish a broken tag from a business that had
a slow month.
[`references/audit-contract.md`](references/audit-contract.md) defines
exactly what each row means; [`examples.md`](examples.md) shows worked
reads.

## Invariants (never break these)

- **Read-only.** The audit changes nothing. Fixing a tag, pausing an
  action, or re-promoting a conversion happens in your own change process.
- **A row is a hypothesis.** Staleness has three unremarkable causes
  (seasonality, low volume, deliberate config) and one emergency (broken
  tracking). The audit can't tell them apart — the triage below exists to.
- **Absence of findings ≠ health.** Zero rows means the *configured* actions
  fired recently. An account with no conversion actions at all passes
  silently (contract, "zero-actions blind spot") — and an `[ok]` below an
  error line is a failure, not a pass.
- **Primary-lens default.** The portfolio scan reads only the actions that
  feed Smart Bidding (`metrics.conversions`). That's the right default: a
  quiet PRIMARY action means bidding is flying blind, which is the actual
  emergency.

## Triage order — reading a portfolio scan

1. **Error lines first.** Scan the account list for `Error checking spend` /
   `Error querying conversion actions` / `Error auditing` — each one makes a
   nearby `[ok]` or `[skipped]` untrustworthy (contract, error isolation).
   Re-run those accounts before triaging anything else.
2. **No-data rows on accounts that are spending real money.** An `ENABLED`
   primary action with zero fires in 90 days, on an account spending daily —
   that's Smart Bidding optimizing toward nothing. Top of the list.
3. **Stale rows where the action is the account's MAIN conversion.** A lead
   form or purchase action quiet 30+ days on an active account is either a
   broken tag or a dead funnel — both urgent, different owners.
4. **Warnings last, against cadence.** A 15-30-day gap only matters relative
   to the action's own rhythm (below). Batch-review these; don't page anyone.

## When stale is EXPECTED (the non-alarms)

| Pattern | Why it's normal | What to do instead |
|---|---|---|
| Seasonal business, off-season | AC tune-ups in January, tax prep in July — demand went home | Note the season in the report; set an expectation date; only escalate if the season returns and the action doesn't |
| Low-volume action (a few fires per month) | An action averaging 1-2 conversions/month will sit at 15-30 days quiet routinely — that's arithmetic, not breakage | Compare days-quiet to the action's own average gap, not to the fixed 15/30 thresholds |
| Deliberately-secondary actions | Demoted to observation → vanishes from the portfolio scan entirely (contract, asymmetry) | Confirm the demotion was intentional (change history), then expect the disappearance |
| Soft/engagement actions used as bidding feeders | Low-conversion accounts sometimes run soft primary actions deliberately, to give Smart Bidding volume | These are load-bearing despite low value-per-fire — a quiet one IS actionable (bidding starves), just not a "broken tag" conclusion |
| Newly created action | "Never fired" right after creation is a launch state, not a defect | Give new campaigns/tags 7-14 days before judging |
| Migration leftovers | Old imported/duplicate actions superseded by newer ones go permanently stale by design | Cleanup candidates, not emergencies — queue for config hygiene |

## Escalation ladder (before "the tag is broken")

Work the cheap checks in order — each one closes a branch:

1. **Date the last fire.** Widen the window (`--days 180` or more) or run
   the deep-dive: "Never fired (90 days)" often becomes "fired until the
   site relaunch on the 14th" — which is your root cause.
2. **Check the observation view.** The deep-dive's `(obs)` rows show whether
   *anything* is tracking. All actions quiet ≈ site/tag-level break; one
   action quiet ≈ that action's trigger.
3. **Ask who touched conversion settings.**
   [`change-history-checker`](../change-history-checker/) — inside 30 days
   its detailed view names the actor. A demotion, a counting change, or a
   new duplicate action explains many "breaks".
4. **Fire the conversion yourself.** Tag Assistant / GTM preview / a test
   lead on the live form. Only a failed live test earns the verdict
   "tracking is broken".
5. **Then fix** — tag, page, or trigger — and re-run the audit in a few
   days to confirm the row cleared. Never bulk-delete stale actions as the
   first move; removed actions take their history with them.

## False-alarm table

| Signal | Likely cause | Verify by | Then |
|---|---|---|---|
| `Never fired` on a years-old action | Window artifact — zero fires in `--days`, not zero ever (contract) | Deep-dive or `--days 365` | Date the stop; investigate what changed then |
| `[skipped]` on an account you know is spending | Spend-check error masquerading as no-spend (contract, error isolation) | The `Error checking spend` line above it | Fix credentials/access; re-run that account |
| `[ok]` with zero findings, error line above | Action query failed — nothing was audited | The `Error querying conversion actions` line | Re-run; treat the `[ok]` as void |
| An account never appears problematic, ever | No conversion actions configured at all | Deep-dive STEP 1 (`Found 0 …`) | Route to [`account-diagnostic`](../account-diagnostic/) — setup gap, not health |
| Warning rows churning in and out weekly | Low-volume Poisson noise around the 15-day line | The action's own average gap | Judge against cadence; consider them ambient |
| Action vanished from the scan (was Warning last month) | Demoted to observation — not fixed, not broken | Deep-dive `(obs)` marker; change history | Confirm intent; track it in the deep-dive if it still matters |
| Deep-dive exits with `WARNING: No conversions found` | ALL actions quiet in the window — the early exit fires before the per-action table (contract) | Re-run with wider `--days`; read STEP 1's list | Whole-account quiet = site/tag-level investigation, not per-action |
| Deep-dive can't find the account by name | Name lookup only sees directly-accessible accounts — not your MCC's clients (contract) | — | Use `--cid`; that's the reliable path |
| Same action, different verdicts across the two scripts | Primary-vs-all-conversions metric split (contract, asymmetry) | The `(in)`/`(obs)` marker | Expected; read the asymmetry table |
| Whole portfolio suddenly "stale" at once | Systemic: consent/tag-manager change, conversion import outage — or an audit run against the wrong window | A known-good high-volume account's deep-dive | If confirmed account-side, escalate as ONE incident, not N rows |

## Cadence

Weekly portfolio scan on actively-managed books; after any site migration or
GTM change (same week, not next month); ~2 weeks after launching new
campaigns or new conversion actions (ramp first, then judge); before
client-facing reporting periods so "why did conversions drop" is answered
proactively.
