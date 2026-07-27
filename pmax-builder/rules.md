# Rules — PMax Builder

Decision logic for running builds. Mechanics live in
[`references/build-contract.md`](references/build-contract.md); the workflow
lives in [SKILL.md](SKILL.md). This file owns the judgment calls.

## Invariants

1. **The final URL comes from the account's live Search ads, never from the
   business name.** Before any build, pull the final URLs of the account's
   ENABLED Search ads and use the root domain they vote for (the SKILL.md
   workflow has the query). Never construct `<businessname>.com` from the
   campaign brief, the account name, or a task title. This rule exists
   because of a real incident: a PMax was once built on a domain guessed
   from the business name while the account's Search campaigns ran on a
   different domain — the campaign spent against the wrong site. The bundled
   generator writes whatever `--final-url` you hand it; this check is yours,
   not the script's.
2. **Ad copy is ingested verbatim, never retyped.** Sheet mode reads the
   copy cells directly — that is the point of it. If you paste copy manually,
   paste exactly what the source contains. Writing NEW copy is a different
   job with its own standards — see the routing table in SKILL.md.
3. **The CSV is the entire product.** This skill never touches a live
   account: no mutations, no uploads. Google Ads Editor import — a human
   reviewing rows before posting — is the deliberate safety gate. Anything
   that skips that review is outside this skill's design.
4. **Check the counts before you import.** The generator validates nothing:
   blank sheet rows silently shrink your copy, extras silently truncate, an
   unrecognized video URL passes through verbatim, and an end date can land
   before the start date. The console summary and a spot-check of the CSV's
   asset-group row are the verification surface. Two minutes there beats a
   failed import — or a quietly wrong campaign.
5. **Templates are the vertical configuration.** The generator builds
   whatever the four template files contain. Adapting this skill to a new
   vertical means editing templates, never the script.

## Sheets mode vs manual paste — picking the ad-copy source

| Situation | Mode | Why |
|---|---|---|
| Copy lives in a maintained "PMax Ad Copy" sheet (team-owned, reviewed) | `--sheet-id` | Verbatim ingestion straight from the source of truth — no transcription step to introduce errors. Preferred whenever the sheet exists. |
| Repeat builds for the same client | `--sheet-id` | The sheet persists between builds; re-runs stay reproducible. |
| One-off build, copy arrived in an email/doc | Manual flags | Standing up a sheet for a single build adds a failure surface (scopes, sharing) for zero reuse. |
| No Sheets-scoped token available (or a 403 you can't resolve now) | Manual flags | Manual mode needs no Google credentials at all — it is the zero-dependency path. |
| Both provided | The sheet wins | Contract fact — the manual flags are silently ignored. Don't pass both; it hides which source actually built the CSV. |

## Editing the templates for your vertical

The shipped `search_themes.json` and `audience_signals.json` are
**multifamily/apartment defaults**. Import them unedited and your campaign
targets apartment hunters — whatever your business sells.

| You are building for | Do this first |
|---|---|
| An apartment community / multifamily property | Nothing — the shipped themes and Renters/Moving-Soon signals ARE your vertical. |
| Any other vertical (auto repair, plumbing, dental, ...) | Replace the `generic` and `location_specific` lists in `search_themes.json` with your service terms (`{city}`/`{state}` substitution works only in `location_specific`), and replace or empty the three fields in `audience_signals.json`. |
| A vertical where Google's audience taxonomy has no good match | Set the `audience_signals.json` fields to `""` — remarketing (via `--remarketing-segments`) still applies; you simply ship no interest/life-event signals. |

`campaign_settings.json` holds house campaign defaults (bidding, networks,
automation opt-outs) — rarely edited, and note the contract's warning: its
`cta`, `default_budget_daily`, and `default_radius_miles` keys are inert.
`negative_locations.json` is country exclusions — edit only if you serve
internationally.

Theme-count changes are expected to move the summary's `Search Themes:` and
`Total rows:` lines — that is the template working, not a bug.

## False alarms and real traps

| Symptom | What it usually is | Check |
|---|---|---|
| `Headlines: 12` when the sheet "has 15" | Blank cells in rows 4-18, or copy parked in an ignored row (row 20 is skipped by design) | Count the sheet's filled cells against the console block; fix the sheet, re-run |
| Long headlines short by one | The 5th long headline sits in row 20 (the ignored short-headline slot) | Move it into rows 22-26 |
| `Dates: 2026-07-02 to 2026-06-30` | The late-June trap — default end date (this June 30) fell before the default start date | Re-run with `--end-date` next fiscal year; nothing serves from an end-before-start campaign |
| A full URL sitting in a Video ID column | Unrecognized YouTube URL shape (shorts links pass through verbatim) | Re-run with the bare 11-character ID |
| `Videos: 2` but one video is broken | The count tallies inputs, not valid extractions | Spot-check CSV columns 65+ before import |
| `Budget: $10.0/day` on a $50/day brief | The $10 default is deliberate — budget is set post-import | Adjust in Editor/UI after import (per SKILL.md manual steps) |
| `Search Themes: 8` not 14 | You edited the theme template — the count follows the file | Expected; confirm it matches your edited list length |
| 403 the moment the sheet is read | Refresh token minted without Sheets scopes | The error text says exactly this — re-run the api-setup generator once; or fall back to manual mode to keep moving |
| Start date lands on/counts a public holiday | The date helper skips weekends only | Pass `--start-date` explicitly around holidays |
| Import fails on encoding | The CSV was opened and re-saved (Excel re-encodes) | Regenerate; import the untouched file |

## Escalation defaults

- **Search ads vote for more than one root domain** → stop and ask the
  account owner which domain is canonical. Never build against a mixed-domain
  account on majority vote alone; the choice is a business decision.
- **No ENABLED Search campaigns exist** (new account) → the URL rule has
  nothing to vote with; confirm the URL with the client in writing before
  building.
- **After every import** → run the
  [`pmax-asset-automation`](../pmax-asset-automation/) audit against the
  account. The CSV bakes the automation opt-outs in; the audit is the cheap
  proof they landed — and the standing monthly check thereafter.
