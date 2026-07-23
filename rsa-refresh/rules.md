# Rules — driving a refresh and reading what comes back

Decision logic for the operator (or agent) running the three stages: when a
refresh is the right instrument, how to read the context JSON and the
baseline, and what to check before anything reaches Google Ads Editor.
[`examples.md`](examples.md) has worked reads;
[`references/refresh-contract.md`](references/refresh-contract.md) has the
exact selection/merge/sheet mechanics; the three copy references own the
generation standard itself.

## Invariants (never break these)

- **Empty > Inaccurate.** A headline or description slot stays empty before
  it carries a claim the website doesn't verify. A failed scrape means STOP
  — and note the mode split: prepare mode **still writes the context JSON**
  with `scrape_failed: true` and empty `website_text`. Checking that flag is
  Stage 2's first act; generating "from what I know about apartments" is
  exactly the failure this skill exists to prevent.
- **The script never invents copy.** Generation happens at Stage 2, by an
  agent following the reference files; the script refuses to run without a
  copy file (direct automated mode raises). The merge only assembles and
  gates — 30/90 length, dedupe, the 15/4 caps, the <10 skip. If the copy
  file contains a junk headline under 30 characters, the sheet gets it.
  Review is a Stage-2/post-sheet duty, not something the script does.
- **Only customizers survive mechanically.** Every non-customizer headline
  the account should keep must be re-included in `copy_{cid}.json`. "The
  script preserves BEST and GOOD" is shorthand for *the refresh-mode
  workflow* preserving them — via your copy file, per the call below.
- **The sheet is a review queue, not a deployment.** Nothing touches Google
  Ads until a human imports the Refreshed tab through Google Ads Editor.
  The review pass below happens before any import, every time.
- **Decide the write mode before running.** Append is the default — re-runs
  of the same account without `--clear` stack rows. Multi-account batches
  into one sheet is what append is *for*; same-account iteration is what
  `--clear` is for.

## Refresh vs rebuild — the call that shapes Stage 2

Read the context JSON's labels before writing anything.

**REFRESH (surgical)** when the labels can guide surgery: a real
BEST/GOOD/LOW spread across ad groups, sound keyword-driven structure, and
copy in the right voice. Stage 2 then re-includes the non-LOW headlines
verbatim and writes new copy only for the LOW (and empty) slots —
`headlines_needed` per ad is the sizing hint. The point of refresh mode is
not disturbing proven assets: Google's labels are evidence, and deleting a
BEST headline throws that evidence away.

**REBUILD (fresh set)** when the labels can't guide anything or the copy
shouldn't survive: labels mostly `NO_DATA`/`LEARNING` (nothing proven worth
keeping), generic filler structure that predates the headline standard, a
rebrand/repositioning, or verification problems throughout the existing
copy. Stage 2 writes the full 14-headline structure per
`references/pm-headline-structure.md` and ignores `headlines_needed`.
Customizers still ride along automatically.

**The tell:** count real `LOW` labels against the total. A handful of LOW
among BEST/GOOD → refresh. LOW everywhere, or labels absent → the labels
can't steer a surgical pass; rebuild. Mixed account (two strong ad groups,
three weak) → the call is per ad group, not per account — the copy file is
keyed by ad ID precisely so you can refresh some and rebuild others.

Either way, descriptions are account-wide: 3 generated once, customizer
descriptions preserved in place.

## Reading the baseline snapshot

The baseline is **before/after evidence**, not a health audit — it exists so
the refresh's effect is measurable. Capture it in Stage 1
(`--baseline-sheet-id`) or standalone *before* the Editor import; re-run it
after the new copy has served long enough to re-label (30+ days), and read
the two rows side by side.

- **Assets columns all 0 on a standalone run** = mode artifact (standalone
  passes no asset data), not "no labeled assets." Only the integrated
  Stage-1 capture fills them.
- **A row of `N/A`s** = the queries failed (access, wrong CID) — not an
  account with no data. Check the console warnings.
- IWQS rating thresholds (<5 / <7) are the snapshot's own classification;
  deeper Quality Score work belongs to
  [`account-diagnostic`](../account-diagnostic/), and impression-share
  movement (Search IS, lost-to-rank, lost-to-budget) reads per
  [`impression-share-diagnostics`](../impression-share-diagnostics/) —
  don't re-derive those disciplines from one baseline row.

## What governs Stage 2 (the compliance chain)

- The context JSON's `instructions` field embeds the headline structure and
  description references verbatim — but **not**
  `references/hallucination-filter.md`. Stage 2 loads that file from the
  skill folder and applies it; it is the operative filter standard (the
  script's in-code pattern list is never invoked by the shipped flow).
- [`ad-copy-verification-standard`](../ad-copy-verification-standard/)
  applies to every claim: verified from `website_text` (or the GMB data),
  cited, never assumed. If `gmb_social_proof` has headlines, use the first
  one verbatim; if it's `null`, write an additional feature headline — never
  an invented rating.
- `competitor_insights`, when present, steers emphasis: lead with
  `unique_client_usps`, de-emphasize `avoid_saturated_usps`. When it's
  `null` (the common public case — see the false-alarm table), generate
  from the website alone.

## False-alarm / edge table — rule these out before reacting

| Signal | Likely cause | Verify by | Then |
|---|---|---|---|
| Every asset `NO_DATA`, `headlines_needed` 0 everywhere | The performance query failed — non-fatal, run continued | Stage-1 console: `Warning: Could not query asset performance` | Fix access, re-run Stage 1. Don't read it as "fully optimized" or "labels broken" |
| `headlines_needed` 0 on one ad you expected to refresh | 15 existing headlines all non-LOW (customizers, UNKNOWN, NO_DATA count as non-LOW) | The ad's `existing_headlines` labels in the context JSON | It's a sizing hint, not an order — rebuild mode ignores it; refresh mode means this ad needs nothing |
| Error rows in the sheet after Stage 3, but Stage 1 scraped fine | **Resume-time re-scrape failed** — Stage 3 re-runs the scrape and its failure gate, and doesn't otherwise use the content | Stage-3 console: the scrape-failure block | Your copy file is fine. Retry Stage 3 when the site is reachable |
| An ad group missing from both tabs | The <10-headline skip | Stage-3 console `[SKIP]` lines | Supply more headlines for that ad ID in the copy file, re-run Stage 3 |
| Rows doubled/tripled in a tab | Append default across re-runs | Row count vs runs | Use `--clear` for same-account iteration; read only the newest block meanwhile |
| Generated copy references the wrong property/city | `property_url` is the **first ad's** final URL — multi-domain or vanity/portal URLs scrape the wrong site | `property_url` in the context JSON vs the account's real site | Fix the ads' final URLs (or wait for the right first ad) and re-run Stage 1. Never patch by inventing content |
| `gmb_social_proof` / `competitor_insights` null despite `SERP_API_PATH` set | The city/state gate: without the compliance module, features carry only a URL-derived property name | Stage-1 console: `[GMB] Missing property name/city/state` | Expected public-config behavior (contract §gating). Generate without social proof |
| Refreshed tab shows fewer than 15 headlines on an ad | Dedupe dropped case-insensitive duplicates (silently), or >30-char skips, or Stage 2 under-supplied | `Changes Made` column (length skips are logged; dedupe drops are not) | ≥10 ships and serves; add replacements in the copy file only if the loss was real copy, not duplicates |

## Escalation default

When a claim can't be verified, the slot stays **empty**. When an ad group's
refresh-vs-rebuild call is ambiguous, **hold it back** — leave its ID out of
the copy file (it skips cleanly, console-logged) rather than half-rebuilding
it. When the sheet read surfaces anything you can't explain from the
contract, resolve it before the Editor import — never after. The import
itself is always the human's move.
