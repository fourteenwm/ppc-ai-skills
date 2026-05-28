# Ads Checker

Audit Google Ads accounts for creative compliance across 10 checks — DKI, auto-created assets, broken URLs, ad disapprovals, stale seasonal copy, URL expansion, auto-applied recommendations, inappropriate/Fair-Housing-risk content, spelling, and irrelevance — then layer an intelligence system on top: issue-history comparison run-over-run, chronic-issue detection (3+ occurrences in 90 days), and a cached feed for a daily briefing.

**The pain point:** Creative problems are easy to miss at portfolio scale and expensive when they linger — a disapproved ad bleeds spend, a broken final URL kills conversions, an auto-applied "broad match keyword" recommendation quietly wrecks targeting, and a stale "Summer Special" runs into October. Eyeballing dozens of accounts doesn't scale, and a one-shot audit tells you *what's* wrong today but not whether it's *new*, *getting worse*, or *the same thing for the fifth week running*. This skill encodes a repeatable audit plus the memory to tell the difference — so you triage by severity AND by trend, and chronic offenders surface on their own.

---

## What's Inside

- **10 creative-compliance checks** with severity logic (CRITICAL / HIGH / MEDIUM / OK), spanning policy, automation settings, copy hygiene, and relevance
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
mkdir -p .claude/skills/ads-checker
curl -o .claude/skills/ads-checker/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/ads-checker/SKILL.md
curl -o .claude/skills/ads-checker/README.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/ads-checker/README.md
```

---

## Script Dependency (You Provide)

This skill is docs-only — it drives two scripts you implement against your own data sources. The SKILL.md documents the data contract; adapt the scripts to your credentials, account registry, and Sheet.

**1. `ads_checker_audit.py`** — given `--cid <CID>` or `--portfolio <name>` (and `--dry-run`), it:

- Queries the Google Ads API for each account's RSAs, assets, campaign settings, policy summaries, and recommendation subscriptions
- Runs the 10 checks and computes an overall severity per account
- Compares each account's issue counts to its most recent prior row (history tab) and tags deltas
- Detects chronic issues (3+ occurrences / 90 days) among HIGH/CRITICAL accounts
- Writes results to a Google Sheet: a `Raw Output` detail tab, an optional per-portfolio tab, a `History` portfolio-trend tab, and an `Account History` per-account tab

**2. `read_latest_ads_checker.py`** — given `--critical-only` (optionally `--portfolio <name>`, `--hours-back N`, `--json`), it reads the **cached** `Account History` rows from the last 24h and formats CRITICAL/HIGH accounts for a daily briefing. It does not call the Google Ads API.

**Reference implementation hooks:**

- Google Ads API via `google-ads-python` (loads credentials from `google-ads.yaml`)
- Google Sheets via `gspread` + an OAuth credential
- A spell-check library (e.g. `pyspellchecker`) for the spelling check
- An account registry for CID ↔ name ↔ portfolio lookups (your `accounts.json` or equivalent)

**The cached-output contract (do not break):** the `Account History` tab must carry `Audit Date` (`%Y-%m-%d %H:%M`), `Portfolio`, `CID`, `Account Name`, `Overall Severity`, and the per-issue `* Count` columns. The reader filters to the last 24h on `Audit Date`. Change the tab name, date format, or headers in one script and you must change them in the other, or the briefing section silently goes blank.

A working reference implementation lives in the private brain this skill was extracted from; if you'd like a starter template to adapt, open an issue.

---

## Usage

**Inline (single account or portfolio):**

> "Run ads checker for the Example portfolio"
> "Creative audit for Customer ID 1234567890"

The skill will:

1. Parse the scope into `--cid` / `--portfolio`
2. Run `ads_checker_audit.py` (piping `"no"` so the optional chronic-issue prompt never blocks)
3. Surface the severity breakdown, the changes-vs-last-run (NEW/INCREASED/RESOLVED), and any chronic accounts
4. Point you at the Google Sheet output

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

Daily-briefing reader (`read_latest_ads_checker.py --critical-only`):

```
CRITICAL CREATIVE (Fix Immediately):
  🔴 Example Property: 25 disapprovals, 1 inappropriate, 3 DKI
```

---

## License

MIT — use freely in your own brain / repo / agency.
