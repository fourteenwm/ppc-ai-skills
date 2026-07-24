# Worked Examples — three audit reads, two of them traps

Synthetic accounts and numbers throughout. Console excerpts are trimmed to
the decision-bearing lines; formats match what the scripts print (plain
text, `[ok]`/`[skipped]` markers, no emoji).

---

## Example 1 — The routine portfolio read: four rows, one emergency

**Setup:** weekly scan of a 12-account book, July 21.

```
PORTFOLIO CONVERSION AUDIT
====================================================================================================
Accounts to audit: 12
Lookback period: 90 days
Analysis date: 2026-07-21 09:14:03
====================================================================================================

Auditing accounts...

  [ok] Fernbrook Apartments
  [ok] Bridgeline Heating
  [ok] Gearline Transmission
  ...
  [skipped] Lindenmoor Cabinetry (no spend in last 7 days)

Audit complete. Checked 11 accounts, skipped 1 (no spend).

NO RECENT CONVERSIONS (90+ days) - 2 issues

Account Name                                       | Conversion Action                        | Last Activity
-------------------------------------------------- | ---------------------------------------- | ---------------
Fernbrook Apartments                               | Lead Form Submit                         | Never fired
Fernbrook Apartments                               | Contact - Old (GA4 Import)               | Never fired

STALE (30+ days) - 1 issues

Bridgeline Heating                                 | Heating Tune-Up Booking                  | 47 days ago

WARNING (15-30 days) - 1 issues

Gearline Transmission                              | Phone Call - 60s                         | 22 days ago

SUMMARY
...
Total problematic conversions: 4
  No recent data:       2
  Stale (30+ days):     1
  Warning (15-30 days): 1
```

(`- 1 issues` is the script's own pluralization — expected.)

**The read, in triage order:**

1. **Error lines:** none — every `[ok]`/`[skipped]` is trustworthy this run.
2. **Fernbrook / Lead Form Submit — the emergency.** An `ENABLED` primary
   action, zero fires in 90 days, on an account spending daily: Smart
   Bidding is optimizing toward nothing. Escalation ladder: a deep-dive at
   `--days 240` shows it firing steadily until ~14 weeks ago; the `(obs)`
   rows and the phone action still fire, so tracking is alive at the site
   level; a test submit on the live form never reaches Google — the form
   was rebuilt and the conversion trigger didn't survive. Fix the trigger,
   live-test, re-scan in a few days.
3. **Fernbrook / Contact - Old (GA4 Import)** — a migration leftover
   superseded by the current lead action. Stale by design: queue for config
   cleanup, not for panic.
4. **Bridgeline / Heating Tune-Up Booking, 47 days** — it's July. Heating
   bookings sleep in summer. Note the season, set an expectation date
   (early fall), move on.
5. **Gearline / Phone Call - 60s, 22 days** — this action averages a fire
   every ~18 days. 22 days is inside its natural wobble; ambient, batch-
   review next week.

One report, four rows, exactly one work item — that's the audit doing its
job.

---

## Example 2 — The edge case: error lines make `[ok]` and `[skipped]` lie

**Setup:** same portfolio, a month later; two accounts moved to a new
billing structure and access is half-migrated.

```
Auditing accounts...

  [ok] Halstead Dental
Error checking spend for 3456789012: The caller does not have permission
  [skipped] Tolliver & Boyce Law (no spend in last 7 days)
Error querying conversion actions: The caller does not have permission
  [ok] Ravenna Windows & Doors

Audit complete. Checked 11 accounts, skipped 1 (no spend).
```

**The read:** two of these three verdicts are false, and the summary
arithmetic won't tell you.

- **Tolliver's `[skipped]` is not a paused account.** The error line above
  it is the spend *check* failing — a failed check returns "no spend" and
  the account skips as if idle (contract, error isolation). This firm
  spends five figures a month.
- **Ravenna's `[ok]` is void.** Its conversion-action query failed, so zero
  actions were audited — zero findings prints as a pass.
- Halstead's `[ok]` (no error line adjacent) stands.

**The call:** fix API access for the two moved accounts, re-run just those
two (`--cids 3456789012,2345678901`), and only then report the portfolio
clean. Never forward a summary whose account list contains error lines —
the counts are arithmetic over untrustworthy rows.

---

## Example 3 — The edge case: "Never fired" that fired for years

**Setup:** the portfolio scan shows `Ravenna Windows & Doors | Quote
Request | Never fired`. Before anyone declares the tag broken, date the
stop — "Never fired" only means "not in the last 90 days" (contract).

```
python scripts/last_conversion_dates_by_action.py --cid 2345678901 --days 240
```

```
STEP 1: CONFIGURED CONVERSION ACTIONS
--------------------------------------------------------------------------------

Found 3 website conversion actions configured
(Filtered out 2 store/mobile/Google-hosted actions)

  [OK] (in) Quote Request
     Type: WEBPAGE | Category: SUBMIT_LEAD_FORM | Status: ENABLED
  [OK] (in) Phone Call - Website
     Type: WEBSITE_CALL | Category: PHONE_CALL_LEAD | Status: ENABLED
  [OK] (obs) Newsletter Signup
     Type: WEBPAGE | Category: SIGNUP | Status: ENABLED
...
HEALTHY - Last conversion within 14 days (2 actions)

  - (in) Phone Call - Website: 2026-07-21 (today)
  - (obs) Newsletter Signup: 2026-07-19 (2 days ago)

STALE - Last conversion 30+ days ago (1 actions)

  - (in) Quote Request: 2026-04-18 (94 days ago)
     INVESTIGATE: May indicate broken tracking or low volume
```

**The read:** the wider window converts "Never fired" into a *date* —
April 18, which is the day before the rebuilt website went live. The marker
pattern narrows it further: phone calls fire `today` and the observation
signup fired 2 days ago, so the site's tag container is alive; exactly one
form-based action died on relaunch day. That's a form trigger that didn't
survive the rebuild (new form ID), not a broken account.

**The call:** re-map the form trigger in the tag container, submit a live
test, confirm the fire, and re-run the portfolio scan in a few days to
watch the row clear. Also worth noting what did NOT happen: nobody deleted
"Quote Request" during the 90-day panic — removed actions take their
history with them, and that history is what just solved this.
