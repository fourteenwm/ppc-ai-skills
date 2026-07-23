# Worked Examples — three refresh reads

Three runs from real-shaped situations, all data synthetic. Each shows the
decision path, not just the commands. Mechanics referenced here are defined
in [`references/refresh-contract.md`](references/refresh-contract.md);
the judgment calls follow [`rules.md`](rules.md).

---

## Example 1 — Routine surgical refresh (labels trustworthy)

**Fernbrook Flats** (CID `1234567890`), quarterly copy pass. Stage 1:

```
python scripts/rsa_refresh_generator.py --cid 1234567890 \
  --sheet-id YOUR_SHEET_ID --baseline-sheet-id YOUR_SHEET_ID \
  --prepare-for-claude
```

Console (public configuration — no compliance/SERP modules):

```
Found 4 enabled RSA ads
Querying asset performance labels...
...
Scraping property website with Firecrawl: https://www.fernbrook-flats.example.com
Firecrawl scraped 11482 characters
...
[GMB] SERP API not available - skipping GMB lookup
[COMPETITOR] SERP API not available - skipping competitor analysis
[CLAUDE CODE MODE] Context saved to: rsa_context_1234567890.json
```

**The read, before writing anything:** the context JSON shows four ad groups
(`2 Bedrooms`, `1 Bedroom`, `Brand`, `Kingsbury District`) with a healthy
label spread — mostly GOOD with one BEST, and 2–4 LOW per ad group;
`headlines_needed` reads 2–4. Per `rules.md` this is the **refresh** case:
labels can guide surgery, structure is keyword-driven, voice is right.

**Stage 2:** for each ad, the copy file re-includes every non-LOW headline
verbatim, then adds replacements for the LOW slots only — each new line
verified against `website_text` (the sauna + two-pool combo is on the site;
"resort-style" is not, so it never appears). Descriptions: one amenity
formula + two voice-lifted sentences per
`references/description-voice-lifting.md`. `gmb_social_proof` is `null`, so
no rating headline — an extra feature headline instead.

**Stage 3** (`--clear` — same-account iteration, per rules invariant #5):

```
  Customizers preserved: 4 headlines, 4 descriptions
  Generated descriptions applied: 12
  Total RSAs: 4
...
[VALIDATION] Skipped (compliance module not available)
...
Wrote 4 rows to Refreshed RSAs tab
```

**Sheet review before Editor:** Validation Status `N/A` is the expected
public default, not a warning. One ad shows 14 headlines — `Changes Made`
logs no length skip, so it was a silent dedupe drop (a re-included GOOD
headline duplicated a new keyword line, case-insensitively). Fine: ≥10
ships. Import the Refreshed tab via Google Ads Editor; the baseline row
written this morning is the *before* for the ~30-day re-capture.

---

## Example 2 — EDGE: the prepare-mode scrape trap (context written anyway)

**Larkfield Commons** (CID `2345678901`). Stage 1 ends like this:

```
WARNING: All scraping methods failed for https://apply.leasehub.example.com/larkfield-commons - headlines will be generic only
...
Property name from URL: Apply
WARNING: No website content available
...
[CLAUDE CODE MODE] Context saved to: rsa_context_2345678901.json
```

**The near-miss:** the context file exists, the "Next steps" block printed,
and the ad-group names alone are enough to draft plausible apartment copy.
Stage 1 did **not** stop — prepare mode writes the context JSON even on a
failed scrape (contract §Stage 1). Nothing in the mechanics prevents
generating from vibes here.

**The correct read:** `features.scrape_failed` is `true`, `website_text` is
empty, and the property name extracted from the URL is literally "Apply" —
three tells in one file. Per the first invariant in `rules.md`: **STOP.
Zero copy gets written.**

**Root cause, from the same tells:** `property_url` is the *first ad's*
final URL, and this account's first ad pointed at a third-party leasing
portal (`apply.leasehub…`), not the property site — a URL that blocks
scrapers and describes nothing. The fix is upstream: correct the ads' final
URLs (or scrape after the account's real domain leads), then re-run
Stage 1. What the fix is **not**: writing headlines from the property name
and hoping. Empty > Inaccurate is the whole skill.

---

## Example 3 — EDGE: the standalone-baseline zeros misread

**Copper Hollow Apartments** (CID `3456789012`). Before a planned refresh,
a standalone baseline:

```
python scripts/rsa_baseline_snapshot.py --cid 3456789012 \
  --account-name "Copper Hollow Apartments" --sheet-id YOUR_SHEET_ID
```

```
  [Baseline] === Copper Hollow Apartments (345-678-9012) ===
  IWQS: 6.1 (AVERAGE)
  Scored Keywords: 38  |  KW Impressions: 41,203
...
  Assets: Best=0 Good=0 Low=0 Learning=0
...
  [Baseline] Appended row 2 to 'RSA Baseline'
```

**The near-miss:** "every asset count is zero — Google hasn't labeled
anything, so there's nothing to guide a surgical pass; rebuild everything."
That read would discard real evidence.

**The correct read (contract §baseline):** standalone runs pass **no asset
data** — the four Assets columns are always 0 in this mode. It's an
artifact of *how the baseline was invoked*, not a fact about the account.
The asset counts only populate when the baseline rides Stage 1
(`--baseline-sheet-id`), where the generator's performance query feeds it.

**Resolution:** run Stage 1 with `--baseline-sheet-id`. The appended row now
reads `Assets: Best=6 Good=21 Low=9 Learning=4` — a trustworthy spread, so
per `rules.md` this is a **refresh**, sized by the 9 LOW slots. Had the
integrated capture *also* shown zeros alongside a
`Warning: Could not query asset performance` line, that would be the other
false alarm in the table — a failed label query, fixed by access, never by
rebuilding.
