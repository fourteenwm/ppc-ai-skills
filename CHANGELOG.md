# Changelog

All notable changes to this repository.

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
