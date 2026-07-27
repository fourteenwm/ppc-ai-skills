# Build Contract — what `build_pmax_csv.py` actually does

> **Source of truth:** `scripts/build_pmax_csv.py` and the four files in
> `templates/`. Every claim below is derived from those files; if the script
> or a template changes, this contract and the CHANGELOG must change with it.
> Line references point at `scripts/build_pmax_csv.py`.

## Inputs and mode selection

- **Two ad-copy modes, one winner.** `--sheet-id` beats the manual flags: the
  script checks `--sheet-id` first and only falls to the manual path when it
  is absent (`:402-404`). Passing both means the sheet is read and the manual
  flags are silently ignored.
- **Manual mode is all-or-nothing.** It requires ALL THREE of `--headlines`,
  `--long-headlines`, `--descriptions`. Anything less prints
  `ERROR: Provide either --sheet-id or all three of --headlines, --long-headlines, --descriptions`
  and exits 1 (`:410-412`).
- **Manual mode needs no Google credentials at all.** `gspread`, `yaml`, and
  the OAuth machinery are imported inside the sheet-reading functions
  (`:142-144`, `:186`) — they are never touched unless `--sheet-id` is used.
- **`--config` is sheet-mode-only.** It points at your `google-ads.yaml`
  (default `./google-ads.yaml`; defined `:381-382`) and is consumed only by
  the sheet-read call (`:403`); nothing else in the script reads credentials.
- **Required flags:** `--campaign-name`, `--business-name`, `--final-url`,
  `--city`, `--state`, `--lat`, `--lon`, `--output`. Defaults:
  `--asset-group-name General`, `--radius 40`, `--budget-daily 10.00`
  (`:368-391`).

## The Google Sheet contract (sheet mode)

- The script reads **column A, rows 1-35, of the FIRST tab** (`:192-193`).
  Tab name is irrelevant; tab position is not.
- Row map (`:210-212`): headlines from rows **4-18**, long headlines from
  rows **22-26**, descriptions from rows **28-32**. Rows 1-3, 19-21, and 27
  are titles/section labels and are never ingested.
- **Row 20 (the "short headline" slot) is ignored by design.** Copy placed
  there vanishes from the build with no warning.
- **Blank cells are silently skipped**, whether empty or missing entirely
  (`:203-212`) — a sheet with three blank headline rows yields 12 headlines
  and the build proceeds. The only tell is the count block it prints:

  ```
    Ad copy from sheet [SHEET_ID]:
      Headlines: 12
      Long Headlines: 5
      Descriptions: 5
  ```

- **No length validation anywhere.** The 30/90/90-character limits live in
  the sheet and in Google's import rules, not in this script — an
  over-length headline flows into the CSV untouched.
- Missing credentials file: `ERROR: Credentials not found at <path>` plus an
  api-setup pointer, exit 1 (`:146-149`). A 403 from Sheets prints a
  four-line explanation (the refresh token was minted without the Sheets
  scopes — re-run the google-ads-api-setup generator) and exits 1
  (`:194-201`). Any other Sheets API error raises with a traceback.
- Scopes requested: `spreadsheets` + `drive.readonly` (`:160-163`).

## Caps and truncation (both modes)

- Headlines cap at **15**, long headlines at **5**, descriptions at **5**,
  video IDs at **15** — extras are silently dropped (`:270-286`).
- There is **no minimum check**. Zero long headlines still builds a CSV;
  Google's minimums (3 headlines / 1 long headline / 2 descriptions per
  asset group) are enforced at import/serving time, not here.

## Video ID extraction

- Recognized URL shapes (`:119-129`): `youtu.be/<id>`,
  `youtube.com/watch?v=<id>`, `youtube.com/embed/<id>`, or a bare 11-character
  ID. A `watch?v=<id>&list=...` URL resolves correctly (the ID is captured
  before the extra params).
- **Anything else passes through verbatim.** A `youtube.com/shorts/<id>` URL
  matches none of the patterns, so the ENTIRE URL string lands in the Video
  ID column. Nothing warns; spot-check the CSV.
- The summary's `Videos: N` counts the non-empty `|`-separated inputs you
  passed (`:444`), not how many extracted to valid IDs.

## Dates

- `--start-date` default: **3 business days out, skipping weekends only**
  (`:99-107`). Holidays are business days to this function — a build the day
  before a holiday gets a start date that counts the holiday.
- `--end-date` default: **June 30 of the current fiscal year** — if today is
  past June 30, next year's June 30 (`:110-116`).
- **The late-June trap:** built between roughly June 26 and June 30, the
  default start date (3 business days out) lands in July while the default
  end date is still THIS June 30 — an end date before the start date. The
  script does not compare them; the `Dates:` line in the summary is the only
  tell. Pass `--end-date` explicitly in that window.
- Both overrides are accepted verbatim — no format or ordering validation.

## Row assembly (in emission order, `:420-426`)

| # | Row type | Count | Key columns |
|---|----------|-------|-------------|
| 1 | Campaign | 1 | name, type, networks, budget, dates, the asset-automation columns (below), brand business name |
| 2 | Asset group | 1 | headlines 38-52, long headlines 53-57, descriptions 58-62, video IDs 65-79, Final URL 82, audience signals 89-93 |
| 3 | Search themes | one per theme in `templates/search_themes.json` | theme text col 106 |
| 4 | Positive location | 1 | proximity col 99, radius col 102 |
| 5 | Negative locations | one per entry in `templates/negative_locations.json` (238 shipped) | ID col 98, name col 99, `Campaign Negative` col 105 |

- With the shipped templates (8 generic + 6 location-specific themes) that is
  **255 data rows** (+ header). Edit the theme template and the row count
  moves with it — the summary's `Total rows:` line is computed, not fixed.
- **Call to action (col 63) is left blank** (`:281`) — blank is how the
  Editor import gets the "Automated" CTA default.
- The campaign row bakes the asset-automation stance from
  `templates/campaign_settings.json` (`:252-257`): Text customization,
  Final URL expansion, Image enhancement, Image generation, Landing page
  images, and Video enhancement all ship **Disabled**. Five of those six
  columns correspond to the five API settings the
  [`pmax-asset-automation`](../../pmax-asset-automation/) audit checks
  (Editor's "Landing page images" ≈ the API's image-extraction setting;
  Editor's "Image generation" is a sixth toggle outside that audit's five) —
  which is why a post-import audit is the natural closing step of a build.
- Positive location is written as a proximity target:
  `({radius}mi:{lat}:{lon})` with the radius rendered as a float — passing
  `--radius 40` emits `40.0` (`:326-327`). Miles only; there is no km switch.
- `--remarketing-segments` omitted → column 89 stays empty; the
  interest/life-event/demographic signals from
  `templates/audience_signals.json` still ship (`:291-297`).

## Templates — what the script reads, and what it ignores

- `search_themes.json`: `generic` list used verbatim; `{city}`/`{state}`
  placeholders are substituted **only in the `location_specific` list**
  (`:307-309`) — a placeholder in a `generic` entry ships as literal text.
- `audience_signals.json`: the three fields are written as-is into columns
  90/91/93. Empty strings mean "ship no signals beyond remarketing".
- `negative_locations.json`: every entry becomes a `Campaign Negative` row.
- `campaign_settings.json`: **three keys are inert** — `cta`,
  `default_budget_daily`, and `default_radius_miles` are never read by the
  script (the CTA column is hardcoded blank; the budget and radius defaults
  live in argparse, `:376-377`). Editing those three keys changes nothing;
  every other key in the file maps 1:1 onto a campaign-row column
  (`:229-258`).
- Templates load from the `templates/` directory **next to the script's
  parent folder** (`:53-54`) — the skill folder layout is load-bearing; run
  the script from anywhere, but keep `scripts/` and `templates/` siblings.

## Output file contract

- **UTF-16LE with BOM, tab-delimited, CRLF line endings** (`:349-363`) —
  the exact encoding Google Ads Editor expects from its own PMax exports.
  Do not open-and-resave in Excel before importing; re-encoding breaks it.
- Every data row is emitted at exactly **115 tab-separated fields**.
- `--output` is required; parent directories are created automatically
  (`:351`). The file is the build's ONLY artifact — the script writes
  nothing else to disk and never touches a Google Ads account.

## Console summary (emitted verbatim, `:433-451`)

```
PMax CSV generated: data/pmax-builds/<name>-pmax.csv
  Campaign: <campaign-name>
  Asset Group: <asset-group-name>
  Business: <business-name>
  URL: <final-url>
  Location: <city>, <state> (40.0mi radius)
  Budget: $10.0/day
  Dates: <start> to <end>
  Headlines: <n>
  Long Headlines: <n>
  Descriptions: <n>
  Videos: <n>
  Search Themes: <n>
  Negative Locations: 238
  Total rows: <n> (+ header)
  Columns: 115
  Encoding: UTF-16LE with BOM
  Ad copy source: Google Sheet | CLI arguments
```

Numeric quirks worth knowing so you don't misread a healthy run: the radius
and budget lines render Python floats (`40.0mi`, `$10.0/day` — not `$10.00`),
and `Ad copy source` says `Google Sheet` whenever `--sheet-id` was passed,
even though the copy itself may have had rows skipped — the count lines above
it are the real verification surface.
