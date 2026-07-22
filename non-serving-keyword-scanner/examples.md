# Examples — worked scan reads

Three worked triage decisions applying `rules.md`. All accounts, CIDs,
keywords, and numbers are synthetic.

## 1. Routine portfolio scan — clusters first, then the three verdicts

**Report:** 38 accounts scanned from `accounts.md`, 214 flagged keywords
across 19 accounts.

**Reasoning:** Sorted by Account → Campaign, one cluster dominates: Ridgeline
Auto Care (1234567890) has 61 rows, every one in its "Winter Services"
campaign. Change history shows the campaign was re-enabled three weeks ago
after being paused since April — the classic status/window asymmetry. The
180-day window includes roughly five dark months, so those keywords never had
a chance to serve for most of it. A re-scan of just that account with
`--days 21` (the serving period) returns 4 rows — the other 57 were timeline
noise. The scattered remainder gets per-row reads. Three representative
verdicts:

- *"transmission fluid exchange coupon"* (Harborview Collision) — the shop
  discontinued coupon promotions last year. Nothing should ever serve this →
  **Pause**.
- *"snow chain installation"* — it's August, and the term is
  calendar-gated → **Keep**, annotated as seasonal so next run's review
  takes seconds.
- *"brake pad replacement"* EXACT — a core service with obvious demand, so
  zero impressions is wrong → **Investigate**. A search-terms pull
  (`google-ads-query`) shows those queries matching a PHRASE keyword in a
  different ad group: the exact is shadowed, not dead. The fix is steering,
  not pausing — negatives via the `sqr-pipeline` review gate so the exact
  wins its own traffic.

Mid-review the request comes in: "just pause all 214 and be done." Declined
per the invariants — 61 of those rows were a healthy seasonal campaign three
weeks into its revival, and a blanket pause would have gutted it silently.

**Decision:** Annotated sheet with verdict counts (9 Pause / 187 Keep-or-
timeline / 18 Investigate), the human executes the pauses in the UI. No
savings claimed — every row cost $0.00; the deliverable is a cleaner, more
honest account structure.

## 2. Whole account flagged — the scanner found an outage, not keyword rot

**Report:** Maplewood Tire & Brake (2345678901) — 178 of its ~190 enabled
Search keywords flagged, every campaign represented.

**Reasoning:** Triage order says stop — at this density there are no per-row
reads. This is not 178 individual keyword problems; it's one account-level
problem wearing 178 disguises. The campaigns pass the scan's enabled-status
filters, but nothing has served in months. An `account-diagnostic` run
confirms it: budget set, $0 month-to-date spend — the auto-red circuit
breaker — with a billing hold visible in the UI.

**Decision:** Zero keyword actions. The billing fix routes to the account
owner; the keyword list is set aside entirely. Re-scan with `--days 30`
after the account has served for a full month — only what's still at zero
*after* revival gets a real read. Pausing 178 keywords here would have
dismantled a structure that needs to be intact the day billing resumes.

## 3. Edge case: the disappearing keyword read as a win

**Report:** June run — *"diesel particulate filter cleaning"* (Ridgeline
Auto Care) flagged; verdict **Keep** (niche term, high-value job when it
lands). July run — the row is gone. A teammate reads it as "it started
serving — the cleanup is working."

**Reasoning:** The tab is a snapshot, not a log — absence has three causes,
and only one of them is good news: the keyword served at least once (real
recovery), a human paused it, or Google's low-activity auto-pause removed it
from scan scope (paused keywords are never scanned). Change history settles
it: Google auto-paused the keyword two weeks after the June run — it had
been at zero impressions for ~13 months, and June's flag was simply month
twelve-and-change of that silence. Nothing recovered; the scan's scope
shrank.

**Decision:** Correct the read, update the June annotation. Don't re-enable —
an auto-paused keyword re-enabled without a structural change just restarts
the same 13-month clock. The niche intent survives as a PHRASE variant that
does serve occasionally. And the process fix: this misread was possible
because both runs wrote the same tab — switch to dated tabs
(`--tab-name "Non-Serving 2026-07"`) so run-over-run comparisons are real.
