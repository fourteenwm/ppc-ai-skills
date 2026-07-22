# Ads Checker

Audit Google Ads accounts for creative compliance across 10 checks — DKI, auto-created assets, broken URLs, ad disapprovals, stale seasonal copy, URL expansion, auto-applied recommendations, inappropriate/Fair-Housing-risk content, spelling, and irrelevance — then layer an intelligence system on top: issue-history comparison run-over-run, chronic-issue detection (3+ occurrences in 90 days), and a cached feed for a daily briefing.

**The pain point:** Creative problems are easy to miss at portfolio scale and expensive when they linger — a disapproved ad bleeds spend, a broken final URL kills conversions, an auto-applied "broad match keyword" recommendation quietly wrecks targeting, and a stale "Summer Special" runs into October. Eyeballing dozens of accounts doesn't scale, and a one-shot audit tells you *what's* wrong today but not whether it's *new*, *getting worse*, or *the same thing for the fifth week running*. This skill encodes a repeatable audit plus the memory to tell the difference — so you triage by severity AND by trend, and chronic offenders surface on their own.

---

## What's Inside

- **10 creative-compliance checks** with severity logic (CRITICAL / HIGH / MEDIUM / OK), spanning policy, automation settings, copy hygiene, and relevance
- **Operator docs, not just scripts** — `rules.md` (triage order, false-alarm classes, finding→fix-skill routing), `examples.md` (worked triage reads), and `references/check-rubric.md` (exact per-check criteria + the output contract)
- **Issue-history comparison** — every run tags each issue type NEW / INCREASED / DECREASED / RESOLVED / SAME vs the last audit
- **Chronic-issue detection** — flags accounts where an issue has recurred 3+ times in 90 days, so persistent problems escalate automatically
- **Brand-aware spelling** — account/brand names load as spelling exceptions so real property names don't false-positive
- **Fair-Housing-aware** content screening for discriminatory language alongside profanity, violence, scam, and competitor terms
- **Cached-output contract** for a daily briefing — a lightweight reader surfaces the last 24h of CRITICAL/HIGH findings without re-running the audit
- **Severity-ranked Google Sheet output** plus per-account and portfolio trend tabs
- Read-only — never mutates Google Ads

---

## Installation

```bash
mkdir -p .claude/skills/ads-checker/scripts .claude/skills/ads-checker/references
curl -o .claude/skills/ads-checker/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/ads-checker/SKILL.md
curl -o .claude/skills/ads-checker/README.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/ads-checker/README.md
curl -o .claude/skills/ads-checker/rules.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/ads-checker/rules.md
curl -o .claude/skills/ads-checker/examples.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/ads-checker/examples.md
curl -o .claude/skills/ads-checker/references/check-rubric.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/ads-checker/references/check-rubric.md
curl -o .claude/skills/ads-checker/scripts/ads_checker_audit.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/ads-checker/scripts/ads_checker_audit.py
curl -o .claude/skills/ads-checker/scripts/read_latest_ads_checker.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/ads-checker/scripts/read_latest_ads_checker.py
```

---

## The Scripts (Ship With This Skill)

Both scripts are included and self-contained — Google Ads API + Google Sheets only, credentials from your `google-ads.yaml`.

**1. [`scripts/ads_checker_audit.py`](scripts/ads_checker_audit.py)** — given `--cid <CID>`, `--cids <CID1,CID2>`, `--portfolio <name>`, or `--all` (plus `--sheet-id` for live runs, `--dry-run` to skip the write), it:

- Queries the Google Ads API for each account's RSAs, assets, campaign settings, policy summaries, and recommendation subscriptions
- Runs the 10 checks and computes an overall severity per account
- Compares each account's issue counts to its most recent prior row (history tab) and tags deltas
- Detects chronic issues (3+ occurrences / 90 days) among HIGH/CRITICAL accounts
- Writes results to a Google Sheet: a `Raw Output` detail tab, an optional per-portfolio tab, a `History` portfolio-trend tab, and an `Account History` per-account tab

**2. [`scripts/read_latest_ads_checker.py`](scripts/read_latest_ads_checker.py)** — given `--sheet-id` and `--critical-only` (optionally `--portfolio <name>`, `--hours-back N`, `--json`), it reads the **cached** `Account History` rows from the last 24h and formats CRITICAL/HIGH accounts for a daily briefing. It does not call the Google Ads API.

**Prerequisites:** `google-ads.yaml` at project root (see [google-ads-api-setup](../google-ads-api-setup/)) and `pip install google-ads gspread google-auth pyyaml requests pyspellchecker`. Optional: an `accounts.json` registry for name/portfolio resolution (schema in the script header) — portfolio names are whatever grouping labels your registry uses; without a registry, `--all` walks the MCC in your `google-ads.yaml`.

**Adaptation hooks (edit the script headers' marked sections):**

- The inappropriate-content blocklist ships with housing-vertical example sets (Fair Housing phrases, listing-aggregator competitor mentions) — swap in your vertical's compliance phrases and competitor list
- The spelling exceptions list ships with common ad abbreviations plus a real-estate example block — extend for your vertical; account/brand names are added automatically from your registry
- Chronic-issue account files are created under `./accounts/<portfolio>/<slug>.md` after an interactive prompt

**The cached-output contract (do not break):** the two scripts share a hard lockstep contract — the `Account History` tab name, the `Audit Date` format, and the column headers. Change any of them in one script and you must change the other, or the briefing section silently goes blank. The exact tab/column contract, per-check criteria, and comparison/chronic semantics live in [`references/check-rubric.md`](references/check-rubric.md).

---

## Usage

**Inline (single account or portfolio):**

> "Run ads checker for the Example portfolio"
> "Creative audit for Customer ID 1234567890"

The skill will:

1. Parse the scope into `--cid` / `--portfolio`
2. Run `scripts/ads_checker_audit.py` (piping `"no"` so the optional chronic-issue prompt never blocks)
3. Surface the severity breakdown, the changes-vs-last-run (NEW/INCREASED/RESOLVED), and any chronic accounts
4. Point you at the Google Sheet output

After the run, [`rules.md`](rules.md) drives the triage: false-alarm classes ruled out (brand-word spelling flags, current-promo seasonal hits, the unregistered-CID trap), chronic accounts escalated as process problems, and every actionable finding routed to its fix skill — each with its own review gate. [`examples.md`](examples.md) shows worked reads, including why a blank briefing section is never an all-clear.

**Parallel (multiple portfolios at once):**

```
Task(subagent_type="general-purpose",
     description="Audit Portfolio A creative",
     prompt="Use the ads-checker skill to audit the Portfolio A segment.")

Task(subagent_type="general-purpose",
     description="Audit Portfolio B creative",
     prompt="Use the ads-checker skill to audit the Portfolio B segment.")

# ...launched in a single message for parallel execution
```

---

## Output Example (Truncated)

Console summary:

```
[1/1] Auditing Example Property... CRITICAL (44 issues, 4739 AI, 1 auto-apply, 1 inappropriate, 12 spelling, 3 irrelevance)

COMPARISON TO PREVIOUS RUN
First-time audits: 0
Compared to previous: 1
INCREASED ISSUES (1 accounts):
  • Example Property: ai_assets (+14)

Detecting chronic issues...
No chronic issues detected (threshold: 3+ occurrences in 90 days)

Successfully wrote 1 rows to 'Raw Output' tab
Appended 1 account rows to 'Account History' tab
```

Daily-briefing reader (`scripts/read_latest_ads_checker.py --sheet-id YOUR_SHEET_ID --critical-only`):

```
CRITICAL CREATIVE (Fix Immediately):
  🔴 Example Property: 25 disapprovals, 1 inappropriate, 3 DKI
```

---

## License

MIT — use freely in your own brain / repo / agency.

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
