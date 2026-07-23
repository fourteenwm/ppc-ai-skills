# Query Contract — resolution, dates, CSV output, template scopes

> **Source of truth:** `scripts/query.py` and the eight `.gaql` files in this
> folder — the code and templates win over this document. The templates
> themselves are the authority on which fields each resource returns (open the
> `.gaql` file; its SELECT list is the answer — this contract deliberately does
> not duplicate field lists). Mirrors the shipped revision as of 2026-07-23.
> Any change to the script or a template must update this contract and the
> CHANGELOG in the same commit.

Exactly how the script resolves targets, builds queries, and writes CSVs.
Judgment about *running* queries lives in [`rules.md`](../rules.md).

## Target resolution

- `--cid`: dashes stripped, then validated as exactly 10 digits — anything else
  is `ERROR: '<value>' is not a valid customer ID (expected 10 digits, dashes
  ok)`. The registry is **never read** on a `--cid` run.
- `--account`: resolved via the registry (`--accounts`, default
  `./accounts.json`), case-insensitively, in this order:
  1. exact slug (registry key) match
  2. exact `name` match
  3. exact `aliases` entry match
  4. partial match against slugs and names — **aliases are never
     partial-matched**
- Exactly one partial match resolves; multiple raise the ambiguous error with
  up to 5 candidates; zero raise not-found with the registry's first 5 keys as
  suggestions. Both print as `ERROR: …` and exit 1 — the script never guesses.
- The registry entry's `id` goes through the same 10-digit validation at run
  time — a malformed CID in your `accounts.json` fails the run, not silently.
- `--cid` and `--account` are mutually exclusive; one is required.

## Template resolution

- Templates load from **this skill's `references/` folder** (resolved relative
  to the script's own location, not your working directory) — the templates
  travel with the skill; your credentials, registry, and output stay in the
  project you run from.
- `--resource` matches a template **by exact filename stem only**
  (`--resource search-terms` → `references/search-terms.gaql`). The alias
  vocabulary in [`resources.md`](resources.md) (`sqr`, `kw`, `geo`…) is for the
  *request-parsing step* — the agent maps your phrasing to a short name before
  building the command. The script itself performs no alias or fuzzy matching:
  `--resource sqr` fails with the available-resources list.
- Unknown resource → `ERROR: No GAQL template for resource '<name>'.` plus a
  sorted list of every `.gaql` stem present — which means a template you drop
  in is discoverable by that error message too.

## Date range

- `{DATE_RANGE}` in a template is replaced with
  `BETWEEN '<today − days>' AND '<today>'`. Both endpoints are inclusive, so
  **`--days 30` covers 31 calendar dates including today** — and today's row
  is partial-day data.
- **`conversions` is the exception: its template has no `{DATE_RANGE}`
  placeholder**, so `--days` is inert for that resource and the metrics are
  all-time totals for each conversion action. Comparing a `conversions` pull
  against a dated `campaigns` pull is an apples-to-oranges read
  (`rules.md` false-alarm table).

## Query execution

- The script appends `PARAMETERS omit_unselected_resource_names=true` to the
  query unless the template already contains `PARAMETERS` or ends with `;`.
  This is wire-payload hygiene (the API omits resource-name fields you didn't
  select); **CSV columns are unaffected either way** — they come from the
  response field mask, which is the template's SELECT list.
- Read-only by construction: the script only ever executes the template as a
  SELECT via `search_stream`. There is no mutation path.

## CSV contract

- **Columns are the SELECTed fields in dot notation, sorted alphabetically** —
  not the template's SELECT order. `ad_group.name` sorts before
  `metrics.clicks`. Nested values flatten into dotted keys.
- **Row order follows the template's ORDER BY** (cost descending for seven
  templates, conversions descending for `conversions`).
- Money fields (`metrics.cost_micros`, `metrics.average_cpc`,
  `campaign_budget.amount_micros`) are raw micros — divide by 1,000,000.
  Ratio fields (`metrics.ctr`, impression-share metrics) are 0–1 decimals.
- **Zero rows → no file is written.** The run prints
  `Rows: 0 (no file written - query returned nothing; try a longer --days
  window)` and exits 0 — an empty query is not an error.
- Success prints exactly two lines: `File: <path>` (relative to your working
  directory when possible) and `Rows: <count>` (no thousands separator).
- Default path: `data/<YYYYMMDD>-<slug>-<resource>.csv` under the **current
  working directory** (`data/` is created if missing). The slug is the
  registry key on `--account` runs, the normalized CID on `--cid` runs.
  `--output <path>` is used verbatim instead.

## Per-template scope (what each one filters, beyond the date range)

The SELECT lists live in the `.gaql` files. What earns a line here is the
scope each template imposes — these filters explain most "where did my rows
go?" moments:

| Resource | FROM | Scope filters | Sort |
|---|---|---|---|
| `search-terms` | `search_term_view` | impressions > 0 | cost desc |
| `campaigns` | `campaign` | status ≠ REMOVED — **paused campaigns included** | cost desc |
| `keywords` | `keyword_view` | criterion status ≠ REMOVED — paused keywords included | cost desc |
| `ad-groups` | `ad_group` | status ≠ REMOVED — paused ad groups included | cost desc |
| `conversions` | `conversion_action` | status = ENABLED; **no date filter — all-time totals** | conversions desc |
| `budgets` | `campaign` | **campaign status = ENABLED only** — a paused campaign's spend is invisible here | cost desc |
| `assets` | `asset_group_asset` | **Performance Max campaigns only** — zero rows on a Search-only account | cost desc |
| `geo` | `geographic_view` | impressions > 0; location column is a **numeric criterion ID**, not a place name | cost desc |

Note the `campaigns`-vs-`budgets` asymmetry: `campaigns` keeps paused
campaigns (their spend history stays visible), `budgets` drops them. "The
totals don't match between my two pulls" is usually this row.

## Error surfaces (all exit 1, all on stderr)

- Bad CID / ambiguous account / account not found → `ERROR: <detail>` with
  the suggestions described above.
- Registry missing on an `--account` run → `ERROR:` explaining both fixes
  (copy `accounts.example.json`, or pass `--cid` directly).
- Credentials missing → `ERROR: Credentials not found at <path>` plus a
  pointer to the google-ads-api-setup skill. Note the ordering: account and
  template resolution run first, so a bad resource name fails before
  credentials are ever checked.
- API failure → `ERROR: Google Ads API error:` followed by one `  - <message>`
  line per error the API returned.

## Adding a ninth template

Drop `<resource>.gaql` into this folder and it is immediately queryable as
`--resource <resource>`. The contract your file must honor:

- Use `{DATE_RANGE}` where the date filter goes (or omit it for undated
  resources — then `--days` is inert for your template, like `conversions`).
- Don't end the query with `;` — that suppresses the `PARAMETERS` append.
- Expect the CSV columns to come out alphabetized, not in your SELECT order.
- Add a row to [`resources.md`](resources.md) so the request-parsing step can
  route to it by name.

Write the query itself against [`gaql-query-patterns`](../../gaql-query-patterns/).

## Reading run state cold

The `data/` folder is the run record: filenames carry date, account slug, and
resource, so a cold session can tell what was pulled and when from a directory
listing alone. Two caveats — the date is `YYYYMMDD` only, so **a same-day
re-pull of the same account + resource overwrites silently** (pass `--output`
to keep both), and a zero-row run leaves no file at all, so absence of a CSV
means either "never ran" or "ran empty" — the console line was the only
witness to the difference.
