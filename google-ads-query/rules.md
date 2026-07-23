# Rules — template or custom, registry or CID, and when to read the CSV

Decision logic around a mechanical instrument. The script resolves a target,
runs one shipped GAQL template, and writes a CSV; every judgment — which
template fits the question, whether a registry is worth maintaining, when the
file actually gets read — is the operator's. [`examples.md`](examples.md) has
worked reads; [`references/query-contract.md`](references/query-contract.md)
has the exact resolution/date/CSV mechanics.

## Invariants (never break these)

- **CSV-first is the point.** Raw data lands in a file; the conversation gets
  a path and a row count. Never paste query results into context, never show
  sample rows unasked — the pattern exists so a 50,000-row report costs the
  context window two lines.
- **Analysis is a separate, requested step.** Run → report path + rows → stop.
  Read the file only when the user asks a question the file answers.
- **Read-only.** The script executes SELECT templates and nothing else. Any
  "and then fix it" follow-up is a different skill's job (routing table in
  `SKILL.md`).
- **One account per run.** Portfolio sweeps are a loop of single runs, made
  deliberately — not a default behavior.
- **Never guess a CID and never invent a registry entry.** CIDs come from the
  user, their registry, or their own account records. An unresolvable account
  name is a question back to the user, not an improvisation.

## Template vs custom GAQL — the call

The eight templates answer "how is [resource] performing over [window],
ranked by spend." Match the *question*, not the keyword:

| The ask | Call | Why |
|---|---|---|
| "Which campaigns spent the most last month?" | `campaigns` template | Exactly the template's grain and sort |
| "Pull search terms for [account]" | `search-terms` template | The template IS the search query report |
| "Search terms for one specific campaign" | Template, then filter the CSV | A one-off narrowing beats a new template; the campaign name is a column |
| "Performance by device" / "by hour" / "by audience" | Custom GAQL | No shipped template carries those segments — segmenting changes the grain |
| "Keywords with QS below 5 that spent over $100" | `keywords` template, filter the CSV | The template already carries QS + cost; thresholds are a read-time filter |
| "Asset performance for Search RSAs" | Custom GAQL | The `assets` template is PMax-only by scope (contract table) |
| Same custom pull requested a second time | Save it as a ninth template | Repetition is the signal; the drop-in contract is in the contract file |

The boundary rule: **filter-after-pull for one-offs; new template for repeat
asks; custom GAQL when the grain itself is different.** Custom queries are
written against [`gaql-query-patterns`](../gaql-query-patterns/) and dropped
into `references/` per the contract's ninth-template section.

## Registry or bare CID

- **Bare `--cid` needs zero setup and is never wrong.** Default to it when the
  CID is in hand, when this is a first run, or when the skill is being used
  against an unfamiliar account list.
- **The registry pays rent when names repeat.** Managing a stable book of
  accounts by name ("pull search terms for Fernbrook") is worth the one-time
  `accounts.example.json` copy — name, aliases, and partial matching are for
  humans who think in account names, not IDs.
- **A registry of real CIDs is credentials-adjacent — keep it out of version
  control.** The shipped example file is placeholders; your `accounts.json`
  lives next to your `google-ads.yaml`, with the same handling discipline.
- Name given, no registry present → the script's error offers both fixes.
  Offer the CID route first; it needs no setup.

## Reading the CSV — when and how

- **When:** the user asks an analysis question, and not before. "Ask for
  analysis to dig in" is the standing close of a query run — the file waits.
- **First moves when reading:** row count from the run output, then headers,
  then the narrowest slice that answers the question. Pull the whole file into
  context only when it's genuinely small.
- **Column literacy** (mechanics in the contract): columns are alphabetized,
  not SELECT-ordered; money is micros (÷ 1,000,000); ratios are 0–1;
  `geo`'s location column is a numeric criterion ID needing a lookup before
  it means anything to a human.
- **Cross-pull comparisons need matching windows.** `conversions` is all-time
  (no date filter — contract), so never reconcile it against a 30-day
  `campaigns` pull and call the difference a tracking problem.

## False-alarm table

| Signal | Likely cause | Verify by | Then |
|---|---|---|---|
| `Rows: 0` on `assets` | Account has no Performance Max — the template is PMax-scoped | Campaign types in a `campaigns` pull | Not a bug; route the question to `campaigns` or custom GAQL |
| `Rows: 0` on anything | Window too short, or the template's scope filter (impressions > 0, ENABLED-only) excludes what you're after | Contract's per-template table | Longer `--days`, or custom GAQL with the filter relaxed |
| `budgets` total ≠ `campaigns` total | `budgets` drops paused campaigns; `campaigns` keeps them | Paused rows in the campaigns CSV | Expected asymmetry — read the contract table before reconciling |
| `conversions` numbers look huge | All-time totals — `--days` is inert for this resource | The template has no `{DATE_RANGE}` | Compare like-for-like or pull a dated custom query |
| `ERROR: No GAQL template for resource 'sqr'` | Aliases are request-parsing vocabulary, not script input | `resources.md` alias list | Re-run with the exact short name (`search-terms`) |
| Costs look a million times too big | Micros, unconverted | Any `_micros` column name | Divide by 1,000,000 at read time |
| Today's numbers look low | Today is included and partial | `--days` window math (contract) | Expected; exclude today when comparing full days |
| Yesterday's file vanished | Same-day re-pull overwrote it (date-only filenames) | `data/` listing | Use `--output` for keep-both runs |
| `ERROR: Ambiguous account …` | Partial match hit several registry entries | The suggestion list in the error | Relay the candidates; the user picks — never auto-pick |

## Escalation default

When resolution fails, relay the script's own suggestions and let the user
choose — never pick a candidate on their behalf and never fabricate a CID.
When a row count surprises you (zero where data should be, or double what's
expected), check the contract's per-template scope table before re-running:
most surprises are scope filters doing their documented job, and a re-run
without understanding is a wasted API call that will surprise you identically.
