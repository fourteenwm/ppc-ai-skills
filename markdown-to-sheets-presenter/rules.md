# Rules — Markdown to Sheets Presenter

Decision logic for when to present, how to structure tabs, and how to
handle themes. Script and theme mechanics live in
[`references/presentation-contract.md`](references/presentation-contract.md);
the workflow lives in [SKILL.md](SKILL.md).

## Invariants

1. **A presentation pass is not an editing pass.** Numbers, ad copy, and
   quotes land in the sheet verbatim from the markdown. Never truncate ad
   copy or description text — widen the column instead (the theme's
   description-column width exists for exactly this). If the source
   markdown is wrong, fix the source and re-present.
2. **The script only bootstraps.** One spreadsheet, one formatted header
   row, then it exits. Everything the client actually sees — tabs, data,
   colors, conditional formatting — is composed by the agent per the
   contract's division of labor. Don't tell a user "the script does that."
3. **The theme file is the single home of presentation values.** Colors,
   fonts, thresholds, and widths come from
   `templates/professional-blue-theme.json` — never from memory, never
   improvised mid-run. If a value feels wrong, the fix happens in a copy of
   the theme file, not inline.
4. **Missing data shows as "—", never blank.** An empty cell reads as "we
   forgot"; an em-dash reads as "not available." Gray out metrics that
   don't apply.
5. **Charts go below the data, never over it** (row 24 or later on a
   standard tab). A chart floating over rows is the fastest way to make a
   client miss the numbers you formatted for them.

## Presenter vs raw CSV — pick the right output

| The ask | Right output |
|---|---|
| A human will **read** it — client deliverable, exec review, monthly recap | This skill |
| A tool or person will **re-import** it — bid tools, Editor paste, further scripting | Raw CSV ([google-ads-query](../google-ads-query/) writes those natively) — formatting would just be undone |
| Recurring automated report on a schedule | Neither: that's a pipeline job; schedule the query and skip per-run hand formatting |
| Mid-analysis working data, internal only | Stay in markdown/CSV — present once, at the end, when findings are stable |
| A data dump (thousands of rows, no narrative) | CSV. Formatting adds scroll fatigue, not clarity — and you'll fight API quota for nothing |
| The skill's own output already IS a sheet ([account-diagnostic](../account-diagnostic/) with `--sheet-id`) | Use that skill's native output — don't re-present a sheet into another sheet |

## Theme judgment

- **Default: ship the professional-blue theme untouched.** It's deliberately
  vendor-neutral and reads well on white decks and projectors.
- **Client-brand request:** copy `professional-blue-theme.json`, swap the
  `header`/`subheader` colors (hex AND the rgb decimals — the API reads the
  decimals), keep everything else. One theme per client workbook; never mix
  themes across tabs.
- **Never recolor the semantic slots.** Success stays green, warning stays
  yellow/amber, alert stays red — whatever the brand palette says. A sheet
  where "good" renders in brand purple loses the only scanning convention
  every client already knows.
- **Contrast is non-negotiable:** white text needs a dark background. If
  the brand's primary is light (yellows, pastels), use it for subheaders
  and keep a dark header — don't put white on cream.

## Table-structure judgment

- **Start from SKILL.md's two standard maps** (competitive analysis /
  performance report). They fit most reports from this catalog.
- **A one-table report gets one tab.** Don't scaffold Summary/Data/Actions
  around a single 20-row table — the mapping exists for multi-section
  reports, not as a quota.
- **More than ~6 sections: merge the minor ones.** Small sections (2-4 rows
  each) collapse into `Summary` with a bold subheader row per section. Ten
  tabs of four rows each is worse than three tabs with structure.
- **Per-competitor tabs only when there are 2+ competitors.** One
  competitor's detail lives on the scores tabs.
- **Prose-only markdown (no tables) does not get fake tables.** Lay it out
  as sectioned text rows (the parse-failure fallback is the same layout),
  or push back — a memo may simply not want to be a spreadsheet (see
  examples.md, example 3).
- **Scoring tables** get the conditional-formatting treatment (thresholds
  from the theme), right-aligned numerics, and a legend row so the client
  knows what green means without asking.
- **Currency values** get the accounting format, right-aligned.
- **Percentages** get the percentage format, right-aligned.
- **Tables over 100 rows** get filtering enabled on the header row and a
  pagination note.

## False alarms

| Looks wrong | Actually |
|---|---|
| 403 on first run | The refresh token predates the Sheets scope — re-run the api-setup generator once (SETUP.md walks it) |
| Sheet isn't in the client's Drive folder | By design: Sheets-only scope, lands in Drive root, gets moved manually (contract) |
| Header color stops at column Z | The bootstrap formats A–Z only (`endColumnIndex: 26`) — the agent's own pass covers wider tables |
| Bootstrap header is 11pt but the theme says 12pt | Known one-point gap: script hardcodes its bootstrap style; agent-applied formatting follows the theme (contract) |
| Tab is named `Data`, not what the plan says | The bootstrap surface — renaming it per the tab plan is Step 3 work |
| No conditional formatting after the script ran | Correct: the script formats one header row and exits; conditional formatting is the agent's population pass |
| stdout prints "just JSON" | That's the machine surface (pipe it to `jq`); the human-readable URL is on stderr |
| Two identical sheets in Drive | Creation is never idempotent — every run makes a new file, and Drive allows duplicate names. Delete the extra |

## Escalation defaults

- **Ambiguous source structure** (markdown where section boundaries or
  table ownership aren't obvious): ask the user which sections the client
  actually needs before building tabs — don't guess and populate twice.
- **A report wider than 26 columns or deeper than ~10 tabs**: question the
  structure before presenting it. That shape usually means the analysis
  wants splitting, not formatting.
- **Brand-theme requests**: copy the theme file per the judgment above;
  never edit `professional-blue-theme.json` in place — it's the shipped
  default for every future run.
- **API quota errors mid-population**: pause and finish manually or wait it
  out (SKILL.md error table) — don't retry-loop against a quota wall.
