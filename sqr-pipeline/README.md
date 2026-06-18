# SQR Pipeline

End-to-end search query report (SQR) negative-keyword pipeline for Google Ads —
pull search terms, classify them with 3-run consensus, review, and upload
approved negatives with two-step mutation safety.

**The pain point:** Reviewing search terms is the most time-consuming task in
PPC, and the riskiest to automate. Single-pass LLM classification is
inconsistent — run the same prompt twice and edge-case queries flip categories.
Worse, blindly negating a term can block a query you actually want to win. This
pipeline runs **3 independent classification passes**, surfaces only the queries
where 2+ runs agree, lets you optionally screen out geo conflicts, and makes you
review and approve before a single negative touches a live account. Consensus
catches the false positives; the human gate and two-step approval catch
everything else.

---

## What's Inside

- **MCC-wide pull** — one script pulls last-30-day search terms across your whole MCC into a sheet (or use your own scheduled Google Ads Script).
- **3-run consensus classification** — 3 independent Claude passes per query; only 2-of-3 / 3-of-3 agreement surfaces as a negate candidate. No external API cost.
- **Optional geo conflict check** — don't negate a query just because it names a place; verify it doesn't collide with a location you actively target.
- **Human review gate** — approved negatives are marked by a person in the sheet, never by the tool.
- **Two-step upload** — dry-run preview → deterministic approval code → execute. The code is a hash of the pending work, so a changed sheet invalidates a stale approval.
- **Remove branch** — un-negate a keyword that was added by mistake, with the same two-step safety.
- **Optional n-gram analysis** — per-account 2- and 3-word phrase frequency for spotting recurring junk across many queries.

---

## How It Works

```
Pull search terms   ──►  SQR tab (your sheet)
        │
        ▼
Prep batches        ──►  ./data/sqr-pipeline/ob_batches/
        │
        ▼
Classify x3         ──►  run1/ run2/ run3/   (3 independent Claude passes)
        │
        ▼   (optional geo conflict check)
        ▼
Consensus merge     ──►  "3-3 Agree" / "2-3 Agree" tabs   (Include? column)
        │
        ▼
Human review        ──►  mark "x" on the rows to negate
        │
        ▼
Upload (two-step)   ──►  PHRASE negatives on shared lists   (dry-run → approve → execute)
```

See `SKILL.md` for the full step-by-step orchestration and `sheet-template.md`
for the Google Sheet structure.

---

## Prerequisites

1. **Google Ads API access** — a developer token + OAuth refresh token, saved as
   `google-ads.yaml` at your project root, with `login_customer_id` set to your
   MCC. See the [`google-ads-api-setup`](../google-ads-api-setup/) skill.
2. **Google Sheets access** — a `token.json` at your project root with the
   `https://www.googleapis.com/auth/spreadsheets` scope (the same OAuth flow can
   mint it), or a `google-ads.yaml` refresh token that already includes that scope.
3. **A Google Sheet** built to `sheet-template.md` (the input, agree, and Uploader tabs).
4. **Your own competitor list** — replace `references/offbrand-keywords.txt` with
   real competitor names for your accounts (the shipped list is a fictional sample).
5. **The [`mutation-safety`](../mutation-safety/) skill** — steps 6 and 7 modify live accounts.
6. **Python 3.10+** with: `pip install google-ads google-auth google-api-python-client pyyaml`

---

## Installation

```bash
mkdir -p .claude/skills/sqr-pipeline/scripts .claude/skills/sqr-pipeline/references
BASE=https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/sqr-pipeline

for f in SKILL.md README.md sheet-template.md; do
  curl -o .claude/skills/sqr-pipeline/$f $BASE/$f
done
for f in mcc_search_query_report.py sqr_prep.py prep_geo_batches.py \
         sqr_compare.py sqr_ngram_analysis.py sqr_upload_negatives.py \
         sqr_remove_negatives.py; do
  curl -o .claude/skills/sqr-pipeline/scripts/$f $BASE/scripts/$f
done
for f in classify-prompt.md geo-prompt.md offbrand-keywords.txt; do
  curl -o .claude/skills/sqr-pipeline/references/$f $BASE/references/$f
done
```

Then start Claude Code in your project directory and say **"run SQR pipeline"**.

---

## A note on usability

"Completely usable" here means the SKILL.md + scripts run against *your* Google
Ads account and *your* Google Sheet once you've supplied credentials and built
the sheet to `sheet-template.md`. The classification step is intentionally
LLM-in-the-loop — Claude reads each batch and classifies it — so the value lives
in `SKILL.md` and `references/classify-prompt.md` as much as in the `.py` files.
You bring the sheet and the competitor list; the skill brings the workflow.

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
