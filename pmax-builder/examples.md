# Worked Examples — PMax Builder

Three real-shaped builds. All names, CIDs, and sheet IDs are synthetic.
Console excerpts match the script's actual output format.

---

## Example 1 — Routine multifamily build (Sheets mode) with a copy-count catch

**The brief:** New PMax for Lindenmoor Flats, an apartment community in
Columbus, OH. Ad copy is in the property's "PMax Ad Copy" sheet. Two brand
videos. Multifamily property → the shipped templates are already the right
vertical; nothing to edit.

**Step 1 — source the final URL from Search, not the brief.** The brief says
"the property's site is lindenmoor.com". Rule 1 says don't trust it; the
domain vote over the account's ENABLED Search ads (query in SKILL.md Step 3)
returns:

```
  42  lindenmoorflats.com
```

One root, and it isn't the guessed one — `lindenmoor.com` would have built
the campaign against a domain Search has never used. `--final-url` will be
`https://www.lindenmoorflats.com/`.

**Step 2 — build:**

```bash
python3 .claude/skills/pmax-builder/scripts/build_pmax_csv.py \
    --campaign-name "Pmax: Lindenmoor Flats" \
    --business-name "Lindenmoor Flats" \
    --final-url "https://www.lindenmoorflats.com/" \
    --city "Columbus" --state "OH" \
    --lat 39.9612 --lon -82.9988 \
    --sheet-id "[SHEET_ID]" \
    --video-ids "aB3dEfGhIjk|Lm9oPqRsTuv" \
    --remarketing-segments "Lindenmoor Flats;All visitors (AdWords);All Users of 12345 | Lindenmoor Flats - BLP" \
    --output "data/pmax-builds/lindenmoor-flats-pmax.csv"
```

The sheet-read block prints:

```
  Ad copy from sheet [SHEET_ID]:
    Headlines: 15
    Long Headlines: 4
    Descriptions: 5
```

**Stop.** The sheet template holds 15/5/5 and the script just ingested
15/4/5. Rule 4: the counts are the verification surface. Opening the sheet:
the copywriter put the fifth long headline in **row 20** — the "short
headline" slot the script ignores by design. It looks perfectly fine in the
sheet; it silently vanishes from the build. Move it into the empty row 26,
re-run, and the block reads `Long Headlines: 5`. Summary from the clean run:

```
PMax CSV generated: data/pmax-builds/lindenmoor-flats-pmax.csv
  Campaign: Pmax: Lindenmoor Flats
  Asset Group: General
  Business: Lindenmoor Flats
  URL: https://www.lindenmoorflats.com/
  Location: Columbus, OH (40mi radius)
  Budget: $10.0/day
  Dates: 2026-08-06 to 2027-06-30
  Headlines: 15
  Long Headlines: 5
  Descriptions: 5
  Videos: 2
  Search Themes: 14
  Negative Locations: 238
  Total rows: 255 (+ header)
  Columns: 115
  Encoding: UTF-16LE with BOM
  Ad copy source: Google Sheet
```

Sanity read: dates are ~3 business days out to next June 30 (built Monday
2026-08-03 → starts Thursday); `$10.0/day` is the float rendering of the
budget default, not an error; 255 rows = campaign + asset group + 14 themes
+ location + 238 negatives. Import in Google Ads Editor, upload images manually, set the real
budget — then run the [`pmax-asset-automation`](../pmax-asset-automation/)
audit to confirm the five automation opt-outs landed.

---

## Example 2 — Different vertical (auto repair): edit templates first, manual copy, and a video URL that isn't what it looks like

**The brief:** PMax for Gearline Auto Repair in Mesa, AZ — $45/day budget,
copy supplied in the brief itself, one full video plus one YouTube *short*.

**Templates first (rule 5).** Import the stock templates unedited and this
auto shop targets apartment hunters. Before building:

- `templates/search_themes.json` → replaced with 5 generic terms ("auto
  repair near me", "brake repair", "oil change near me", "car ac repair",
  "check engine light") and 3 location-specific ones ("auto repair in
  {city}", "mechanic in {city} {state}", "{city} auto repair") — 8 themes
  total.
- `templates/audience_signals.json` → all three fields set to `""`. Google's
  renter taxonomy has no auto-repair equivalent worth forcing; remarketing
  (passed on the command line) is the only audience signal shipped.
- `campaign_settings.json` / `negative_locations.json` → untouched.

**First run** pastes the copy but forgets one flag:

```
ERROR: Provide either --sheet-id or all three of --headlines, --long-headlines, --descriptions
```

Manual mode is all-or-nothing — add `--long-headlines` and re-run:

```bash
python3 .claude/skills/pmax-builder/scripts/build_pmax_csv.py \
    --campaign-name "Pmax: Gearline Auto Repair" \
    --business-name "Gearline Auto Repair" \
    --final-url "https://www.gearlineauto.com/" \
    --city "Mesa" --state "AZ" \
    --lat 33.4152 --lon -111.8315 --radius 25 \
    --budget-daily 45.00 \
    --headlines "ASE Certified Mechanics|Same Day Auto Repair|..." \
    --long-headlines "Full Service Auto Repair Shop in Mesa|..." \
    --descriptions "Family owned auto repair.|..." \
    --video-ids "https://youtube.com/shorts/Xy7zAbCdEfg|aB3dEfGhIjk" \
    --remarketing-segments "Gearline Auto Repair;All visitors (AdWords);All Users of 12345 | Gearline - BLP" \
    --output "data/pmax-builds/gearline-auto-pmax.csv"
```

Summary (abridged — unchanged lines omitted):

```
PMax CSV generated: data/pmax-builds/gearline-auto-pmax.csv
  ...
  Location: Mesa, AZ (25.0mi radius)
  Budget: $45.0/day
  ...
  Videos: 2
  Search Themes: 8
  Negative Locations: 238
  Total rows: 249 (+ header)
  ...
```

`Search Themes: 8` and `Total rows: 249` are the edited template doing its
job, not a failure (255 − 6 removed themes).

**The trap:** `Videos: 2` counts what was *passed*, not what parsed. The
extractor recognizes `youtu.be/`, `watch?v=`, and `/embed/` URLs — a
`/shorts/` URL matches nothing and passes through **verbatim**. The rule-4
spot-check of the asset-group row finds the entire string
`https://youtube.com/shorts/Xy7zAbCdEfg` sitting in the Video ID 1 column.
Re-run with the bare 11-character ID (`Xy7zAbCdEfg`) — the console looks
identical both times; only the CSV shows the difference.

---

## Example 3 — The late-June build that ends before it starts

**The brief:** Routine build for Halstead Commons (Raleigh, NC), Sheets mode,
copy clean at 15/5/5. Run on Monday, June 29.

```
  Ad copy from sheet [SHEET_ID]:
    Headlines: 15
    Long Headlines: 5
    Descriptions: 5
PMax CSV generated: data/pmax-builds/halstead-commons-pmax.csv
  ...
  Dates: 2026-07-02 to 2026-06-30
  ...
  Total rows: 255 (+ header)
  ...
```

Every count is perfect — and the campaign is broken. The default start date
is 3 business days out (Thursday, July 2); the default end date is June 30
of the *current* fiscal year, and on June 29 that is **tomorrow**. End
before start: nothing will ever serve. The script never compares the two
dates — the `Dates:` line is the only tell, which is why rule 4 says read
the summary, not just the exit code.

Re-run with the end date the build actually intends:

```bash
    ... --end-date "2027-06-30" ...
```

```
  Dates: 2026-07-02 to 2027-06-30
```

Import proceeds normally. The trap window is roughly the last two business
days before June 30 every year; the fix is one explicit flag.
