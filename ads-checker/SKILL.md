---
name: ads-checker
description: Audit Google Ads accounts for creative compliance (10 checks) with intelligence integration (issue-history comparison, chronic-issue detection, daily-briefing integration). Auto-invoke when user says "run ads checker", "creative audit", "check ads for [portfolio]", "audit ads", or "ads checker for [account/portfolio]". Outputs to a Google Sheet with a severity breakdown. Read-only — no Google Ads mutations.
allowed-tools: [Read, Bash, Grep, Glob]
---

# Ads Checker

**Purpose:** Run comprehensive creative-compliance audits across your Google Ads portfolios, identify issues, track issue history across runs, detect chronic problems, and write prioritized findings to a Google Sheet.

**Type:** Read-only audit skill. It does not mutate Google Ads — it only reports issues and writes results to an audit Google Sheet.

---

## What This Skill Wraps

All audit logic and **all intelligence features** live in one script you provide — referred to here as `ads_checker_audit.py`. This skill is a procedural wrapper: it determines scope, runs the script, interprets the console output, and summarizes findings. **Do not reimplement the checks in the skill; the script is the single source of truth.**

A small read-only companion script, `read_latest_ads_checker.py`, is consumed by a daily briefing to surface recent CRITICAL/HIGH findings (see "Cached-Output Contract" — a HARD constraint if you wire it into a briefing).

Both scripts are environment-specific (they hold your credentials, account registry, and Sheet ID). See the README's "Script Dependency (You Provide)" for the data contract each must satisfy.

---

## The 10 Checks

### Phase 1 (Core)
1. **DKI Detection** — Dynamic Keyword Insertion in copy/assets (trademark risk) → HIGH
2. **Google AI Assets** — `AUTOMATICALLY_CREATED` assets that should be disabled → MEDIUM
3. **URL Validation** — broken/invalid destination URLs (parallel HEAD checks) → CRITICAL
4. **Ad Disapprovals** — non-approved policy statuses on ENABLED ads/ad groups/campaigns → CRITICAL (disapproved) / MEDIUM (limited)
5. **Seasonal Promotions** — outdated seasonal language in copy/assets → HIGH

### Phase 2 (Extended)
6. **Auto-Created Assets Setting** — `TEXT_ASSET_AUTOMATION` currently `OPTED_IN` on campaigns → HIGH
7. **Final URL Expansion** — `FINAL_URL_EXPANSION_TEXT_ASSET_AUTOMATION` `OPTED_IN` → MEDIUM
8. **Auto-Applied Recommendations** — enabled recommendation subscriptions (whitelist `OPTIMIZE_AD_ROTATION`; flag high-risk keyword/CPA/ROAS types) → HIGH / MEDIUM
9. **Inappropriate Content** — profanity, violence, adult, discriminatory (incl. Fair Housing), scam, competitor, spam terms → CRITICAL/HIGH by category
10. **Spelling/Grammar** — misspellings via a spell checker, with ad-copy + brand-name exceptions → HIGH (5+) / MEDIUM (1-4)
11. **Irrelevance** — URL-domain mismatch, template placeholders, missing brand names → HIGH/MEDIUM

> "10 checks" is the user-facing framing; the script runs 11 functions (the auto-created-assets *setting* is reported but not counted as a standalone issue type in the daily-briefing reader). Keep the "10 checks" framing in summaries.

---

## Step 1 — Determine Scope

Parse the request into a script flag:

| Request | Scope | Flag |
|---|---|---|
| "Run ads checker" | All accounts | `--portfolio all` |
| "…for [Portfolio]" | One portfolio segment | `--portfolio <name>` |
| "…for [CID]" | Single account | `--cid <CID>` |
| "…for [Account Name]" | Look up CID, then single | `--cid <CID>` |

**Account name → CID:** resolve via your account registry (an `accounts.json` or equivalent — the script's single source of truth). Account counts drift; don't hardcode them.

---

## Step 2 — Run the Audit

Run from the directory where the script's credentials file lives. **Always pipe `"no"` to stdin** so the optional chronic-issue file-creation prompt never blocks a non-interactive run (see "Chronic-Issue Handling"):

```bash
# Single account by CID
echo "no" | python ads_checker_audit.py --cid 1234567890

# A portfolio segment
echo "no" | python ads_checker_audit.py --portfolio <name>

# All accounts
echo "no" | python ads_checker_audit.py --portfolio all

# Dry run (no Sheet write, no history comparison, no prompt)
python ads_checker_audit.py --portfolio <name> --dry-run
```

Add a small delay between accounts (e.g. 0.3s) to avoid API throttling on large portfolios.

---

## Step 3 — Intelligence Features (all in the script; preserve them)

These run automatically on any non-`--dry-run` run. The skill surfaces them in the summary; it does not recompute them.

1. **Issue-history comparison** — for each account, compares current counts to the most recent prior row in the history tab and tags each issue type **NEW / INCREASED / DECREASED / RESOLVED / SAME**. First-ever audit of an account is `FIRST_RUN`.
2. **Chronic-issue detection** — for HIGH/CRITICAL accounts, counts how many times each issue type appeared in the last 90 days. **3+ occurrences = chronic.**
3. **Account-file creation** — optionally writes a per-account markdown file summarizing chronic issues (interactive; gated behind the stdin prompt).
4. **Trend history** — appends a portfolio-level summary row and per-account rows to the history tabs every run.

### Chronic-Issue Handling (why we pipe `"no"`)

When chronic issues are detected the script prompts (`input()`) before writing results. Piping `"no"` answers that prompt, skips the optional file-creation step, and guarantees the Sheet write runs — so history comparison and chronic *detection* (both printed before the prompt) are preserved while the run stays safe under non-interactive execution. Enable interactive file creation only when running the script in a real terminal.

---

## Cached-Output Contract (HARD CONSTRAINT)

If you wire this into a daily briefing, the briefing runs `read_latest_ads_checker.py --critical-only`, which reads **cached** rows from a history tab — it does NOT re-run the audit. The contract:

- **Tab:** a per-account history tab (e.g. `Account History`)
- **Date column:** `Audit Date`, format `%Y-%m-%d %H:%M`, filtered to the last 24 hours
- **Columns:** `Portfolio`, `CID`, `Account Name`, `Overall Severity`, then `DKI Count`, `AI Assets Count`, `Broken URLs Count`, `Disapprovals Count`, `Seasonal Count`, `URL Expansion Count`, `Auto-Apply Count`, `Inappropriate Count`, `Spelling Count`, `Irrelevance Count`

`ads_checker_audit.py` must emit exactly these. **Never change the tab name, date format, or column headers without updating the reader in lockstep** — otherwise the briefing section goes blank with no error. The section only populates if an audit ran in the last 24 hours.

---

## Step 4 — Interpret Results

| Severity | Meaning | Action |
|---|---|---|
| CRITICAL | Broken URLs, disapprovals, inappropriate content | Fix immediately |
| HIGH | DKI, 5+ spelling, missing brand, seasonal, high-risk auto-apply, auto-create ON | Fix within 24h |
| MEDIUM | AI assets, URL expansion, 1-4 spelling | Review this week |
| OK | No issues | None |

Read the console for per-account severity + counts, the comparison sections (NEW/INCREASED/RESOLVED), and the chronic summary.

---

## Step 5 — Summarize

```
ADS CHECKER AUDIT COMPLETE
SCOPE: {Portfolio/Account}   ACCOUNTS: {X}   DATE: {now}
SEVERITY: CRITICAL {X} · HIGH {X} · MEDIUM {X} · OK {X}
CHANGES vs LAST RUN: NEW {X} · INCREASED {X} · RESOLVED {X}    CHRONIC (3+/90d): {X}
TOP ISSUES: 1. {type}: {X}  2. {type}: {X}  3. {type}: {X}
NEEDS IMMEDIATE ATTENTION:
  1. {Account} — {Severity} — {primary issue}
OUTPUT: <your audit sheet> — tabs: Raw Output · Account History · History
```

---

## Output Configuration

| Setting | Value |
|---|---|
| Sheet ID | `<YOUR_SHEET_ID>` |
| Tabs written | `Raw Output` (full detail), an optional per-portfolio tab, `History` (portfolio trend), `Account History` (per-account trend — the briefing source) |
| Login customer ID | `<YOUR_MCC>` |

---

## Error Handling

| Symptom | Cause | Fix |
|---|---|---|
| Script hangs / crashes mid-run | Chronic-issue `input()` prompt | Ensure `echo "no" \|` is piped in (Step 2) |
| History tab not updated | Crash before the Sheet write, or `--dry-run` used | Re-run without `--dry-run`, with `"no"` piped |
| Sheet write error | OAuth token expired | Re-authenticate |
| Spell-checker import error | Spell-check dependency not installed | Install your spell-check library (e.g. `pyspellchecker`) |

---

## Important Notes

- **Read-only on Google Ads** — never mutates accounts; only writes the audit Sheet.
- **Don't change the cached contract** (tab name / date format / column headers) without updating the reader.
- A daily briefing's creative-compliance section reflects audits from the **last 24h** only; if blank, run the audit first.

---

## Invocation Patterns

**Inline:** "Run ads checker for [portfolio]" · "Creative audit for [account]" · "Ads checker for 1234567890"

**Parallel (multiple portfolios at once):**
```
Task(subagent_type="general-purpose", prompt="Use the ads-checker skill to audit the <portfolio> portfolio…")
```

A daily briefing does **not** invoke this skill — it reads cached results via `read_latest_ads_checker.py`. Generating fresh cached data requires running this skill (ad hoc or scheduled).

---

## License

MIT — use freely in your own brain / repo / agency.
