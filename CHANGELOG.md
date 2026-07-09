# Changelog

All notable changes to this repository.

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
