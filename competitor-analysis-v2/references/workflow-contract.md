# Workflow Contract — Competitor Analysis v2

> **Source of truth:** the seven files in `prompts/` own their stages' methodology —
> scoring attributes, bands, schemas, and process rules live *there* and are never
> restated here or in `SKILL.md`. `scripts/screenshot.cjs` owns capture mechanics (its
> claims below are line-derived). `templates/` own output structure. This contract owns
> what none of them can: which file is authoritative for what, how their internal
> numbering maps onto the 8-phase workflow, and what the one script actually does. If a
> prompt, template, or the script changes, update this contract and the CHANGELOG in
> the same commit. Judgment (competitor selection, screenshot reads, angle choice)
> lives in `rules.md`.

---

## Authority map — one home per fact

| File | Sole owner of | Never restated in |
|---|---|---|
| `prompts/website-extraction.md` | The 21-field XML schema, extraction prompt text, field-purpose table | SKILL, this contract |
| `prompts/strategic-analysis.md` | Attributes 1-15, per-attribute 0-3 criteria, category structure (9/9/6/9/6/6 = 45), archetypes, interpretation bands | everywhere else |
| `prompts/tactical-scan.md` | Attributes 16-22, ✅/⚠️/❌ flag semantics, 21-point bands, quick-win framing | everywhere else |
| `prompts/gap-identification.md` | Messaging matrix, positioning-map axes, emotional landscape, the six-step gap process, table-stakes/differentiator/whitespace tests | everywhere else |
| `prompts/client-verification.md` | The verification law (explicit-evidence-only, source citations, ✅/❌ fillability), page-scrape checklist, output format | everywhere else |
| `prompts/angle-development.md` | Angle structure (7 elements), QUICK WIN / STRATEGIC BET / EXPERIMENTAL criteria, character-limit workflow | everywhere else |
| `prompts/analysis-framework.md` | Blank scaffolds: matrices, profile templates, SWOT, pattern tables, executive-summary shape | everywhere else |
| `templates/client-gift.md` | The Client Gift's 15-section structure and tone rules | SKILL (points only) |
| `templates/ads-angle-brief.md` | The 1-page brief's 7 sections, vertical notes, quality checklist | SKILL (points only) |
| `templates/template.css` | PDF styling | — |
| `sales/service-page-copy.md` | Copy for *selling this service* (two audience framings, intro/delivery emails, testimonial capture) — a business asset, not a runtime input to any phase | — |

## The numbering translation table

Four prompt files carry internal phase labels from the **v1.0 framework** (strategic →
tactical → gaps → verification → angles); one was renumbered to the v2 workflow; the
brief template mixes both. The prompts are correct about *sequence* — only the labels
predate the 8-phase workflow. Translate on contact; do not "fix" a prompt mid-run:

| File says | Means | Runs at workflow phase |
|---|---|---|
| `website-extraction.md` *(no label)* | Extraction | **Phase 3** |
| `strategic-analysis.md` "(Phase 1)" | First ad-scoring pass | **Phase 4** |
| `tactical-scan.md` "(Phase 2)" | Second ad-scoring pass | **Phase 4** |
| `gap-identification.md` "(Phase 5)" — and its references to "Phase 3 XML", "Phase 4 ads", "Phase 6 verification" | Already renumbered to the v2 workflow | **Phase 5** ✓ |
| `client-verification.md` "(Phase 4)" — its "Phase 3" = gap identification, its "Phase 5" = angle development | Verification | **Phase 6** |
| `angle-development.md` "(Phase 5)" — its "Phase 4" = verification, its "Phases 1-2" = strategic/tactical | Angle development | **Between 6 and 7** — feeds the Ads Angle Brief; no workflow number of its own |
| `templates/ads-angle-brief.md` "(Phase 5)" / "(Phase 6)" | Gap identification ✓ / angle development | Phase 5 / post-6 |

Two cross-file facts that follow from the shared v1 ancestry:

- **Attribute numbering is continuous 1-22 across two files.** The strategic prompt's
  archetype list cites "high scores on 13, 19" — attribute 19 (Promotional Hooks) lives
  in the *tactical* file. Not an error; the two prompts score one framework.
- The strategic and tactical prompts share their worked example (the same shop-management
  ad scored 26/45 and 7/21), and `client-verification.md` + `angle-development.md` share
  one example chain (5 gaps in → 3 verified → 3 angles out). Read them as continuations.

## Which prompts run, per output

| Output requested | Phases run | Prompts consumed |
|---|---|---|
| Client Gift only | 1-3, 5-8 (Phase 4 only if ads provided) | extraction, gap-identification (+ analysis-framework scaffolds), client-verification |
| Ads Angle Brief only | 1-6 + angle development (Phase 8 not needed — brief is markdown) | extraction, strategic + tactical (if ads), gap-identification, client-verification, angle-development |
| Both | 1-8 | all seven |

Phase 4 is legitimately skippable (no competitor ads available) — the workflow notes the
skip and website intelligence carries the analysis. Phases 3, 5, and 6 are never
skippable. Verification (Phase 6) gates *both* outputs: the gift's recommendations
section and every angle in the brief.

## screenshot.cjs — line-derived mechanics

The skill's only code. Nothing in it touches Google Ads; it needs no credentials.

**Argument parsing (:117-148).** Positional args are kept only if they start with
`http` (:137-139) — a bare `client.com` is **silently dropped**, not an error, so a
6-URL command with one schemeless URL yields 5 screenshots with no complaint. Unknown
flags are silently ignored too, and their values are then read as (usually non-http)
positionals and dropped — a typo like `--out` sends output to the default folder
`/tmp/competitor-report/screenshots` (:121). `--urls-file` reads one URL per line,
trimmed, same http-prefix filter (:124-134). Zero URLs after parsing → usage text,
exit 1.

**Capture pass (:158-172).** Sequential, one URL at a time, headless Chromium, viewport
1280×800, 30s navigation timeout, `networkidle` wait, no custom user agent. Each page
gets a 2s settle, a 500px-per-100ms scroll to the bottom (triggers lazy-load), a scroll
back to top, 1s more, then a full-page PNG (:47-84).

**Filenames (:76-78).** `<index>-<domain>.png` where index is the URL's **1-based
position in your argument order** and domain is the hostname with leading `www.`
stripped and dots turned to dashes. Put the client first and `1-*.png` is always the
client — the convention the gift's screenshot grid assumes.

**Retry pass (:177-192).** Failures from pass 1 are retried once, all together, with
three changes: **headful** browser (`headless: false` — this opens real windows and
therefore *fails on display-less servers*), the bundled desktop-Chrome user agent, and
`domcontentloaded` instead of `networkidle` (plus a 3s settle). Retried failures are
kept as failure records.

**Exit and summary (:197-226).** The summary prints after retries: a 50-char `=` rule,
`Screenshots captured: X/Y`, a `Failed URLs:` list if any remain, `Metadata saved:`,
and the saved file paths. **Partial failure still exits 0** — the only exit-1 paths are
zero parsed URLs, a missing `--urls-file`, and a fatal error. Read the `X/Y` line and
the metadata, never the exit code.

**`screenshots.json` — the run's status surface (:209-221).** Written to the output
folder: `outputFolder`, `capturedAt` (ISO timestamp), `totalUrls`, `successful`,
`failed`, and a per-URL `screenshots` array (`success`, `url`, `filepath`, `filename`,
`title`, `index`, `retried`). Failure entries carry `error` and **no filepath**. A cold
session can reconstruct what ran, when, and what's missing from this file alone —
nothing else persists, and nothing lands in the skill folder.

## Credential story

None, end to end. Screenshots and PDF rendering are local Playwright; extraction and
verification are WebFetch/WebSearch/Firecrawl; ad copy for Phase 4 arrives from a SERP
tool or pasted text. No Google Ads API surface exists anywhere in this skill.
