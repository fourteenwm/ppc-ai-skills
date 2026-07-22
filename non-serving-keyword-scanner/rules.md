# Rules — reading and triaging a scan report

Decision logic for what happens AFTER the script writes the review tab.
`examples.md` has worked reads; `references/scan-contract.md` has the exact
selection and output contract; `SKILL.md` is the run guide.

## Invariants (never break these)

- **Report only — the scanner never pauses.** Human-in-the-loop is the
  design, not a missing feature. Every pause is a human decision executed in
  the Google Ads UI or Editor. If pausing ever gets scripted, that script is
  a mutation and belongs behind the
  [`mutation-safety`](../mutation-safety/) approval flow — it is not part of
  this skill.
- **Zero impressions means zero spend — this is a hygiene instrument, not a
  savings instrument.** Every flagged keyword cost $0.00 across the window
  (clicks require impressions). Never present a pause list as budget
  recovery. The value is structural: cleaner accounts, honest coverage (no
  "we're covering that term" illusions), and less noise in every future
  audit.
- **The tab is a snapshot, not a log.** Each run clears and rewrites the tab.
  A row that disappears between runs is NOT evidence the keyword recovered —
  see the false-signal table. If you need run-over-run history, write dated
  tabs (`--tab-name "Non-Serving 2026-07"`).
- **Flagged ≠ pause.** The sheet is a review queue, and every row gets one of
  three verdicts — Pause, Keep, or Investigate — only after the false-signal
  table has ruled out the benign causes. Bulk-pausing the whole tab skips
  the only judgment step this workflow has.
- **Current-state filter, window-scoped metrics.** The scan sees keywords
  that are enabled *now*, measured across the *whole* window. A keyword
  can't serve while any ancestor is paused — so a campaign or ad group that
  spent part of the window paused makes its entire subtree look dead, and a
  keyword added mid-window looks non-serving before it ever had a fair
  chance. Rule out these timeline artifacts before making structural reads
  (mechanics: `references/scan-contract.md`).

## Triage order — clusters before rows

Sort or pivot the tab by Account → Campaign → Ad Group before reading any
single row. Density is the signal: scattered singles are routine hygiene; a
dense cluster means something structural upstream of the keywords.

1. **Whole-account clusters** — most or all of an account's keywords flagged.
   This is never keyword rot; it's an account-level outage (nothing serving:
   billing, policy, every campaign limited). Route to
   [`account-diagnostic`](../account-diagnostic/) and STOP — no per-row
   verdicts. Pausing keywords in a dark account dismantles structure you'll
   want intact the day it's revived.
2. **Whole-campaign or whole-ad-group clusters** — one campaign's keywords
   all flagged. Campaign-level cause: recently re-enabled after a seasonal
   pause, launched inside the last few weeks, budget-starved, or its ads
   disapproved. Verify the campaign's story first (status change history,
   then [`impression-share-diagnostics`](../impression-share-diagnostics/)
   for auction-side causes) — the keywords are symptoms.
3. **Scattered singles** — the routine case. Per-row verdicts using the
   false-signal table, then the three-verdict definitions below.

Work clusters first, biggest first. The scattered remainder is never urgent —
a zero-impression keyword costs nothing today, so this review is
important-not-urgent by construction: batch it, don't firefight it.

## The three verdicts

- **Pause** — you can articulate why this keyword should never serve again:
  the service/product/location is discontinued, the term was misadded, or
  it's a redundant variant of a keyword that already serves the same intent.
  Pause is executed by a human in the UI/Editor, never by the scanner.
- **Keep** — the keyword is expected to be silent right now: seasonal terms
  out of season, genuinely rare-but-valuable niche terms, or rows from a
  cycling/dynamic ad group the exclusion filter didn't catch. Keep means:
  leave it enabled, annotate the sheet so next run's review is instant, and
  expect to see it again. Keeping is not hoarding — Google auto-pauses
  keywords at roughly **13 months of zero impressions** ("low activity"), so
  the platform itself is the eventual backstop. When that auto-pause lands,
  accept it; re-enabling without a structural change just restarts the same
  clock.
- **Investigate** — the interesting verdict: you *expected* this keyword to
  serve. Zero impressions on a term with real demand means something is
  blocking it, and pausing would bury the evidence. Suspects, in the order
  worth checking: a negative keyword blocking it (route to
  [`neg-conflict-finder`](../neg-conflict-finder/)), the query being
  absorbed by a broader keyword elsewhere in the account (confirm with an
  ad-hoc search-terms pull via [`google-ads-query`](../google-ads-query/);
  steer traffic back with negatives via the
  [`sqr-pipeline`](../sqr-pipeline/) and its review gate), Google's "low
  search volume" suppression (UI check — the scan can't see it), or
  rank/bid suppression at the campaign level
  ([`impression-share-diagnostics`](../impression-share-diagnostics/)).

## False-signal table — rule these out before any verdict

| Signal | Benign cause to rule out | Verify by | If benign |
|--------|--------------------------|-----------|-----------|
| Whole campaign flagged | Campaign re-enabled recently after a seasonal/deliberate pause — the window includes the dark months | Campaign status change history | Expected artifact. Re-scan that account with `--days` covering only the serving period (e.g. `--days 30`) and judge on that |
| Whole campaign flagged | Campaign launched in the last 7–14 days — bidding still ramping, low-volume keywords haven't had a fair auction yet | Campaign start date | Expected. Re-read after ~30 days of serving time |
| Individual keyword flagged | Keyword added mid-window, especially in the last 2 weeks | Keyword creation date (change history) | Expected — it stays flagged until its first impression. Escalate to Investigate only if still at zero after ~30 days |
| Seasonal terms flagged | Demand is calendar-gated (snow tires in August) | Term semantics vs. season | **Keep.** Pausing seasonal terms silently costs you next season — nobody remembers to re-enable them, and enabled-at-zero costs nothing |
| Keyword flagged despite real demand | Google "Low search volume" status — suppressed until search volume returns | Keyword status in the UI (the scan doesn't pull it) | Keep, or restructure toward higher-volume phrasing. Pausing a suppressed keyword changes nothing operationally |
| Rows from an inventory/rotation ad group | Keywords cycle in and out by design; the exclusion filter only catches ad groups *named exactly* "special"/"specials" | Ad group's purpose/naming convention | Known noise — verdict Keep, annotate so future runs are instant |
| Account shows 0 rows but an `API Error` printed | The account wasn't scanned — API-level failures print inline and still count as zero | The progress lines above the summary | Not a clean account. Fix access, re-scan (contract details: `references/scan-contract.md`) |
| Row from the last run is gone this run | Google's ~13-month low-activity auto-pause removed it from scan scope (paused keywords aren't scanned), or a teammate paused it | Keyword status + change history | Nothing recovered — the scan's scope shrank. Update your annotations; don't re-enable auto-paused keywords without a structural change |
| Far fewer rows than expected — or zero | The account's spend is in PMax/Display/Video; the scan covers Search campaigns only | Account's channel mix | A Search-less account legitimately returns nothing. Zero rows ≠ zero clutter — it can also mean zero *coverage* by this instrument |

## Escalation default

When a row's read is ambiguous — can't tell dead from suppressed from
seasonal — the verdict is **Keep + Investigate**, never Pause. When the tab
is huge and time is short, triage the clusters and batch the scattered rows
for a routine pass; never resolve time pressure with a blanket pause. The
scanner's job is making invisible clutter visible. Deciding what deserves to
die is the human's.
