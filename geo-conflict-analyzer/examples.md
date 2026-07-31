# Worked Examples — Geo Conflict Analyzer

Three reads, all synthetic data (accounts and CIDs are documentation
placeholders; the geo names reuse prompt.md's own example set). Rules
referenced are in [rules.md](rules.md); mechanics in
[`references/analysis-contract.md`](references/analysis-contract.md).

---

## Example 1 — Routine batch: the FAIL that earns the skill its keep

Fifty Waiting rows across two accounts — Lindenmoor Apartments
(123-456-7891, column H: `Chula Vista, Sunnybrook, East Lake`) and
Ravenna Flats (234-567-8901, column H: `Downtown LA`).

```
============================================================
GEO Conflict Analyzer
============================================================

Loading credentials...
  OpenAI client loaded
  Google Sheets service loaded
  Prompt loaded

Reading up to 50 pending queries from 'Have Cost - GEO'...
  Found 50 pending queries
  Across 2 unique accounts

Calling OpenAI (gpt-4o)...
  Parsed 50 results — PASS=41, FAIL=9
  Confidence: HIGH=44, MEDIUM=4, LOW=2
  [!] 2 LOW confidence results — consider manual review

Writing to 'Have Cost Result - GEO'...
Wrote 50 rows to 'Have Cost Result - GEO' (rows 213-262)

============================================================
Done!
============================================================
```

Count check first (rules): Found 50, Parsed 50 — clean. Among the nine
FAILs:

```
["123-456-7891","apartments near sunnybrook","FAIL","Sunnybrook","HIGH"]
```

Upstream classification had marked that query off-brand (it converted
nothing all quarter) and queued it for negation. The FAIL catches what
that judgment missed: **Sunnybrook is an active geo ad group** — a phrase
negative built from this query would block live traffic in a targeted
area. Off the negative list it comes (invariant 1). The eight other
FAILs read the same way: fuzzy variants of active targets — prepositions,
a `chulla vista` typo, one `east lake apartment` singular.

The 41 PASS/HIGH rows go back to the upstream pipeline for upload.
**Last step, same sitting: the 50 input rows get their Status flipped** —
the script never does it (invariant 5).

---

## Example 2 — PASS/LOW: the property-name-vs-geo call

One of the two LOW rows:

```
["123-456-7891","westgate manor apartments","PASS","","LOW"]
```

The model's hedge is honest — "Westgate Manor" *could* be a neighborhood
it doesn't know, or a property's brand name (rules: the classic noise
case). PASS/LOW means manual read, mandatory, before this query reaches
an upload (rules table).

Two checks resolve it: column H for that CID has no Westgate anything —
so no active-target collision is possible. A maps/brand search shows
Westgate Manor is a competing property two miles from the client's
building. The PASS stands: negativing this query breaks no geo
targeting.

One boundary note closes it out: whether to negative a *competitor's
property name* is brand policy — some accounts deliberately keep
competitor-name traffic. This skill answered the geo question only; the
brand call rides with the upstream classification (invariant 2).

---

## Example 3 — The Tuesday duplicate and the Wednesday shortfall

**Tuesday.** Monday's batch (rows 213-262) got reviewed — but nobody
flipped Status (invariant 5). Tuesday's run reads the same 50 rows,
spends the same OpenAI call, and appends:

```
Wrote 50 rows to 'Have Cost Result - GEO' (rows 263-312)
```

The tell is arithmetic: 100 output rows for 50 input queries, and
scrolling shows duplicate CID+Query pairs — *near*-identical verdicts,
not guaranteed identical, since temperature is 0.1, not 0 (contract).
There's no run-date column to lean on; position is the only ordering.
Fix: keep the later block, delete rows 213-262, flip the input Status,
and make the flip part of the review sitting, not a separate errand.

**Wednesday.** Fresh batch, and the console under-delivers:

```
Reading up to 50 pending queries from 'Have Cost - GEO'...
  Found 50 pending queries
  Across 3 unique accounts

Calling OpenAI (gpt-4o)...
  Parsed 47 results — PASS=39, FAIL=8
  Confidence: HIGH=41, MEDIUM=5, LOW=1
```

Found 50, Parsed 47: three model rows came back malformed and the parser
dropped them silently (contract) — a small gap, so not truncation. No
hand-entry, no re-send: those three rows were never marked done, so
they're still Waiting and ride into the next batch automatically — the
one place the never-flips-status design works *for* you (contract's
silver lining). The 47 parsed rows process normally; only *their* Status
gets flipped.
