# Rules — routine vs investigate, attribution, and the flag decisions

Decision logic around a read-only summary instrument. The script groups
what-changed-when counts; every judgment — whether a change pattern is
routine, who to attribute it to, which flag or resource fits the question —
is the operator's. [`examples.md`](examples.md) has worked reads;
[`references/history-windows.md`](references/history-windows.md) has the
exact window/query semantics.

## Invariants (never break these)

- **Read-only.** The script queries `change_status` and prints. Nothing is
  ever modified, and nothing is ever written to disk — **console output is
  the only artifact**. If a read matters, copy it out before the scrollback
  goes.
- **Counts, not detail.** A `change_status` row is a *resource* that changed,
  dated by its **last** change — never an edit log, never an actor, never
  old→new values. Conclusions that need "who" or "what exactly" need
  `change_event` (30-day window) or the UI — see the attribution ladder.
- **The 90-day wall is hard.** The API rejects older start dates
  (`START_DATE_TOO_OLD`); no retry or rephrasing gets past it. Beyond 90
  days, the answer lives in the web UI's 2-year Change History export — say
  so and route there.
- **Never conclude compromise from this script alone.** It has no actor
  data. "Unrecognized changes" is a trigger for the attribution ladder, not
  a verdict.

## Routine vs investigate — reading the grouped counts

A month of change history has a shape. Read the counts against what you know
was scheduled:

| Pattern | Routine explanation | Investigate when |
|---|---|---|
| `AD_GROUP_CRITERION` spike on one date | Negatives upload day, keyword build | You ran no negatives work that week; spike on a weekend/holiday |
| `ASSET` / `*_ASSET` churn across a few days | Extension refresh cycle | You don't run extension work and there's no agency doing it |
| Steady small `AD_GROUP_AD` counts | RSA edits landing over a week | Large `AD_GROUP_AD` counts in an account nobody's actively writing for |
| Hundreds of changes, one date, several types | Bulk signature: Editor import, bulk upload, automated rules, scripts | The bulk op isn't yours — no import, no rule, no script scheduled |
| `CAMPAIGN_BUDGET` or `BIDDING_STRATEGY` rows | Your documented budget/bid work | Any occurrence you can't map to your own log — money-adjacent surfaces first |
| `REMOVED` spike | Cleanup you planned | Removals you didn't plan, especially ads/keywords in a producing campaign |
| Changes during a known-dormant period | — | Anything at all: a "quiet" account that changed isn't quiet |

The tell is never the count alone — it's **count × date × surface vs your own
work log**. Big numbers on the day you ran an import are boring; small
numbers on a Saturday in a dormant account are not.

## The attribution ladder (when "who did this?" matters)

1. **Change is ≤ 30 days old** → query `change_event` (pattern in the
   reference): `user_email` names the person, `client_type` names the tool —
   `GOOGLE_ADS_RECOMMENDATIONS` (auto-apply), `GOOGLE_ADS_AUTOMATED_RULE`,
   `GOOGLE_ADS_EDITOR` etc. resolve most "wasn't me" mysteries without
   suspicion of a breach.
2. **30–90 days old** → the script's counts date and type the change;
   attribution needs the web UI's Change History (shows the user per change,
   2 years back).
3. **Unrecognized actor, or access is the question** → route to
   [`mcc-hack-audit`](../mcc-hack-audit/) for the manager-access map. Change
   history shows post-link activity but **never the link acceptance itself**
   (reference, "What neither resource shows").

## Flag decisions

- **`--detailed`** — use when the question is *which* extensions changed, not
  *whether* extensions changed (it prints sitelink/callout/snippet text).
  Only engages when the run could include `ASSET` / `CUSTOMER_ASSET` /
  `AD_GROUP_ASSET`; `--types CAMPAIGN_ASSET --detailed` silently runs the
  basic query (the script's gate doesn't include it). Detail lines dedupe and
  cap at 10 shown per date+type group (`... and N more`).
- **`--types`** — narrow *after* a broad pass, or when the question names a
  surface ("what keywords changed" → `AD_GROUP_CRITERION`). Narrowing also
  buys headroom against the 500-row cap in busy windows.
- **`--list-accounts`** — when you have a name, not a CID. It lists
  **ENABLED, non-manager** accounts under your `login_customer_id` only — a
  CANCELED account you need history for won't appear; pass its CID directly.
- **Window slicing** — month-by-month queries beat one 90-day query in busy
  accounts: each slice gets its own 500-row budget, and the output groups
  stay readable.

## False-alarm table

| Signal | Likely cause | Verify by | Then |
|---|---|---|---|
| Traceback ending in `START_DATE_TOO_OLD` | Window reaches past 90 days | Your `--start` vs today | Not a broken install — clamp to 90 days, route older asks to the UI export |
| Traceback on a dashed CID | The script passes the ID through as-is (no dash-stripping) | The positional arg | Re-run with the 10-digit undashed CID |
| The command just printed usage help | Missing `--start` or `--end` (both are required with a CID) | Your command line | Add both dates; that's the no-args behavior, not a crash |
| The last day of the window looks missing | Date-only bounds read as midnight — `<= '2026-06-30'` keeps almost none of June 30 | The bound semantics (reference) | Bound with the day after |
| Early window sparse, recent days heavy | `LIMIT 500` newest-first — the tail fell off | Total rows ≈ 500? | Slice the window smaller or narrow `--types` |
| June's work missing from a June query | The same resources were edited again later — `last_change_date_time` moved past your window | Query a window extending to now | Expected semantics (one row per resource, last change wins) — not lost history |
| `1 changes` in the output | The script always pluralizes | — | Cosmetic; ignore |
| Huge one-day counts | Bulk-op signature (import, rules, scripts) — not inherently hostile | Your own work log; `change_event` `client_type` if ≤ 30d | Attribute before escalating |
| Changes you don't recognize | Auto-applied recommendations, a co-manager, client-side edits | `change_event` `user_email` + `client_type` (≤ 30d) | Ladder step 1 before any breach theory |

## Escalation default

When a change can't be attributed after the ladder — unknown email, no
matching tool signature, or the window has expired — treat it as an
external-actor question: run [`mcc-hack-audit`](../mcc-hack-audit/) for the
access map and pull the UI Change History for the actor trail. When the
window makes an answer impossible (>90 days via API, >2 years anywhere), say
exactly that and name the UI export as the remaining route — an honest "the
API can't see that far back" beats a confident answer built on a window that
silently excluded the evidence.
