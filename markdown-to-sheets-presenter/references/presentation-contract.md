# Presentation Contract — what ships as code, what the agent composes

> **Source of truth:** `scripts/create_spreadsheet.py` and
> `templates/professional-blue-theme.json`. Every claim below is derived
> from those files; if either changes, this contract and the CHANGELOG must
> change with it. Line references point at the script.

## The division of labor (read this first)

The shipped script is a **bootstrap, not a converter**. It creates one
empty, header-formatted spreadsheet and exits. Markdown parsing, tab
creation, data population, column widths, conditional formatting, charts —
none of that is shipped code. The agent composes those Sheets API calls at
run time (`values().update`, `batchUpdate` with `addSheet` /
`updateSheetProperties` / `repeatCell` / `addConditionalFormatRule` /
`updateDimensionProperties`), driven by three files:

| Surface | Owns |
|---|---|
| `SKILL.md` | The workflow: parse → tab plan → populate → format → report back |
| `rules.md` | The formatting decisions: presenter vs raw CSV, theme handling, table structure |
| `templates/professional-blue-theme.json` | Every presentation value: colors, typography, thresholds, layout |

Nothing in `scripts/` reads `templates/` — the theme file is data for the
agent, not config for the script.

## What `create_spreadsheet.py` actually does

- Creates **one spreadsheet** with **one tab titled `Data`**, first row
  frozen (`:73-85`). The `Data` tab is a starting surface — the agent
  renames it or adds tabs per the tab plan; the script itself never creates
  a second tab.
- Creation is **never idempotent**: every run makes a new spreadsheet, and
  Drive allows duplicate names. Running twice with the same name gives you
  two files.
- The sheet lands in the **Drive root of the authorized account**. The
  script requests only the `spreadsheets` scope (`:65`) and never touches
  the Drive API — that is why folder placement is a manual afterstep, by
  design (docstring `:6-9`).

### Output streams — stdout is machine-readable

- **stdout**: exactly one JSON object, `{"id", "name", "webViewLink"}`
  (`:186-188`). The internal `sheetId` is stripped before printing.
  `python create_spreadsheet.py "Name" | jq -r .id` works.
- **stderr**: all progress — `Creating spreadsheet: <name>` (`:170`) and a
  trailing `Sheet URL: <url>` (`:189`).

### Header formatting (skipped with `--no-format`)

One `batchUpdate` (`:104-145`) against the `Data` tab:

- Range: row 1 only, **columns A–Z only** (`endColumnIndex: 26`, `:115`).
  If your data is wider than 26 columns, headers from AA on are unformatted
  until the agent's own formatting pass covers them.
- Style: background `#1a73e8` as rgb(0.102, 0.451, 0.91) (`:119-123`),
  white **bold 11pt** text (`:124-131`), CENTER/MIDDLE alignment
  (`:133-134`). The `fields` mask (`:137`) limits the write to background,
  text format, and alignment — nothing else on the row is touched.
- Note the size: the bootstrap header is the script's own hardcoded 11pt;
  the theme file specifies **12pt** for headers. Formatting the agent
  applies afterward follows the theme — the one-point difference on the
  bootstrap tab is cosmetic and disappears if the agent re-formats that
  header during population.

### Credentials and errors

- Reads OAuth values (`refresh_token`, `client_id`, `client_secret`) from
  `google-ads.yaml` — path via `--config`, default `./google-ads.yaml`
  (`:162-163`).
- Missing credentials file → exit 1 with a pointer to the
  google-ads-api-setup skill (`:51-54`).
- `HttpError` whose text contains `403` or `PERMISSION_DENIED` → the
  token-predates-the-Sheets-scope message and exit 1 (`:177-183`). Any
  other `HttpError` raises a full traceback (`:184`).
- The `sheetId` returned by the create call (first sheet, default 0,
  `:92-94`) is used only to aim the header-format call.

## The theme file's contract

`templates/professional-blue-theme.json` is the **single home** of every
presentation value. `SKILL.md` and `rules.md` deliberately carry no hex
codes, no thresholds, no pixel widths — pointers only. The file holds:

| Block | Contents |
|---|---|
| `colors` | 8 semantic slots: header, subheader, two alternating row colors, border, success, warning, alert. Each carries the hex **and** a pre-converted `rgb` object in 0–1 decimals — exactly the shape the Sheets API's `userEnteredFormat.backgroundColor` wants, so the agent never converts hex by hand. |
| `typography` | Three tiers (header 12pt, subheader 11pt, data 10pt), all Arial, bold flags per tier. |
| `conditional_formatting` | Score thresholds (fraction of max ≥ 0.8 → success, ≥ 0.5 → warning, below → alert), the threat-level map (HIGH → alert, MEDIUM → warning, LOW → success), and flag text colors (check / x / warning glyphs). |
| `layout` | Row heights (header 30, data 21), minimum column width 100px, description columns 550px, freeze 1 row / 0 columns. |

Client-brand variants: **copy the file and swap values; never edit the
shipped theme in place** — the judgment calls (what may change, what must
not) live in `rules.md`.

## What is NOT in this folder

- No markdown parser. Section detection, table extraction, and scoring-data
  recognition are agent judgment per `SKILL.md` Step 2.
- No population or formatting script. Every post-bootstrap API call is
  composed per run.
- No Drive integration: no folder moves, no permission grants, no sharing.
  The operator shares the sheet and files it manually.
