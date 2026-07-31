# Worked Examples — Markdown to Sheets Presenter

Three decisions, all synthetic data. Rules referenced are in
[rules.md](rules.md); mechanics in
[`references/presentation-contract.md`](references/presentation-contract.md).

---

## Example 1 — Competitive analysis, the standard path

**Ask:** "Make the Gearline competitive analysis presentable for tomorrow's
call."

**Source:** a markdown report on Gearline Auto Group vs two competitors
(Redline Transmission, Summit Auto Care) — executive summary, 15-attribute
strategic scoring, 7-attribute tactical flags, gap list, verified angles.

**Tab plan** (SKILL.md Step 3, competitive-analysis map): `Summary`,
`Strategic_Scores`, `Tactical_Scores`, `Gaps`, `Recommendations`, plus
`Competitor_Redline` and `Competitor_Summit` — per-competitor tabs earn
their place because there are two of them (rules: 2+ competitors).

**Bootstrap:**

```
$ python .claude/skills/markdown-to-sheets-presenter/scripts/create_spreadsheet.py "Gearline Auto Group - Competitive Analysis - 2026-07-31"
Creating spreadsheet: Gearline Auto Group - Competitive Analysis - 2026-07-31
{
  "id": "<spreadsheet-id>",
  "name": "Gearline Auto Group - Competitive Analysis - 2026-07-31",
  "webViewLink": "https://docs.google.com/spreadsheets/d/<spreadsheet-id>/edit"
}

Sheet URL: https://docs.google.com/spreadsheets/d/<spreadsheet-id>/edit
```

The JSON is stdout (parse the `id` from it); the rest is stderr progress.

**Population decisions:** the `Data` tab is renamed `Summary`; six tabs
added per the plan. Strategic scores land as written — Gearline 31/45,
Redline 27/45, Summit 22/45 — and the conditional-formatting pass colors
them from the theme's thresholds: 31/45 and 27/45 sit in the warning band
(≥50% of max), 22/45 falls below 50% into alert. A legend row under the
table says so in words. Ad copy examples in the competitor tabs are pasted
full-length with the description column at the theme's 550px — one
headline ran 87 characters and the answer was a wider column, not an
ellipsis (invariant 1).

**Report back:** the Output Format block from SKILL.md Step 6 — link, tab
list, row counts per tab.

---

## Example 2 — Performance report: merge before you scaffold

**Ask:** "Client wants the June performance review as a sheet."

**Source:** a nine-section markdown report — overview, spend pacing,
campaign table, keyword highlights, quality-score notes, search-terms
recap, competitor movement, test results, next steps.

**The judgment:** nine tabs of 3-6 rows each would be scroll fatigue
(rules: >6 sections, merge the minor ones). The map collapses to the
performance-report standard: `Dashboard` (overview + pacing + QS notes +
competitor movement as subheaded blocks), `Campaigns` (the one real data
table, plus keyword highlights), `Action_Items` (test results + next
steps).

**Formatting beats:**

- Spend column gets accounting format, right-aligned; CTR/CVR columns get
  percentage format (SKILL.md special handling).
- Two campaigns have no quality-score data — cells read `—` in gray, not
  blank (invariant 4).
- The campaign table is 31 rows: under the 100-row threshold, so no filter
  row needed.
- One chart (spend by week) goes on `Dashboard` **below** the data blocks,
  anchored at row 26 (invariant 5).

Sheet name: `Client - Performance Report - 2026-07-31` per the naming
convention — the client's actual name, not "Client", in real use.

---

## Example 3 — The asks this skill should decline

**Scene A:** "Export these 4,100 search terms to a sheet so I can paste
them into Editor later."

Re-import is the tell (rules table, row 2). Editor paste wants raw,
unformatted values — headers with fills and frozen rows add nothing and
sometimes trip a paste. That's [google-ads-query](../google-ads-query/)
CSV territory. No presenter run; the right answer is the CSV path and a
one-line explanation.

**Scene B:** "Make my Q3 strategy memo presentable."

The memo is twelve paragraphs, zero tables. Faking tables out of prose
produces a spreadsheet nobody wants to read (rules: prose-only markdown).
Two honest options, offered before any API call:

1. Keep it as a document — formatting a memo is a docs job, not a sheets
   job; or
2. If a sheet is required for filing consistency, lay it out as sectioned
   text rows — the parse-failure fallback layout — with section subheaders
   and no pretend columns.

The user picked the document. Zero sheets created; the decline IS the
deliverable. The presenter earns its keep on reports with structure — it
should say so when handed one without.
