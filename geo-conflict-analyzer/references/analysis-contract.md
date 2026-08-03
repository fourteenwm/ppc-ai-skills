# Analysis Contract — what `analyze.py` actually does

> **Source of truth:** `scripts/analyze.py`, with `prompt.md` as the
> model's entire instruction set. Every claim below is derived from those
> files; if either changes, this contract and the CHANGELOG must change
> with it. Line references point at the script.

## Row selection (`:87-123`)

- Reads `A:I` of `--input-tab` (default `Have Cost - GEO`), skips the
  header row, pads short rows to 9 cells.
- A row is **pending** only when ALL FOUR hold (`:111`): Status (col I)
  equals `waiting` case-insensitively, AND CID (col A), Query (col C),
  and GEO Names (col H) are all non-empty.
- **A Waiting row with an empty column H is skipped silently — forever.**
  No error, no result row, and its status never changes; it just never
  gets processed. If a query seems to be ignored run after run, check
  column H first.
- Selection is first-N in sheet order, capped at `--batch-size`
  (`:120-121`). One run selects at most one batch.

## Geo lists ride the rows (`:126-141`)

Column H is split on comma/semicolon/pipe, whitespace-stripped, empties
dropped (`:136-137`). The per-CID target list sent to the model comes
from **that CID's first pending row in the batch** — later rows' column H
values for the same CID are ignored (`:135`). Nothing is fetched from
Google Ads; the geo lists are exactly what the sheet says, current or
not.

## One run = one model call (`:144-157`)

The whole batch goes to OpenAI in a **single** chat-completions call:
system message = the full text of `prompt.md`, user message = a JSON
payload of queries + per-CID geo targets. Temperature 0.1, `max_tokens`
4000 — that 4,000-token **output** cap is why oversized batches truncate:
at ~30 output tokens per verdict row, batch sizes much past ~100 risk the
response cutting off mid-list, and truncated rows simply don't parse (see
Parsing). Model is `--model`, default `gpt-4o`.

## `prompt.md` is a runtime dependency (`:42-43`, `:80-84`)

Loaded fresh on every run from the skill folder root
(`SCRIPT_DIR.parent / "prompt.md"`); a missing file raises
`FileNotFoundError` before any API call. It is not documentation-about
the model's behavior — it IS the behavior: the PASS/FAIL definitions, the
specificity ladder, the **95 verdict lines** (93 worked examples; 54 PASS,
41 FAIL, counted from the file), the default-to-FAIL rule, and the required output
format all live there. Editing it changes classification on the next run;
test edits with `--dry-run` batches before trusting them.

## Parsing (`:160-177`) — silent drops, no retries

The response is scraped with a strict regex for
`["CID","Query","PASS|FAIL","geo","HIGH|MEDIUM|LOW"]` rows; if none
match, a 4-column fallback fills Confidence with `N/A` (`:171-175`).
Anything else — commentary, malformed rows, a truncated tail, a query
containing a double-quote — **vanishes without a warning**. The only
integrity signal is arithmetic: `Found N pending` vs `Parsed M results`
in the console. Dropped queries keep their Waiting status and simply
come back in the next run's batch.

## Writing (`:180-215`) — append-only, headerless, output tab must exist

- Results append after the last non-empty row of **column A** of
  `--output-tab` (`:180-187`): the script **never writes headers** — an
  empty output tab gets data starting at row 1 with no header row. Bring
  your own headers (the SKILL.md output-format columns).
- Write is `RAW` (`:211`) across columns A:E. Nothing is cleared;
  **history accumulates** run over run, and there is no run-date column —
  position is the only ordering signal.
- **The script never creates tabs.** A missing input tab fails at read
  time (before any spend); a mistyped `--output-tab` fails at *write*
  time — **after the OpenAI call has been paid for**. `--dry-run` prints
  the first 5 rows and skips the write entirely (`:196-202`), which also
  means it never validates that the output tab exists.

## The invariant that shapes the whole workflow: Status is never written

The script's only sheet write is the output-tab append (`:208-213`).
**Nothing ever updates the input tab** — processed rows stay `Waiting`.
Consequences, by construction:

1. Re-running without flipping Status re-selects the same first-N rows,
   re-spends the OpenAI call, and **appends duplicate result rows**.
2. Flipping Status on accepted rows is a manual (or upstream-pipeline)
   step of the workflow, not an optional cleanup.
3. The silver lining: parser-dropped rows retry automatically, because
   they were never marked done.

## Credentials and side effects

- `OPENAI_API_KEY` from the environment or a `.env` in the working
  directory (`load_dotenv()`, `:46-54`); missing → error before anything
  runs. `GEO_SHEET_ID` env var substitutes for `--sheet-id` (`:220-221`).
- Sheets OAuth token from `--token` (default `./token.json`), Sheets
  scope only (`:57-70`). **An expired token is refreshed AND rewritten in
  place** (`:72-75`) — `token.json` changing mtime after a run is
  expected, not tampering.
- No Google Ads API anywhere in the script — Sheets + OpenAI only.

## Console anatomy (`:239-283`)

60-char `=` banners; `Loading credentials...` with three `  ...loaded`
lines; `Reading up to N pending queries from '<tab>'...`;
`  Found N pending queries` / or the clean exit
`No pending queries found (Column I = 'Waiting').` (exit 0);
`  Across M unique accounts`; `Calling OpenAI (<model>)...`;
`  Parsed N results — PASS=x, FAIL=y`;
`  Confidence: HIGH=a, MEDIUM=b, LOW=c`; a conditional
`  [!] N LOW confidence results — consider manual review` (`:275-276`);
then the write line
`Wrote N rows to '<tab>' (rows X-Y)` or the dry-run preview, and `Done!`.
Console output is not persisted anywhere — the output tab is the only
durable record.
