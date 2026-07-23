---
name: rsa-refresh
description: Refresh RSA ad copy by scraping the business website, identifying LOW-performing assets, and generating replacement headlines and descriptions using AI. Auto-invoke when user says 'refresh RSAs for [account]', 'update RSA assets', 'rewrite RSAs', or 'replace low-performing RSA assets'. Uses Firecrawl for scraping and Claude for copy generation.
---

# RSA Refresh Skill

Refreshes Responsive Search Ad copy for **one account** by replacing
low-performing assets with new headlines and descriptions verified against
the actual business website. One operator (or agent) owns the workflow end
to end: prepare context → make the refresh-vs-rebuild call
([`rules.md`](rules.md)) → generate copy under the reference standards →
merge to a review sheet → review → import via Google Ads Editor.

The core rule at every step: **Empty > Inaccurate** — no slot ever carries
a claim the website doesn't verify.

## Workflow

### Stage 1: Prepare Context
```bash
python scripts/rsa_refresh_generator.py \
  --cid YOUR_CID \
  --sheet-id YOUR_SHEET_ID \
  --prepare-for-claude
```

This will:
1. Query existing RSAs and asset performance labels (BEST/GOOD/LOW/LEARNING)
2. Scrape the business website using Firecrawl (with fallbacks)
3. Extract basic property/business info
4. Output `rsa_context_{cid}.json` with all data Stage 2 needs

**Before generating anything**, read the context per `rules.md`: check
`features.scrape_failed` (Stage 1 writes the JSON even when the scrape
failed — generating from an empty `website_text` is forbidden), then make
the refresh-vs-rebuild call from the label spread.

### Stage 2: Generate Copy (Claude Code)
Read `rsa_context_{cid}.json` and generate replacement headlines +
descriptions following the reference docs:
- `references/pm-headline-structure.md` -- 15 headline rules (1 customizer + 14 AI-generated)
- `references/description-voice-lifting.md` -- 3 descriptions with voice lifting technique
- `references/hallucination-filter.md` -- Defense-in-depth filter for unverified claims (NOT embedded in the context JSON — load it from this folder)

Save output as `copy_{cid}.json` with format:
```json
{
  "headlines": {"AD_ID_1": ["H1", "H2", ...], "AD_ID_2": [...]},
  "descriptions": ["D1", "D2", "D3"]
}
```

In refresh mode, re-include every existing headline worth keeping — the
script mechanically preserves **customizer assets only**; anything else
survives by being in this file (`rules.md` owns that call).

### Stage 3: Resume and Write to Sheet
```bash
python scripts/rsa_refresh_generator.py \
  --cid YOUR_CID \
  --sheet-id YOUR_SHEET_ID \
  --copy-file copy_YOUR_CID.json
```

This merges the generated copy with the live ad structure and writes
"Original RSAs" and "Refreshed RSAs" tabs. **Append is the default write
mode** — add `--clear` when re-running the same account. Review in the
sheet before importing to Google Ads Editor. Exact merge gates (30/90
length, dedupe, the below-10-headlines skip) and both tabs' column layouts:
[`references/refresh-contract.md`](references/refresh-contract.md).

## After the run — operator duties

1. **Review the Refreshed tab against `rules.md`** before any import:
   Validation Status `N/A` is the normal public default; `Changes Made` is
   the merge's log; ad groups missing from both tabs were skipped
   (console `[SKIP]` lines — below 10 headlines).
2. **Rule out the false alarms** — all-`NO_DATA` labels, error rows on a
   resume, doubled rows, the wrong-site scrape — per the table in
   `rules.md` before reacting to any of them.
3. **Import via Google Ads Editor** — the sheet is a review queue; the
   import is always the human's move.
4. **Measure**: re-run the baseline after the new copy has served ~30 days
   and read the two `RSA Baseline` rows side by side.

## What this skill deliberately does NOT do

- **No mutations.** Output is a review sheet; the only write path into
  Google Ads is you importing through Editor.
- **No autonomous copy.** The script refuses to generate copy itself
  (direct automated mode raises with instructions to use the handoff) —
  Stage 2 is an agent applying the reference standards, and there is no
  flag that bypasses it.
- **No mechanical preservation beyond customizers.** BEST/GOOD assets
  survive a refresh because Stage 2 re-includes them, not because the
  script protects them.
- **No after-measurement.** The baseline captures *before*; the comparison
  is a later re-capture read side by side — no diffing logic ships.
- **No multi-account batching.** One `--cid` per run (append mode is how
  runs accumulate into one sheet). For literal text swaps across many
  accounts at once, that's [`rsa-bulk-edit`](../rsa-bulk-edit/).
- **No out-of-the-box verticals beyond property management.** The
  references and helpers are PM-tuned; adapting is a deliberate step (see
  Vertical Note).

## Files in this skill

| File | Purpose |
|------|---------|
| `SKILL.md` | This file — the three-stage workflow + routing |
| `README.md` | Zero-context setup: install, prerequisites, first run |
| `rules.md` | Judgment layer: refresh-vs-rebuild, baseline reading, false alarms, escalation |
| `examples.md` | Worked reads: a surgical refresh, the prepare-mode scrape trap, the baseline zeros misread |
| `references/refresh-contract.md` | Exact mechanics: selection, file formats, merge gates, sheet + baseline contracts, enrichment gating |
| `references/pm-headline-structure.md` | The 15-headline standard (embedded into the context JSON at Stage 1) |
| `references/description-voice-lifting.md` | The 3-description standard + voice lifting (embedded at Stage 1) |
| `references/hallucination-filter.md` | Forbidden-claim filter applied at Stage 2 (loaded from this folder) |
| `scripts/rsa_refresh_generator.py` | Stages 1 and 3: queries, scrape, context/merge, sheet write |
| `scripts/rsa_baseline_snapshot.py` | Pre-refresh metrics capture (standalone or via `--baseline-sheet-id`) |

`rsa_context_{cid}.json` and `copy_{cid}.json` are runtime artifacts in
your working directory — never part of the skill folder.

## When to load a sibling skill

| Situation | Load |
|---|---|
| The account needs a ground-up RSA set — no salvageable copy, a new account, or you want the shipped SERP competitor analysis + GBP review pipeline | [`rsa-single-account`](../rsa-single-account/) |
| The change is a uniform literal text swap across existing ads (rebrand, spelling, customizer retirement) — no copy judgment | [`rsa-bulk-edit`](../rsa-bulk-edit/) |
| Always at Stage 2, before any claim lands in the copy file | [`ad-copy-verification-standard`](../ad-copy-verification-standard/) |
| Stage-2 copywriting craft beyond the PM structure (the 23-element framework) | [`ad-copy-generation-framework`](../ad-copy-generation-framework/) |
| The baseline raises account-wide questions (Quality Score, structure, conversions) | [`account-diagnostic`](../account-diagnostic/) |
| Reading baseline impression-share movement (Search IS, lost-to-rank/budget) | [`impression-share-diagnostics`](../impression-share-diagnostics/) |
| No `google-ads.yaml` yet, or a 403 on the sheet write | [`google-ads-api-setup`](../google-ads-api-setup/) |

## Prerequisites
- `google-ads.yaml` at project root (Google Ads API credentials) — see the [google-ads-api-setup](../google-ads-api-setup/) skill if you don't have one
- `token-sheets.json` at project root **OR** a refresh token in `google-ads.yaml` with the spreadsheets scope (the setup skill's generator grants `spreadsheets` + `drive.readonly` by default — token predates that? re-run the generator once)
- `FIRECRAWL_API_KEY` environment variable (set in `.env` or shell — get a key at firecrawl.dev)
- `pip install google-ads gspread google-auth pyyaml python-dotenv firecrawl-py requests beautifulsoup4 playwright`

Override paths if needed:
```bash
--config path/to/google-ads.yaml --sheets-token path/to/token-sheets.json
```

## Optional: Pre-Refresh Baseline
```bash
python scripts/rsa_baseline_snapshot.py \
  --cid YOUR_CID \
  --account-name "Account Display Name" \
  --sheet-id YOUR_SHEET_ID
```
Captures IWQS, QS components, ad metrics, and impression share before making
changes so you can measure improvement afterward. Writes one dated row per
capture to an "RSA Baseline" tab.

You can also have the generator capture the baseline automatically by adding
`--baseline-sheet-id YOUR_SHEET_ID` to Stage 1 — **prefer this**: the
integrated capture also fills the asset-label counts, which a standalone run
always writes as 0 (contract §baseline; `rules.md` has the misread).

## Vertical Note

The reference docs under `references/` are tuned for **property management**
(apartment / rental) accounts, and the headline/description references are
embedded into the context JSON at Stage 1 — they are the operative standard.
To adapt for another vertical:

1. Replace the three files under `references/` with your own headline
   structure, voice guide, and hallucination filter — this alone changes
   what Stage 2 is instructed to write
2. Optionally align the in-script scaffolding (`HALLUCINATION_PATTERNS`,
   `generate_keyword_headlines`, `generate_brand_headline`) if you build
   automation on top of it — the shipped three-stage flow never invokes
   these helpers, so the reference files are what governs
   (contract §helpers)

## Optional Enhancements

Set these env vars to enable additional context when generating copy:

- `COMPLIANCE_PATH` — directory containing a `compliance/ad_copy_validator.py` module to add geographic validation (checks headlines reference the correct city/state)
- `SERP_API_PATH` — directory containing `get_gmb_reviews.py` and `analyze_competitors_for_rsa.py` to add Google My Business social proof and competitor USP analysis to the context JSON

Both are optional. The script gracefully skips these features when the
modules aren't available. Interface details, the city/state gating that
couples the two hooks, and the fact that
[`rsa-single-account`](../rsa-single-account/) ships SERP modules this hook
can import: [`references/refresh-contract.md`](references/refresh-contract.md)
§enrichment.

## Safety

Read-only against Google Ads — the scripts run GAQL SELECT queries and
write only to the review sheet you own. Ad copy reaches Google Ads solely
through your Google Ads Editor import, after the review pass in `rules.md`.
