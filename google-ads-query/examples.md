# Worked Examples — reading query runs

Three real decision walks (synthetic accounts). The mechanics behind every
console line are in
[`references/query-contract.md`](references/query-contract.md); the judgment
calls are [`rules.md`](rules.md).

## Example 1 — routine pull, then the analysis that waits to be asked

**Ask:** "Get search terms for Fernbrook Flats 60d."

Registry present, so the name resolves (`fernbrook flats` matches the entry's
`name` exactly). Command and output:

```
$ python scripts/query.py --account "fernbrook flats" --resource search-terms --days 60
File: data/20260723-fernbrook-flats-search-terms.csv
Rows: 4127
```

The report back is those two lines and nothing else — no sample rows, no
preview, no "here are some highlights." (Note the row count prints plain:
`4127`, no thousands separator.) 4,127 rows of raw search terms stay on disk
where they cost zero context.

**Then the user asks:** "Which terms over $50 have no conversions?"

*Now* the file gets read — and read narrowly: filter
`metrics.cost_micros > 50000000` (micros: $50 × 1,000,000) and
`metrics.conversions = 0`, return the surviving terms with costs converted to
dollars. Eleven rows come back to the conversation, not 4,127. If the ask had
been "clean these up," that's negatives work — route to
[`sqr-pipeline`](../sqr-pipeline/), which owns classification and upload.

**The habit this example encodes:** run → two lines → stop. The read happened
because a question was asked, at the narrowest slice that answers it.

## Example 2 — `Rows: 0` that isn't an empty account

**Ask:** "Get assets for Halstead Automotive Group 90d."

```
$ python scripts/query.py --account halstead --resource assets --days 90
Rows: 0 (no file written - query returned nothing; try a longer --days window)
```

The console suggests a longer window, but 90 days is already long — so before
re-running, check the contract's per-template scope table. The `assets`
template is **Performance Max only** (`asset_group_asset`, PMax channel
filter). Halstead is an auto-repair account; a quick `campaigns` pull confirms
every campaign is Search. Zero rows is the *correct* answer to a question the
account can't have data for — no file, exit 0, nothing to fix, and re-running
with `--days 180` would produce the same zero for the same reason.

What the user actually wanted was RSA asset performance — that's custom-GAQL
territory (the shipped template's grain is PMax asset groups), written against
[`gaql-query-patterns`](../gaql-query-patterns/).

**The near-miss to notice:** the same session had pulled `conversions` for
Halstead and seen 214 conversions against a 30-day campaigns pull showing 19.
Not a tracking bug — `conversions` is all-time (no date filter in that
template; `--days` is inert). The two numbers were never comparable.

## Example 3 — the ask that outgrows the templates

**Ask:** "Get campaigns for fernbrook — actually, split it by device."

First, the resolution stumble. The registry has two Fernbrook properties:

```
$ python scripts/query.py --account fernbrook --resource campaigns
ERROR: Ambiguous account 'fernbrook'. Did you mean:
  - fernbrook-flats (Fernbrook Flats)
  - fernbrook-commons (Fernbrook Commons)
```

Relay the candidates verbatim and let the user pick (never auto-pick — rules
invariant). They mean Flats.

Second, the template call. "By device" changes the *grain*: no shipped
template carries `segments.device`, and filtering after the pull can't
manufacture a segment that was never selected. This is the custom-GAQL branch
of the template-vs-custom table — write the query against
[`gaql-query-patterns`](../gaql-query-patterns/) (campaign fields +
`segments.device` + the `{DATE_RANGE}` placeholder where the date filter
goes).

The user then says they'll want this every month. Repetition is the signal to
promote it: save the query as `references/device.gaql` inside this skill —
per the ninth-template contract (no trailing `;`, add a `resources.md` row) —
and from now on it's a first-class resource:

```
$ python scripts/query.py --account "fernbrook flats" --resource device --days 30
File: data/20260723-fernbrook-flats-device.csv
Rows: 42
```

One-off narrowings filter the CSV; repeat asks become templates; different
grains start as custom GAQL. Same table, three branches, one session.
