# Changelog

All notable changes to this repository.

## 2026-07-23 — RSA Refresh + RSA Bulk Edit: the operator layer

The two RSA-editing skills get their judgment and contract layers, and the
three RSA skills now route to each other explicitly. Doc-only — all three
scripts byte-untouched.

**[`rsa-refresh/`](rsa-refresh/):**

- NEW `references/refresh-contract.md` — the exact mechanics sourced from
  both scripts: selection scope, the context/copy JSON formats (including
  the `headlines_needed` math), merge gates (customizer-only mechanical
  preservation, 30/90 length skips, silent dedupe, the below-10-headlines
  skip that drops an ad from both tabs), the append-default sheet contract
  with both tabs' real column layouts, the baseline contract (including
  why a standalone run always writes zero asset counts), the scrape
  ladder and its fork by mode, and the enrichment gating — including that
  the SERP hook needs city/state the compliance module supplies, and that
  [`rsa-single-account`](rsa-single-account/) ships importable SERP
  modules. Also states plainly that the in-script filter helpers are
  scaffolding the shipped flow never invokes — the reference files are
  what governs copy quality.
- NEW `rules.md` — the judgment layer: the refresh-vs-rebuild call (per ad
  group, from the label spread), reading the baseline (the standalone-zeros
  and all-N/A misreads), the Stage-2 compliance chain, an 8-row
  false-alarm table (all-`NO_DATA` labels = failed query, error rows on a
  resume-time scrape failure, doubled append rows, the wrong-site scrape),
  and the escalation default (empty slot / held-back ad group, never
  improvised copy).
- NEW `examples.md` — three worked reads: a surgical refresh, the
  prepare-mode scrape trap (context JSON written anyway — the near-miss is
  generating from vibes), and the standalone-baseline zeros misread.
- The three existing references now carry source-of-truth headers — the
  headline and description standards note that Stage 1 embeds them
  verbatim into the context JSON (edits change what Stage 2 sees), and the
  hallucination filter notes it is loaded from the folder, not embedded.
  The stale output-format table formerly in `hallucination-filter.md`
  (missing the validation columns, wrong Original-tab layout) is replaced
  by the contract's code-accurate version.
- `SKILL.md` re-homed to workflow + routing: does-NOT-do boundary (no
  mutations, no autonomous copy, customizers are the only mechanical
  preservation), files map, and when-to-load routing across the RSA family
  plus [`ad-copy-verification-standard`](ad-copy-verification-standard/) and
  [`ad-copy-generation-framework`](ad-copy-generation-framework/). README
  install block fetches the full doc layer; the "preserving BEST and GOOD"
  phrasing now says how they actually survive (Stage 2 re-includes them).

**[`rsa-bulk-edit/`](rsa-bulk-edit/):**

- NEW `references/edit-contract.md` — match semantics from the code
  (literal substring, no word boundaries, replacement inserted exactly as
  typed, backslash caveat), the searched-fields truth (headlines and
  descriptions only — paths ride along unedited), per-account error
  isolation, the clear-and-rewrite sheet contract, run modes, and the
  Editor-paste contract (columns C→Z carry no account or ad identity).
- NEW `rules.md` — when bulk is the WRONG tool (five routed cases), the
  pre-flight (dry-run, substring audit, casing plan, customizer intent),
  the pre-paste review checklist (length audit — the script writes
  over-limit text unflagged; casing scan; collateral read; per-account
  paste), false alarms, escalation default.
- NEW `examples.md` — a rebrand with the checklist catching a 37-char
  headline and a casing artifact, the substring-collateral read
  (`Care` → `Carefree`), and the ask that isn't bulk work (inserting a
  new claim) next to the customizer retirement that is.
- `SKILL.md` re-homed to workflow + routing with boundary and files map;
  placeholder CIDs normalized to the 10-digit convention. README's claim
  that paths are searched corrected (they never were — the code carries
  them through untouched); root README's "approval and rollback safety"
  wording replaced with what the tool actually does.

**Cross-wiring:** [`rsa-single-account/`](rsa-single-account/) SKILL.md
gains a three-line "Which RSA skill?" block, so each of the three RSA
skills now states when to load the other two — full-set-from-scratch vs
label-guided refresh vs literal swap.

## 2026-07-23 — SQR Pipeline: two one-line doc fixes

From re-deriving every SKILL.md claim against the seven shipped scripts.
Doc-only — all scripts byte-untouched.

- [`sqr-pipeline/SKILL.md`](sqr-pipeline/SKILL.md) — the step-1 row now
  describes what `sqr_prep.py` actually does: it batches every pending query
  and bundles the account brand names + the competitor keyword stub into each
  batch for the classifier (prep itself flags nothing — classification is
  step 2's job).
- [`sqr-pipeline/SKILL.md`](sqr-pipeline/SKILL.md) — the remove branch
  (step 7) now says where removal candidates come from: a blocked-positive
  conflict scan via [`neg-conflict-finder`](neg-conflict-finder/), or a
  performance drop.

## 2026-07-23 — Doc-accuracy pass: budget-guardian and ads-checker

Five one-line corrections from re-deriving doc claims against the code they
describe. Doc-only — every workflow and script is byte-untouched.

- [`budget-guardian/references/alert-contract.md`](budget-guardian/references/alert-contract.md)
  — the Sheets retry waits are 2/4/8s (the fourth failed attempt raises
  without sleeping; the doc said 2/4/8/16s), and a missing `Guardian Config`
  tab crashes loud to a Script Error alert rather than reading as DISABLED
  (empty cells and typos still fail closed).
- [`budget-guardian/SKILL.md`](budget-guardian/SKILL.md) — the
  production-twin parity line no longer claims the twin's cron cadence;
  cadence is outside the parity set. (Every reference to this bundle's own
  2-hour cron is unchanged and correct.)
- [`ads-checker/examples.md`](ads-checker/examples.md) — example 1's first
  console line now shows the format the engine actually prints
  (`CRITICAL (6 issues)` — DKI, disapproval, and seasonal counts never
  appear as suffix extras); the per-check breakdown moved into the prose.
- [`ads-checker/references/check-rubric.md`](ads-checker/references/check-rubric.md)
  — the spelling check's "no brand shield" note is scoped to registry-less
  `--cid`/`--cids` runs; a registry-less `--all` walk builds the shield
  from the walked account names.

## 2026-07-22 — Ads Checker: the operator layer and the check rubric

[`ads-checker/`](ads-checker/) shipped as a rich procedural wrapper with the
stable reference material carried inline. This pass re-homes that payload
and adds the judgment layer — doc-only, both scripts byte-untouched.

- NEW `references/check-rubric.md` — exact per-check criteria sourced from
  the engine: what fires each of the checks and at what severity, the
  10-checks-vs-11-functions precision (the auto-created-assets *setting*
  check feeds severity but has no history column — it's a setting state,
  not an issue volume), the severity-by-matched-term nuance on the
  inappropriate check (spam-category matches count but never move
  severity), the 20-URL sampling on URL validation, and the full
  cached-output contract both scripts share — tabs, columns, date format,
  comparison and chronic semantics (including that comparison history is
  scope-bound while chronic detection is not).
- NEW `rules.md` — the judgment layer: invariants (the audit Sheet is the
  instrument's memory; severity ranks urgency class while count ranks
  effort), a triage order (CRITICAL by exposure → chronic → NEW/INCREASED →
  structural HIGH → copy HIGH), how to read the history tags (RESOLVED
  means verify fixed-vs-vanished), an 11-row false-alarm table mined from
  the engine (brand/coined-word spelling flags, current-promo seasonal
  hits, HEAD-blocking servers, whole-library asset scans, the
  unregistered-CID BRAND_MISSING trap, blank briefing = stale never
  all-clear), chronic reasoning (3+/90d means the fix isn't sticking —
  find the source), and a finding→fix-skill routing table.
- NEW `examples.md` — three worked reads: a portfolio run with a chronic
  disapproval tag, the spurious HIGH on an unregistered account (the fix
  was configuration, not copy), and a blank briefing section almost
  reported as "clean this week" (a `--dry-run` writes no history).
- SKILL.md re-homed to workflow + routing: the checks list, severity
  table, and contract column list moved to their owning files; gained an
  explicit does-NOT-do boundary, a finding→sibling routing table, and a
  files-in-this-skill map.
- README: install block fetches the new anatomy files, What's-Inside names
  the operator docs, the contract paragraph points at the rubric instead
  of restating it, and a triage pointer covers the false-alarm classes.

## 2026-07-22 — Shared Budget Updater: the operator layer and the write contract

[`shared-budget-updater/`](shared-budget-updater/) already shipped its
invariants, a triage table, worked examples, and workflow diagrams. What
was missing was the judgment an operator needs around a tool that *changes
live budgets*: whether a failed row is safe to run again, what number
belongs in a row in the first place, and how to work the daily window.

- `rules.md` grew a sharpened invariant (**there is no sanity-check layer**
  — the workflow writes the row's number absolutely, so the approval gate
  is the entire defense) and three judgment sections: **the shared-budget
  math** (column C is the *daily* amount; monthly ÷ 30.4; the pairing
  interlock — pushing a daily budget without updating the Guardian's
  monthly tab makes its next alert more likely, and correct),
  **safe-rerun reasoning** (absolute overwrites make reruns benign;
  crash-mid-run recovery, stale pending rows, clearing an `x`, duplicate
  rows, pending-edit = new approval), and **cadence** (the daily latency is
  a review window; when manual dispatch is legitimate; no draft state).
  The triage table gained an account-level policy-block row.
- NEW `references/update-contract.md` — the exact write contract sourced
  from the code: the mutation surface (amount-only, blind overwrite,
  dollars→micros), row lifecycle (batch-mark-after-loop and what a
  mid-run crash leaves behind), the ingestion ladder (which skips are
  silent, and why a malformed amount alerts instead), the consolidated
  alert shape, the error taxonomy and both retry envelopes, how to read
  run state cold from the tab + Actions log, the env-var table, and the
  production-twins parity set. SKILL.md hands those facts over and keeps
  workflow + routing.
- SKILL.md now routes what triage surfaces:
  [`google-ads-query`](google-ads-query/) for read-only ID verification,
  [`budget-recommendation-calculator`](budget-recommendation-calculator/)
  for sizing, [`portfolio-pacing-rules`](portfolio-pacing-rules/) for pace
  context, [`change-history-checker`](change-history-checker/) for
  Ads-side receipts, [`budget-guardian`](budget-guardian/) as the tripwire
  pairing — plus a new "Production twins & behavior parity" section.
  `rules.md` and `examples.md` wire the same routes inline.
- README: install file list names the doc layer explicitly; the triage
  pointer now covers the judgment sections and the contract.
  `sheet-template.md` states that column C is the daily amount.
- Two code changes, each deliberately ported from the production twins
  after hunk-by-hunk review: `workflows/_shared/sheets_retry.py` now also
  retries HTTP 429 rate-limit errors and takes 4 attempts (matching
  budget-guardian's copy — the two bundles' `_shared/` helpers are
  identical again), and the Slack alert gained a remediation-hint line via
  the new `workflows/_shared/mutate_error_hints.py` — known account-level
  policy blocks (currently the EU political advertising declaration)
  arrive with the fix attached instead of a bare error code. Generic
  hardening on both; all other workflow code byte-untouched.

## 2026-07-22 — Budget Guardian: the operator layer

[`budget-guardian/`](budget-guardian/) already shipped its invariants, a
triage table, and worked examples. What was missing was the judgment an
operator needs *around* the alerts: when a correct alert is still the wrong
signal, which knob to reach for when tuning, what the kill switch is
actually for, and what the direct-CID roster model implies for coverage.

- `rules.md` grew four sections: a **false-alarm classes** table (mid-month
  budget edits, month-boundary resets, Google overdelivery vs. the sheet
  number, small-denominator early-month trips, and the
  several-accounts-at-once → suspect-the-budget-source-first rule),
  **threshold tuning** (the per-account knob is the `Budgets` tab; the two
  constants in `main.py` are global posture — and the alert labels don't
  follow them), **kill-switch guidance** (legitimate flips, the
  disabled-runs-exit-green trap, per-account alternatives from scalpel to
  hammer), and **the `Budgets` tab is the roster** (new accounts are
  invisible until added; blank budget = deliberate unwatch; coverage diffs
  are an operator duty).
- NEW `references/alert-contract.md` — the exact run contract sourced from
  the code: threshold math (including the if/elif detail that an account
  jumping straight past 120% never gets its 100% warning that month), the
  three alert shapes, state/dedupe semantics, the Budgets-tab parse ladder
  (which skips log and which are silent), kill-switch read semantics, the
  failure contract, how to read run state cold, the env-var table, and the
  production-twin parity set. SKILL.md hands those facts over and keeps
  workflow + routing.
- SKILL.md now routes what triage surfaces:
  [`change-history-checker`](change-history-checker/) and
  [`mcc-hack-audit`](mcc-hack-audit/) on the 120% incident path,
  [`budget-recommendation-calculator`](budget-recommendation-calculator/)
  for budget-sizing questions,
  [`portfolio-pacing-rules`](portfolio-pacing-rules/) for pace context,
  [`shared-budget-updater`](shared-budget-updater/) as the execution arm.
  The rules.md triage table and examples wire the same routes inline.
- README: install file list names the doc layer explicitly; new "Triaging
  an alert" pointer under Operations.
- One code change, deliberately ported from the production twin after
  hunk-by-hunk review: `workflows/_shared/sheets_retry.py` now also retries
  HTTP 429 rate-limit errors (new `_is_transient()` helper) and takes 4
  attempts with 2/4/8/16s backoff instead of 3. Generic hardening, no
  identity-bearing content. All other workflow code byte-untouched.

## 2026-07-22 — Non-Serving Keyword Scanner: the judgment layer

[`non-serving-keyword-scanner/`](non-serving-keyword-scanner/) shipped a
scan with thin reading guidance — "decide pause/keep/investigate" and little
else. The interesting failure mode of a zero-impression report is misreading
it: bulk-pausing seasonal keywords that cost nothing, "cleaning up" an
account whose real problem is an outage upstream, or celebrating a row that
disappeared because Google's ~13-month low-activity auto-pause removed it
from scan scope. The skill now ships the judgment layer:

- NEW `rules.md` — when zero impressions is expected vs. actionable:
  invariants (report-only; hygiene not savings; the tab is a snapshot, not a
  log), clusters-before-rows triage, sharpened Pause/Keep/Investigate
  definitions, a false-signal table (re-enabled and newly launched
  campaigns, mid-window keyword adds, seasonal terms, low-search-volume
  suppression, inline API errors, the false recovery), and an escalation
  default.
- NEW `examples.md` — three worked reads: a routine portfolio triage, a
  whole-account cluster that turned out to be a billing outage, and a
  disappearing row misread as a win. All names and numbers synthetic.
- NEW `references/scan-contract.md` — the exact selection criteria, output
  columns, tab-write behavior, and failure contract, sourced from the
  script (and correcting the old SKILL.md's paraphrase: the query has no
  explicit keyword-type filter — `keyword_view` restricts by construction).
- SKILL.md restructured to workflow altitude: identity + operator duties
  (present → triage per rules.md → verdicts → route), an explicit
  "deliberately does NOT do" boundary, a files-in-this-skill table, and
  routing to [`account-diagnostic`](account-diagnostic/),
  [`neg-conflict-finder`](neg-conflict-finder/),
  [`impression-share-diagnostics`](impression-share-diagnostics/),
  [`google-ads-query`](google-ads-query/), and
  [`sqr-pipeline`](sqr-pipeline/). Scan mechanics moved to the reference;
  the Future Enhancements stub was dropped (a pause mode would contradict
  the report-only identity).
- README install block now fetches the three new files alongside the
  script and accounts template.

`scripts/non_serving_keyword_scan.py` is byte-identical — documentation
anatomy only.

## 2026-07-20 — Competitor Analysis v2: generic single-operator workflow

[`competitor-analysis-v2/`](competitor-analysis-v2/)'s SKILL.md was written
around an internal multi-agency profile system this catalog doesn't ship — a
profile-lock requirement, agency/portfolio machinery gating the phases and the
QA checklist, and references to two skills that don't exist here. The README
already described the real workflow; SKILL.md now matches it: one operator,
their own client, their own competitor site list, no profile ceremony, and no
Google Ads credentials required (competitor ads for the optional scoring phase
come from a SERP tool or are pasted in — the analysis itself runs on Playwright
plus web fetches).

- Cross-references now point at real catalog siblings:
  [`ad-copy-generation-framework`](ad-copy-generation-framework/),
  [`rsa-single-account`](rsa-single-account/),
  [`fair-housing-compliance`](fair-housing-compliance/), and the
  [`ad-copy-verification-standard`](ad-copy-verification-standard/) the
  workflow enforces.
- `sales/pricing-guide.md` removed — an internal business document, never part
  of the analysis workflow.
- Leftover internal agency/portfolio labels in the prompts, templates, and
  sales copy were genericized (analysis content unchanged; the screenshot
  script is byte-identical).
- The README install block now fetches the full skill folder — screenshot
  script, all 7 prompts, all 3 templates — instead of SKILL.md alone, so the
  workflow's file references resolve after install.

## 2026-07-17 — Google Ads API Setup: one token now covers Sheets too

[`google-ads-api-setup/`](google-ads-api-setup/)'s `generate_credentials.py`
now requests three scopes by default — `adwords` + `spreadsheets` +
`drive.readonly` (previously `adwords` only). Why: this catalog's house
pattern reuses the `google-ads.yaml` refresh token for Google Sheets output —
non-serving-keyword-scanner, ads-checker, rsa-refresh, rsa-single-account,
sqr-pipeline, and others all authenticate their Sheets writes with that same
token. A token minted with only the Ads scope passes the connection test,
then 403s at exactly the Sheets step of those skills. Scopes are fixed at
consent time, so the generator now grants everything the catalog needs up
front.

- **Already set up?** If your refresh token predates this change, re-run the
  generator once (`python generate_credentials.py --client-secrets
  client_secret.json`) and paste the new `refresh_token` into your
  `google-ads.yaml`. Nothing else changes — `test_connection.py` and every
  Ads-only skill behave identically with the wider token.
- The generator now also survives Google's granular-consent screen (a partial
  grant no longer crashes the flow) and warns when any requested permission
  was left unticked. SKILL.md + README document the token's coverage, the
  re-run note, and a new Sheets-403 troubleshooting entry.
- [`mcc-hack-audit/`](mcc-hack-audit/) (drive-by): its optional Sheets upload
  now documents its auth path — `gspread.service_account()` reading a
  service-account JSON from gspread's default location, or adapt the upload
  to the yaml-reuse pattern — and its Prerequisites gain the standard
  [`google-ads-api-setup`](google-ads-api-setup/) pointer.

## 2026-07-10 — Release: RSA Single-Account ships its scripts

[`rsa-single-account/`](rsa-single-account/) is no longer bring-your-own-script —
all seven workflow scripts are now included under `rsa-single-account/scripts/`,
one per pipeline step:

- **`check_active_accounts.py`** (Step 1) — accounts with spend this month for
  name→CID resolution; optional `accounts.json` registry (ads-checker schema),
  MCC walk via your `google-ads.yaml` otherwise; `--name` filter, `--exclude`
- **`get_account_website_url.py`** (Step 2) — the documented stdin-CID pipe
  contract (`echo "<CID>" | ...`) preserved exactly; three-pass URL hunt ending
  in a most-common-domain vote across ENABLED ad final URLs
- **`analyze_competitors_for_rsa.py`** (Step 3) — SERP competitor-messaging
  analysis with USP saturation + gap detection; `SERP_API_KEY` env var;
  `vertical_configs.json` ships alongside with three labeled **example**
  vertical keyword sets (auto_repair, plumbing, property_management) —
  `--vertical` accepts any key you add
- **`get_search_campaign_structure.py`** (Step 4) — active Search campaigns +
  ad groups; the documented "campaign name contains 'Search'" production-safety
  filter kept as written
- **`scrape_website_firecrawl.py`** (Step 5) — Firecrawl scrape (homepage +
  services/about) with LLM structured extraction of verified business facts;
  `FIRECRAWL_API_KEY` + `ANTHROPIC_API_KEY` env vars; `--output` caches the
  extraction for reuse across ad groups
- **`get_gmb_reviews.py`** (Step 6) — GBP review fallback via SERP local
  results, with the 4.5★ rating threshold and ≤30-char social-proof headline
  formatting; `SERP_API_KEY` env var
- **`write_rsa_to_sheet.py`** (Step 8) — clears + writes the import-ready RSA
  rows; `--sheet-id` (bare ID or URL); Sheets auth from a `token-sheets.json`
  if present, else OAuth reuse from `google-ads.yaml`

All scripts are read-only on Google Ads. SKILL.md and the skill README are
updated for the shipped scripts (new Prerequisites section →
google-ads-api-setup; the per-step data contracts now double as adaptation
docs for swapping in your own SERP provider or scraper). BYO-script skills:
1 → 0 — every script-driven skill in the repo now ships its scripts.

## 2026-07-10 — Google Ads API Setup: the 7-day token fix + diagrams

[`google-ads-api-setup/`](google-ads-api-setup/) rewritten around the #1
real-world failure this guide previously baked in: an External OAuth app
left in "Testing" status gets refresh tokens Google expires after **7
days** — setup works, then dies a week later with `invalid_grant`, on
repeat. Step 3 is now a real Internal-vs-External fork, and the External
branch ends with **Publish App → In production** so the token you generate
never expires.

- **README:** new "Before You Start" (same-Google-account rule) and
  "Mental Model" (the five questions your yaml answers) sections; a ✅
  check line after every step; Desktop-app-not-Web warning at OAuth client
  creation (`redirect_uri_mismatch`); Google Ads path updated to the
  current **Admin → API Center** UI (old wrench path kept as a
  parenthetical, direct `/aw/apicenter` link added); troubleshooting grows
  entries for `redirect_uri_mismatch`, `DEVELOPER_TOKEN_PROHIBITED`,
  wrong-account/incognito, lost `client_secret.json`, and start-over.
- **Corrected against Google's docs:** the developer-token pairing rule
  now states the documented direction — each **Cloud project** locks
  permanently to the first developer token that calls through it, not the
  token to the project. Deleting a project never strands your token; the
  `DEVELOPER_TOKEN_PROHIBITED` fix is a fresh Cloud project.
- **Scripts:** `generate_credentials.py` prints the 7-day/publish warning
  after issuing a token. `test_connection.py` validates and normalizes
  `login_customer_id` before the client library sees it (missing, dashed,
  or wrong-length IDs get a plain-English error instead of a stack trace),
  guards against an empty yaml, and its `invalid_grant` hint names the
  Testing-status cause.
- **New `diagrams/`:** a hero sequence diagram and a three-phase setup
  flowchart, embedded in the README with full alt text. Mermaid sources +
  theme included; SVGs render with native text (zero `foreignObject`), so
  they draw correctly in GitHub's sanitized `<img>` pipeline.

## 2026-07-10 — Account Diagnostic: operator docs + 42-point branding

[`account-diagnostic/`](account-diagnostic/) grows from a runnable script
into a self-contained operator folder — the docs now carry the judgment
layer, not just the run instructions:

- **`rules.md`** — what happens after the report prints: invariants
  (diagnosis only, never overrule a verdict, one account per run), triage
  order (circuit breakers → dollar REDs → structural REDs → YELLOWs), a
  false-alarm table (mid-month launches masquerading as pacing failures,
  shared-list negatives invisible to check 35, conversion lag inflating
  waste %, and more), preset selection, and a check→skill routing table
  mapping every finding to its fix or deep-dive skill.
- **`examples.md`** — three worked triage reads: dependency-ordered fixes
  on a RED account, a pacing RED correctly read as a launch artifact, and
  a "just fix everything it found" instruction declined into a routed,
  human-gated punch list.
- **`references/check-rubric.md`** — exact GREEN/YELLOW/RED criteria for
  all 44 checks, dollar-impact formulas, the auto-red circuit breakers,
  and the eight preset knobs (with guidance for rolling your own
  vertical preset).
- **SKILL.md** adds the post-run operator duties (present → triage →
  route), an explicit "what this skill deliberately does NOT do"
  boundary, and a files-in-this-skill map.
- **Branding: 42-point.** The skill now titles itself by its standard-run
  count — 42 checks (44 with the local-service preset) — matching the
  count the console header has always printed. "40-point inspection"
  survives as a trigger alias, and the README sample output switched to
  synthetic figures.

No engine changes: `scripts/run_diagnostic.py` behavior is untouched (the
docstring and argparse title strings are the only lines that moved).

## 2026-07-10 — Release: Ads Checker ships its scripts

[`ads-checker/`](ads-checker/) is no longer bring-your-own-script — both
scripts it drives are now included under `ads-checker/scripts/`.

**`ads_checker_audit.py`** — the full 10-check creative-compliance audit
with the intelligence layer intact: issue-history comparison (NEW /
INCREASED / DECREASED / RESOLVED / SAME per issue type), chronic-issue
detection (3+ occurrences in 90 days), the interactive account-file prompt
(the documented `echo "no" |` stdin contract is preserved exactly), and the
severity-ranked Sheet output (`Raw Output`, optional per-portfolio tab,
`History`, `Account History`). Scope comes from the standard CLI —
`--cid`, `--cids`, `--portfolio <name>` against an `accounts.json` registry
with user-defined portfolio labels, or `--all` (walks your MCC when no
registry exists). Output goes to `--sheet-id`; credentials load from
`--config google-ads.yaml`. The inappropriate-content blocklist and
spelling-exception list ship as labeled starter sets (housing-vertical
examples included) with brand terms auto-derived from your registry.

**`read_latest_ads_checker.py`** — the companion daily-briefing reader,
satisfying the documented cached-output contract as written: reads the
`Account History` tab, filters `Audit Date` (`%Y-%m-%d %H:%M`) to the last
24 hours, `--critical-only` / `--portfolio` / `--hours-back` / `--json`.
Never calls the Google Ads API.

SKILL.md and the skill README are updated for the shipped scripts
(Prerequisites → google-ads-api-setup; the data-contract section now doubles
as adaptation docs for custom registries, blocklists, and briefing wiring).
BYO-script skills: 2 → 1 (rsa-single-account ships next).

## 2026-07-09 — Fixed: DGen Automation Disable (API v23)

[`dgen-automation-disable/`](dgen-automation-disable/)'s
`fix_dgen_ad_automation.py` — Google Ads API v23 renamed
`campaign.end_date` to `campaign.end_date_time`; both GAQL queries (the
needs-fix scan and the `--verify` re-query) were erroring server-side with
`Unrecognized field`. Field updated in both; behavior unchanged (ended
campaigns are still excluded). If you're pinned to an older API version via
your own `google-ads.yaml`, the previous field name still works there — this
tracks the current library default.

## 2026-07-09 — Release: repo polish, Start Here diagrams, underspend script inlined

Three-part release readying the repo for a wider audience.

**Underspending Investigation now ships its script.**
[`underspending-investigation/`](underspending-investigation/) gains
`scripts/investigate_underspend.py` — the universal investigation script the
skill's protocol runs (7-day spend analysis, impression share root-cause
readout, month-to-date pacing). Self-contained and read-only: Google Ads API
only, invoked by `--cid` or account name (resolved via an `accounts.md`
registry or an MCC walk), `--config google-ads.yaml`, and `--monthly-budget`
to pace against the contracted budget instead of the daily-budget estimate.
Impression share metrics are converted to percentages so the threshold
readouts fire correctly, and Pmax campaigns are flagged instead of being run
through the Search decision tree. SKILL.md and README updated for the shipped
script; the Script Contract section now documents adaptation hooks (pacing
dashboards, optimization logs, custom registries). BYO-script skills: 3 → 2
(ads-checker and rsa-single-account ship next release).

**Workflow diagrams for all five Start Here skills.**
Each Start Here skill — [`mutation-safety/`](mutation-safety/),
[`ad-copy-verification-standard/`](ad-copy-verification-standard/),
[`investigation-methodology/`](investigation-methodology/),
[`non-serving-keyword-scanner/`](non-serving-keyword-scanner/), and
[`portfolio-health-prioritization/`](portfolio-health-prioritization/) — gains
a `diagrams/` folder: workflow-hero and run-logic diagrams as Mermaid source
with rendered SVGs, embedded in each skill README with descriptive alt text.
The mutation-safety hero is also embedded in the root README under the Start
Here table.

**Repo polish.**
SKILL.md frontmatter normalized across the catalog;
[`client-communication-standards/`](client-communication-standards/) now ships
its client summary template (the repo's one broken reference, fixed); the root
README gains a git-clone install path (curl fetches SKILL.md only —
tool-backed skills also ship `scripts/`), interim notes on the two skills
whose scripts ship next release, and a "How This Repo Fits a Larger System"
section. GitHub repo metadata filled in (homepage + topics).

## 2026-07-09 — New: Account Diagnostic

[`account-diagnostic/`](account-diagnostic/) — 40-point account inspection
(up to 44 checks with preset extras). Discrete GREEN/YELLOW/RED checks across
14 categories, scored into one overall verdict with estimated monthly waste.
Includes two checks most audits miss entirely: PMAX **video enhancement**
automation (fetched by many tools, read by few) and Demand Gen **ad-level**
asset automation (`ad_group_ad.ad_group_ad_asset_automation_settings` —
invisible to campaign-scoped scans; five settings, most defaulting ON).
Two vertical presets (`property-management`, `local-service`). Read-only;
console + CSV output, optional color-coded Google Sheet tab via `--sheet-id`.
Pairs with [`dgen-automation-disable/`](dgen-automation-disable/) to fix what
check 44 flags.

## 2026-07-09 — Retired: Account Audit

`account-audit/` removed — superseded by
[`account-diagnostic/`](account-diagnostic/). The 13-section narrative audit
overlapped it on conversion health, pacing, impression share, QS, and
search-term waste, while the diagnostic adds the config domains the audit
skipped (account settings, PMAX/DGen automation detail, placement safety,
extensions, negative conflicts) and replaces narrative sections with discrete
scored checks. Root README row repointed. Skill count stays 42 (one retired,
one added).

## 2026-07-06 — Updated: Conversion Tracking Health

[`conversion-tracking-health/`](conversion-tracking-health/)'s
`last_conversion_dates_by_action.py` refreshed from the maintained version.
The report now shows the included-vs-observation marker (`(in)`/`(obs)`) on
every action in the health categories — a stale action that feeds Smart
Bidding is a different severity than an observation-only one — adds an
"Actions with Recent Data" summary count, upgrades the closing summary to
priority-tiered recommendations (HIGH: stale + enabled-but-silent actions;
MEDIUM: declining actions to monitor), and suggests widening `--days` when
the lookback comes back empty. No query or CLI changes.

## 2026-07-06 — Retired: Offbrand Analyzer

`offbrand-analyzer/` removed — superseded by
[`sqr-pipeline/`](sqr-pipeline/), which carries query intent classification
(3-run consensus) plus the review gate and two-step upload end-to-end.
[`sqr-classifier/`](sqr-classifier/) remains the zero-setup paste-and-classify
option, and [`geo-conflict-analyzer/`](geo-conflict-analyzer/) still runs its
geo check standalone (cross-references repointed). Skill count: 43 → 42.

## 2026-07-06 — Maintenance: Example CIDs standardized

[`geo-conflict-analyzer/`](geo-conflict-analyzer/) and
[`offbrand-analyzer/`](offbrand-analyzer/) prompt examples now use the
universal `123-456-7890` placeholder CID throughout (13 occurrences),
matching the placeholder convention used across the rest of the repo.
No behavioral changes.

## 2026-07-02 — Updated: Budget Guardian

[`budget-guardian/`](budget-guardian/) gains its judgment layer — `rules.md`
(invariants + a triage table for 100%/120% alerts, script errors, and the
"silence ≠ healthy" checklist) and `examples.md` (worked decisions, including
declining the "just lower the budget" request — the Guardian never touches
budgets). SKILL.md now documents the behavior-parity rule with the production
twin: thresholds, kill switch, dedupe/state, and alert shape stay synced;
ingestion is deliberately different (direct-CID Budgets tab here vs label-driven
account discovery in production). Cross-links
[`shared-budget-updater/`](shared-budget-updater/) — the execution arm to this
tripwire. No code changes — the deployed workflow is untouched.

## 2026-07-01 — Added: Shared Budget Updater

New deployable automation: [`shared-budget-updater/`](shared-budget-updater/) —
a sheet-driven daily budget pusher. Approve a change by adding a row (CID,
shared budget ID, amount) to a Google Sheet tab; a GitHub Actions cron pushes
it via `campaignBudgets:mutate` (amount only), marks the row done in column D,
and sends one consolidated Slack alert for any failed rows. Amounts ≤ $0 are
guarded and never reach the API; failed rows retry on the next run.

- Bundle shape matches Budget Guardian: `SKILL.md` + `README.md` +
  `rules.md`/`examples.md` (alert triage) + `sheet-template.md` +
  `.github/workflows/` cron + `workflows/` Python package + `_shared/` helpers.
- Cross-links [`budget-guardian/`](budget-guardian/) — this pushes the
  budgets, the Guardian is the tripwire that watches what gets spent against
  them.
- Generic replica of a production automation, sanitized per the repo's 6-gate
  audit; config-driven (`UPDATER_SHEET_ID`, `SHEET_TAB`, `SLACK_USER_MENTION`),
  zero credentials shipped.

## 2026-06-18 — Consolidated: SQR Pipeline

Merged the `sqr-3run` and `sqr-upload` skills into a single end-to-end
[`sqr-pipeline/`](sqr-pipeline/) skill: MCC search-terms pull → batch prep →
3-run consensus classification → optional geo conflict check → human review →
two-step negative upload, plus a remove branch to un-negate mistakes.

- Retired `sqr-3run/` and `sqr-upload/` — their scripts (`sqr_prep.py`,
  `sqr_compare.py`, `sqr_upload_negatives.py`) now live in `sqr-pipeline/scripts/`,
  alongside newly added pull, geo-batch, n-gram, and remove scripts.
- `sqr-classifier/` (zero-setup paste-and-classify) is unchanged.
- Cross-references in `offbrand-analyzer` and `geo-conflict-analyzer` repointed
  to `sqr-pipeline`.

## 2026-05-06 — Added: Neg Conflict Finder

New skill: [`neg-conflict-finder/`](neg-conflict-finder/) — a Google Ads Script that finds every place a negative keyword is silently blocking a positive across an entire MCC, at every level Google supports (ad group, campaign, account-level shared lists, MCC-level shared lists, and account-level negatives). Match-type-aware blocking detection. Read-only — outputs to a Google Sheet for review.

Derivative work based on Google's official Negative Keyword Conflict reference script (Apache 2.0). Substantial modifications:
- Ported from single-account to MCC-wide with label-based filtering
- Added MCC-level shared list support
- Fixed phrase-vs-exact blocking detection (subsequence match instead of strict equality)
- Fixed shared-list keyword-loss regression
- Added optional spend filter to skip dormant accounts

This is a Google Ads Script (JavaScript), not a Python skill — pasted directly into the MCC Scripts editor. Apache 2.0 license preserved on the script file (the rest of this repo remains MIT).

## 2026-04-27 — Initial public release

35 PPC AI skills for Google Ads, published by [Fourteen Web Media](https://fourteenwebmedia.com).

Coverage includes:

- Single-account audits and 40-point diagnostics
- Portfolio investigations (pacing, conversion health, impression share)
- RSA bulk edits and asset refresh workflows
- SQR (search query report) negative-keyword pipeline
- PMax campaign building and asset automation
- Creative compliance (Fair Housing, ad copy verification)
- GA4 cross-analysis and lead-quality pattern detection
- Mutation safety patterns with two-step approval

Each skill ships as a Claude Code-compatible `SKILL.md` (with frontmatter for auto-invocation) plus runnable Python scripts where applicable. See `README.md` for the full skill catalog.
