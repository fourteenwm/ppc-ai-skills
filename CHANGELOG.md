# Changelog

All notable changes to this repository.

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
