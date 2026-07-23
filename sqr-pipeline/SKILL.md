---
name: sqr-pipeline
description: End-to-end search query report (SQR) negative-keyword pipeline — pull search terms across your MCC, prep classification batches, run 3 independent classification passes for consensus, (optionally) check geo conflicts, write reviewable agree tabs, then upload approved PHRASE negatives to shared lists with two-step mutation safety. Includes a remove branch to un-negate mistakes. Auto-invoke when the user says "run SQR pipeline", "classify search queries", "pull search terms", "upload negatives", "sqr uploader", "remove negative", or "un-negate keyword".
allowed-tools: [Bash, Read, Write, Task]
---

# SQR Pipeline — Negative Keyword Operator

One operator owns the search-query-report negative-keyword workflow end to end:
pull → prep → 3-run classify → (optional geo) → consensus → human review → upload,
with a maintenance branch to remove a negative that was added by mistake.

The classification step is **LLM-in-the-loop** — Claude reads each batch and
classifies it three independent times. That is the whole point: three independent
opinions per query, with consensus (3-of-3 unanimous / 2-of-3 majority) filtering
out one-off misclassifications before anything touches a live account.

This is a single generic vertical. There is no profile switching and no
account-specific branching — point it at *your* MCC, *your* Google Sheet, and
*your* competitor list (`references/offbrand-keywords.txt`) and it runs.

---

## Triggers

- `run SQR pipeline` / `classify search queries` — full forward run (enters at the right step)
- `pull search terms` / `sqr pull` — pull only (step 0), then stop
- `upload negatives` / `sqr uploader` — upload an already-reviewed sheet (step 6)
- `remove negative` / `un-negate keyword` — maintenance branch (step 7)

Entry is wherever the work is. A "pull" enters at step 0 and stops. "Upload
negatives" with a reviewed sheet enters at step 6. "Run SQR pipeline" with prep
already done enters at step 2. Read the relevant step below before running it.

---

## Step chain

| Step | Tool | What it does | Type |
|------|------|--------------|------|
| 0 Pull | `scripts/mcc_search_query_report.py` | Pull last-30-day search terms across the MCC → the `SQR` tab. (Or use your own scheduled Google Ads Script.) | script |
| 1 Prep | `scripts/sqr_prep.py` | Build classification batches from the sheet; each batch bundles the account brand names + the competitor keyword stub for the classifier. | script |
| 2 Classify | `references/classify-prompt.md` | **3 independent classification passes** over every batch (Claude Task agents). | LLM |
| 3 Geo *(optional)* | `scripts/prep_geo_batches.py` + `references/geo-prompt.md` | Re-check off-brand hits that contain a location you actively target — don't negate those. | script + LLM |
| 4 Consensus | `scripts/sqr_compare.py` (+ optional `scripts/sqr_ngram_analysis.py`) | Merge the 3 runs → `3-3 Agree` / `2-3 Agree` tabs; optional per-account n-grams. | script |
| 5 Review gate | — | **STOP.** Human marks `Include?` (col M). Loop back to step 2 on systematic misclassification. | human |
| 6 Upload | `scripts/sqr_upload_negatives.py` | **MUTATION:** dry-run preview → approval code → upload PHRASE negatives to shared lists. | script |
| 7 Remove | `scripts/sqr_remove_negatives.py` | **MAINTENANCE:** un-negate an incorrectly-negated keyword. | script |

All scripts run from your project root (where `token.json` and `google-ads.yaml`
live), e.g. `python scripts/sqr_prep.py --sheet-id YOUR_SHEET_ID`.

---

## Step 0 — Pull

```bash
# Dry-run: show which accounts would be pulled
python scripts/mcc_search_query_report.py --sheet-id YOUR_SHEET_ID --dry-run

# Fresh snapshot of all enabled accounts (recommended)
python scripts/mcc_search_query_report.py --sheet-id YOUR_SHEET_ID --clear
```

Filter with `--labels "Search,Active"` or `--cids 1234567890,...`. The MCC comes
from `login_customer_id` in `google-ads.yaml` (override with `--mcc-id`). Then
verify the input tab refreshed before prep: `python scripts/sqr_prep.py --sheet-id YOUR_SHEET_ID --dry-run`.

## Step 1 — Prep

```bash
python scripts/sqr_prep.py --sheet-id YOUR_SHEET_ID
# add --geo-tab "GEO Source" to enable the optional geo step
```

Reads the `Have Cost` tab (col I = `Waiting`), writes batches under
`./data/sqr-pipeline/` plus `manifest.json` (`status: prepared`, `num_batches`).
Verify `manifest.json` status is `prepared` and the batch-file count matches
`num_batches` before classifying.

## Step 2 — Classify (3 independent runs)

Spawn **3 Task agents** (one per run, in parallel). Each agent classifies every
batch in `./data/sqr-pipeline/ob_batches/` and writes results to
`./data/sqr-pipeline/run{R}/step1/`.

**Agent prompt template** (fill in `{RUN_NUMBER}` and `{TOTAL_BATCHES}`):

> You are processing SQR classification Run {RUN_NUMBER} of 3.
>
> **Classification prompt:** read the full prompt from `references/classify-prompt.md`.
>
> **For each batch** `ob_001.json` … `ob_{TOTAL_BATCHES:03d}.json` in
> `./data/sqr-pipeline/ob_batches/`:
> 1. Read the batch (it contains `queries`, `brand_names`, `off_brand_keywords`).
> 2. Classify each query per the prompt rules.
> 3. Write a JSON array of `{"CID","Query","Category"}` to
>    `./data/sqr-pipeline/run{RUN_NUMBER}/step1/ob_{NNN}.json`.
>
> **CRITICAL — YOU must be the classifier:**
> - Do NOT write a Python script, regex, or any deterministic code to classify.
> - YOU read each batch and classify each query with your own judgment.
> - The entire point of 3 independent runs is 3 independent LLM opinions. If you
>   codify rules into code, all 3 runs produce identical output and the consensus
>   mechanism is meaningless.
>
> Categories must be lowercase: `high intent`, `low intent`, `informational`,
> `off-brand`. Process ALL batches. If a batch errors, log it and continue.

**Completeness check (mandatory before handoff):** each run's `step1/` must have
the same number of result files as `num_batches`. If a run stalled, re-spawn an
agent for ONLY its missing batch range — never restart the whole phase.

## Step 3 — Geo conflict (optional)

Only if you ran prep with `--geo-tab` (so `geo_targets.json` is populated):

```bash
python scripts/prep_geo_batches.py
```

Then spawn 3 Task agents that read each `run{R}/step2_batches/geo_NNN.json`,
apply `references/geo-prompt.md`, and write verdicts to `run{R}/step2/geo_NNN.json`.
A geo FAIL means the query collides with a location you actively target, so it is
**excluded** from the negate list. Skip this step entirely for the core flow.

## Step 4 — Consensus

```bash
python scripts/sqr_compare.py --sheet-id YOUR_SHEET_ID
# optional per-account phrase frequency:
python scripts/sqr_ngram_analysis.py --sheet-id YOUR_SHEET_ID
```

Writes `3-3 Agree` (unanimous) and `2-3 Agree` (majority) tabs with `Include?`
(col M) left empty for review. Report the row counts as the review handoff.

## Step 5 — Review gate (STOP)

A human marks `x` in **col M (Include?)** on the agree tabs. The operator never
marks `Include?` itself. An empty Uploader tab does NOT mean failure — it means
review hasn't happened yet, or nothing was approved. Both are valid; wait. If the
human reports systematic misclassification, loop back to step 2 with their
corrections folded into the agent prompt.

## Step 6 — Upload (MUTATION)

Two-step mutation flow — see the [`mutation-safety`](../mutation-safety/) skill.
**Never skip the dry-run. Never auto-generate or auto-approve a code.**

```bash
# Step 1 — dry-run preview (prints an APPROVAL CODE, makes no changes)
python scripts/sqr_upload_negatives.py --sheet-id YOUR_SHEET_ID

# Step 2 — execute (only after a human approves the previewed code)
python scripts/sqr_upload_negatives.py --sheet-id YOUR_SHEET_ID APPROVE-XXXXXXXX
```

Present the preview, WAIT for the human to provide the approval code, then run
step 2. The code is a hash of the pending work — if the sheet changed since the
preview, the code won't match and execution is refused. On any error or
unexpected state, STOP and report; do not retry into the API.

## Step 7 — Remove (maintenance)

Un-negate a keyword added by mistake. Mistakes usually surface via a
blocked-positive conflict scan — load [`neg-conflict-finder`](../neg-conflict-finder/)
to find them — or a performance drop. Progressive discovery → preview → approve:

```bash
python scripts/sqr_remove_negatives.py --customer-id 1234567890                                  # list lists
python scripts/sqr_remove_negatives.py --customer-id 1234567890 --list-name "Brand"              # list keywords
python scripts/sqr_remove_negatives.py --customer-id 1234567890 --list-name "Brand" --keyword "apartments near me"   # preview + code
python scripts/sqr_remove_negatives.py --customer-id 1234567890 --list-name "Brand" --keyword "apartments near me" APPROVE-XXXXXXXX  # execute
```

Same two-step safety as upload. Partial keyword matches can hit multiple criteria
— read the preview, don't assume one match.

---

## Files in this skill

| File | Purpose |
|------|---------|
| `SKILL.md` | This file — orchestration for all steps |
| `README.md` | Setup guide + prerequisites |
| `sheet-template.md` | The Google Sheet tab/column spec (you build the sheet) |
| `scripts/mcc_search_query_report.py` | Step 0 — pull search terms to the SQR tab |
| `scripts/sqr_prep.py` | Step 1 — build classification batches |
| `scripts/prep_geo_batches.py` | Step 3 (optional) — build geo batches |
| `scripts/sqr_compare.py` | Step 4 — merge runs → agree tabs |
| `scripts/sqr_ngram_analysis.py` | Step 4 (optional) — per-account n-grams |
| `scripts/sqr_upload_negatives.py` | Step 6 — upload PHRASE negatives (two-step) |
| `scripts/sqr_remove_negatives.py` | Step 7 — remove a negative (two-step) |
| `references/classify-prompt.md` | Step 2 — generic classification prompt |
| `references/geo-prompt.md` | Step 3 — generic geo conflict prompt |
| `references/offbrand-keywords.txt` | Sample competitor stub — replace with your own |

Runtime data lives at `./data/sqr-pipeline/` (gitignored), never inside the skill.

---

## Prerequisites

1. **Google Ads API** — `google-ads.yaml` at project root with `login_customer_id`
   set to your MCC. See [`google-ads-api-setup`](../google-ads-api-setup/).
2. **Google Sheets** — `token.json` at project root with the spreadsheets scope
   (or a `google-ads.yaml` refresh token that includes that scope).
3. **A Google Sheet** built to `sheet-template.md` (Have Cost, SQR, agree tabs, Uploader).
4. **Your competitor list** — replace `references/offbrand-keywords.txt` with your own.
5. **Mutation safety** — review [`mutation-safety`](../mutation-safety/); steps 6 and 7 mutate live accounts.
6. `pip install google-ads google-auth google-api-python-client pyyaml`

## What this skill deliberately does NOT do

- **No auto-approval.** Every mutation requires a human to read the preview and supply the approval code.
- **No automatic negating without review.** A human marks `Include?` before anything uploads.
- **No external classification API.** Classification runs through Claude Task agents, not a paid LLM API.
- **No profile/account switching.** One MCC, one sheet, one competitor list per install.
