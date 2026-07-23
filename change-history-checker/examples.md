# Worked Examples — reading change history

Three real decision walks (synthetic accounts). Output mechanics are in
[`references/history-windows.md`](references/history-windows.md); the
judgment calls are [`rules.md`](rules.md).

## Example 1 — "What did I do in June?" (routine month read)

**Ask:** monthly work audit on Copper Hollow Apartments, CID 0987654321.

Bound with the day after the last day (date-only bounds read as midnight —
reference), so June is `--start 2026-06-01 --end 2026-07-01`:

```
$ python scripts/check_change_history.py 0987654321 --start 2026-06-01 --end 2026-07-01

============================================================
Change History: 0987654321
Period: 2026-06-01 to 2026-07-01
============================================================

2026-06-26:
  AD_GROUP_CRITERION: 41 changes (ADDED)

2026-06-24:
  CUSTOMER_ASSET: 4 changes (ADDED, REMOVED)
  ASSET: 6 changes (ADDED)

2026-06-10:
  CAMPAIGN_BUDGET: 1 changes (CHANGED)
  CAMPAIGN: 2 changes (CHANGED)
```

Read against the work log, every group maps: June 26 = the negatives upload
(41 criteria ADDED — negatives are criteria too); June 24 = the extension
refresh (assets added, old account-level assignments removed); June 10 = the
documented budget change plus two campaign-setting edits made the same day.
(`1 changes` is the script's standing pluralization — cosmetic.)

The user then asks *which* extensions June 24 touched — that's the
`--detailed` question (rules, flag decisions). Re-run adds the asset text:

```
2026-06-24:
  CUSTOMER_ASSET: 4 changes (ADDED, REMOVED)
    - Callout: Same-Week Tours
    - Sitelink: View Floor Plans
  ASSET: 6 changes (ADDED)
    - Snippet (Amenities): ['Pool', 'Fitness Center', 'Pet Friendly']
```

**Verdict: routine.** Every count lands on a date you worked, on a surface
you worked. Nothing to escalate — and note what this did NOT need: no
`change_event`, no actor lookup, because nothing failed the
routine-vs-investigate read.

## Example 2 — the Saturday cluster (bulk signature → attribution ladder)

**Ask:** "Anything odd in Kestrel Automotive lately?" CID 2345678901.

```
2026-07-18:
  CAMPAIGN_BUDGET: 2 changes (CHANGED)
  CAMPAIGN: 3 changes (CHANGED)
  AD_GROUP_AD: 58 changes (ADDED)
```

July 18 is a Saturday. No import was scheduled, no rules run weekends, and 58
new ads plus budget changes is a bulk signature on a money-adjacent surface —
this fails the routine read twice (date nobody worked × surfaces nobody
scheduled). But per the invariant, `change_status` alone convicts nobody: it
has no actor data. The change is 5 days old — **ladder step 1**, the
`change_event` pattern from the reference.

The actor columns split the cluster in two:

| Rows | `user_email` | `client_type` | Read |
|---|---|---|---|
| The 2 budget + 3 campaign rows | (a teammate) | `GOOGLE_ADS_RECOMMENDATIONS` | Auto-applied recommendations — settings-side, known feature, wasn't a person on Saturday at all |
| The 58 `AD_GROUP_AD` rows | An address on a domain nobody recognizes | `GOOGLE_ADS_API` | Unrecognized actor with API access — this is no longer a change-history question |

Half the scare dissolves at step 1 — that's the point of attributing before
escalating. The other half escalates for real: an unknown email mutating ads
via API means *access* is the question. Route to
[`mcc-hack-audit`](../mcc-hack-audit/) for the manager-access map (and
remember: the link acceptance itself never appears in change history — the
absence of a "link added" event here means nothing).

## Example 3 — the 90-day wall, and the window that eats its own tail

**Ask:** "Pull everything since January" — asked on 2026-07-23.

```
$ python scripts/check_change_history.py 2345678901 --start 2026-01-01 --end 2026-07-23
```

The run dies in a Python traceback — a `GoogleAdsException`, not a clean
error line (the script has no API try/except). The part that matters is the
API's own message inside it: **"The requested start date is too old. It
cannot be older than 90 days."** (`START_DATE_TOO_OLD`).

The wrong move is treating the traceback as a broken install and debugging
the environment. The right read: the window is illegal — clamp to the last
90 days for the API, and name the web UI's 2-year Change History export as
the only route to January (rules, escalation default). No amount of retrying
changes an API limit.

The clamped re-run has its own trap. A single 90-day query on this busy
account comes back with heavy recent dates and a suspiciously quiet April —
total rows right at the cap. That's `LIMIT 500` newest-first eating the tail
(reference), not a quiet April. Slice month-by-month — each slice gets its
own 500-row budget:

```
python scripts/check_change_history.py 2345678901 --start 2026-04-24 --end 2026-06-01
python scripts/check_change_history.py 2345678901 --start 2026-06-01 --end 2026-07-01
python scripts/check_change_history.py 2345678901 --start 2026-07-01 --end 2026-07-23
```

One more absence that isn't evidence: work done in May on resources that were
edited again in July won't show in the May slice at all — one row per
resource, dated by its **last** change (reference). The slices answer "what
was last touched when," not "everything that ever happened in each month."
