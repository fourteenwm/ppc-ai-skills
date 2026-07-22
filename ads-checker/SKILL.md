---
name: ads-checker
description: Audit Google Ads accounts for creative compliance (10 checks) with intelligence integration (issue-history comparison, chronic-issue detection, daily-briefing integration). Ships both scripts (audit + briefing reader). Auto-invoke when user says "run ads checker", "creative audit", "check ads for [portfolio]", "audit ads", or "ads checker for [account/portfolio]". Outputs to a Google Sheet with a severity breakdown. Read-only — no Google Ads mutations.
allowed-tools: [Read, Bash, Grep, Glob]
---

# Ads Checker

**Purpose:** Run creative-compliance audits across your Google Ads
portfolios, track issue history across runs, detect chronic problems, and
write prioritized findings to a Google Sheet.

**Type:** Read-only audit skill. It does not mutate Google Ads — it only
reports issues and writes results to an audit Google Sheet.

One operator owns the workflow end to end: determine scope → run the audit →
triage the results (`rules.md`) → route each actionable finding to its fix
skill. The audit itself never changes an account.

---

## What This Skill Wraps

All audit logic and **all intelligence features** live in one script —
[`scripts/ads_checker_audit.py`](scripts/ads_checker_audit.py), shipped with
this skill. This skill is a procedural wrapper: it determines scope, runs the
script, interprets the console output, and summarizes findings. **Do not
reimplement the checks in the skill; the script is the single source of
truth.**

A small read-only companion script,
[`scripts/read_latest_ads_checker.py`](scripts/read_latest_ads_checker.py)
(also shipped), is consumed by a daily briefing to surface recent
CRITICAL/HIGH findings from **cached** rows. The two scripts share a hard
lockstep contract — tab name, date format, column headers — owned by
[`references/check-rubric.md`](references/check-rubric.md) (§ Cached-output
contract). Break it in one script and the briefing goes silently blank.

Both scripts are self-contained: credentials come from your
`google-ads.yaml` (`--config`), the account registry from an `accounts.json`
(`--accounts`, optional), and the output Sheet from `--sheet-id`.

**The 10 checks** (creative-compliance scope): DKI, Google AI assets, broken
URLs, ad disapprovals, seasonal copy, auto-created-assets setting, final URL
expansion, auto-applied recommendations, inappropriate content, spelling,
and irrelevance. Exact firing criteria, per-check severities, and the
10-checks-vs-11-functions precision live in
[`references/check-rubric.md`](references/check-rubric.md) — keep the
"10 checks" framing in summaries.

---

## Prerequisites

- **`google-ads.yaml`** at project root (or `--config <path>`) — see the
  [google-ads-api-setup](../google-ads-api-setup/) skill for creating it.
  Its OAuth credentials are reused for the Google Sheets writes; set
  `login_customer_id` to your MCC if you want `--all` to work without a
  registry.
- **Python packages:** `pip install google-ads gspread google-auth pyyaml requests pyspellchecker`
- **An audit Google Sheet** — create an empty spreadsheet and pass its ID
  via `--sheet-id`; the script creates its own tabs.
- **Optional: `accounts.json`** at project root (or `--accounts <path>`)
  for name/portfolio resolution — schema documented in the script header.
  Auditing an unregistered CID works but triggers a known false alarm
  (`rules.md` → BRAND_MISSING row).

---

## Step 1 — Determine Scope

Parse the request into a script flag:

| Request | Scope | Flag |
|---|---|---|
| "Run ads checker" | All accounts | `--portfolio all` (or `--all`) |
| "…for [Portfolio]" | One portfolio segment | `--portfolio <name>` |
| "…for [CID]" | Single account | `--cid <CID>` |
| "…for [Account Name]" | Look up CID, then single | `--cid <CID>` |
| "…for [several accounts]" | A specific set | `--cids <CID1,CID2,…>` |

**Account name → CID:** resolve via your `accounts.json` registry (default
`./accounts.json`, override with `--accounts` — the script's single source
of truth; its schema is documented in the script header). Portfolio names
are whatever grouping labels your registry uses. Account counts drift; don't
hardcode them. With no registry, `--all` walks the MCC in your
`google-ads.yaml`. Prefer a consistent scope per account over time —
comparison history is scope-bound (see the rubric's comparison semantics).

---

## Step 2 — Run the Audit

Run from the directory where `google-ads.yaml` lives (or pass `--config`).
**Always pipe `"no"` to stdin** so the optional chronic-issue file-creation
prompt never blocks a non-interactive run (see "Chronic-Issue Handling"):

```bash
# Single account by CID
echo "no" | python scripts/ads_checker_audit.py --cid 1234567890 --sheet-id YOUR_SHEET_ID

# A portfolio segment
echo "no" | python scripts/ads_checker_audit.py --portfolio <name> --sheet-id YOUR_SHEET_ID

# All accounts
echo "no" | python scripts/ads_checker_audit.py --portfolio all --sheet-id YOUR_SHEET_ID

# Dry run (no Sheet write, no history comparison, no prompt)
python scripts/ads_checker_audit.py --portfolio <name> --dry-run
```

The script already sleeps 0.3s between accounts to avoid API throttling on
large portfolios. A `--dry-run` writes **nothing** — no rows, no comparison,
no chronic scan — so it never counts as an audit of record (`rules.md` →
blank-briefing row).

---

## Step 3 — Intelligence Features (all in the script; preserve them)

These run automatically on any non-`--dry-run` run. The skill surfaces them
in the summary; it does not recompute them.

1. **Issue-history comparison** — tags each issue type
   NEW / INCREASED / DECREASED / RESOLVED / SAME vs the account's previous
   audit (`FIRST_RUN` if none). Tag mechanics: the rubric. How to read
   them: `rules.md`.
2. **Chronic-issue detection** — 3+ occurrences of an issue type in 90 days
   on HIGH/CRITICAL accounts. Chronic means the fix isn't sticking —
   `rules.md` § Chronic issues.
3. **Account-file creation** — optionally writes a per-account markdown
   dossier (`./accounts/<portfolio>/<account-slug>.md`) for chronic
   accounts (interactive; gated behind the stdin prompt).
4. **Trend history** — appends portfolio and per-account rows to the
   history tabs every run.

### Chronic-Issue Handling (why we pipe `"no"`)

When chronic issues are detected the script prompts (`input()`) before
writing results. Piping `"no"` answers that prompt, skips the optional
file-creation step, and guarantees the Sheet write runs — so history
comparison and chronic *detection* (both printed before the prompt) are
preserved while the run stays safe under non-interactive execution. Enable
interactive file creation only when running the script in a real terminal.

---

## Step 4 — Triage the Results

Read the console for per-account severity + counts, the comparison sections
(NEW/INCREASED/RESOLVED), and the chronic summary. Then:

1. **Read [`rules.md`](rules.md) before recommending anything** — apply the
   triage order (CRITICAL by exposure → chronic → NEW/INCREASED →
   structural HIGH → copy HIGH → MEDIUM batch) and rule out the
   false-alarm classes. A flag that's a false alarm gets contextualized,
   never rewritten.
2. **Route each actionable finding** per the rules.md routing table — every
   fix is its own skill with its own review gate, or an exactly-specified
   UI change.
3. When asked *why* a check fired, answer from
   [`references/check-rubric.md`](references/check-rubric.md) — exact
   criteria, not paraphrase. [`examples.md`](examples.md) shows the
   expected shape of a triage read-out.

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

## When a finding fires — where it routes

Triage itself lives in [`rules.md`](rules.md) (read it before acting;
[`examples.md`](examples.md) shows worked reads). What triage surfaces
routes to siblings:

| Trigger | Load |
|---------|------|
| Disapproved / DKI / stale-seasonal copy needs rewriting | [`rsa-refresh`](../rsa-refresh/) or [`rsa-single-account`](../rsa-single-account/); [`rsa-bulk-edit`](../rsa-bulk-edit/) for the same string across many ads — all under [`ad-copy-verification-standard`](../ad-copy-verification-standard/) |
| Discriminatory-category match on a housing account | [`fair-housing-compliance`](../fair-housing-compliance/) — compliance layer alongside the rewrite |
| Automation opted in (AI assets / auto-create / URL expansion) | [`pmax-asset-automation`](../pmax-asset-automation/) for campaign-level opt-outs; [`dgen-automation-disable`](../dgen-automation-disable/) for Demand Gen ad-level automation |
| "Is the whole account healthy, beyond creative?" | [`account-diagnostic`](../account-diagnostic/) — the 42-point inspection |
| Ad-hoc verification pull (which ads carry this phrase/URL?) | [`google-ads-query`](../google-ads-query/) |
| "Why did this check fire?" / briefing blank / contract questions | [`references/check-rubric.md`](references/check-rubric.md) |

---

## What this skill deliberately does NOT do

- **No mutations, ever.** Read-only on Google Ads; its only writes are the
  audit Sheet and the optional local chronic-issue files. Every fix routes
  through a sibling with its own review gate.
- **No fix execution from audit rows.** Replacement copy comes from
  verified source material via the RSA skills — never from the audit's
  detail snippets.
- **No portfolio prioritization.** The audit scores what it scans; deciding
  which accounts to scan first, or which portfolio deserves attention, is
  the operator's call.
- **No scheduling.** Cadence (and whether a briefing consumes the cache) is
  your pipeline's decision — see Invocation Patterns.

---

## Error Handling

| Symptom | Cause | Fix |
|---|---|---|
| `Error: --sheet-id is required` | Live run without an output Sheet | Pass `--sheet-id`, or use `--dry-run` |
| Script hangs / crashes mid-run | Chronic-issue `input()` prompt | Ensure `echo "no" \|` is piped in (Step 2) |
| History tab not updated | Crash before the Sheet write, or `--dry-run` used | Re-run without `--dry-run`, with `"no"` piped |
| Sheet write error | OAuth token expired | Re-authenticate (see google-ads-api-setup) |
| Spell-checker import error | Spell-check dependency not installed | `pip install pyspellchecker` |
| `Error: --portfolio requires an accounts.json` | Named portfolio with no registry | Create `accounts.json`, or use `--cid`/`--cids`/`--all` |
| Briefing section blank | No audit in the last 24h (or the last run was `--dry-run`) | Check `Audit Date` in `Account History`; run the audit (`rules.md`) |

---

## Files in this skill

| File | Purpose |
|------|---------|
| `SKILL.md` | This file — workflow + routing |
| `README.md` | Zero-context setup guide: install, prerequisites, usage |
| `rules.md` | Judgment layer: invariants, triage order, history-tag reading, false-alarm classes, chronic reasoning, routing table |
| `examples.md` | Worked triage reads, incl. two edge cases |
| `references/check-rubric.md` | Exact per-check criteria + severities, the cached-output contract, comparison/chronic semantics |
| `scripts/ads_checker_audit.py` | The audit engine (read-only on Google Ads) |
| `scripts/read_latest_ads_checker.py` | Briefing reader — cached rows only, never re-runs the audit |

Runtime output lands in your audit Sheet (and optional `./accounts/` dossier
files) — never inside the skill folder.

---

## Invocation Patterns

**Inline:** "Run ads checker for [portfolio]" · "Creative audit for
[account]" · "Ads checker for 1234567890"

**Parallel (multiple portfolios at once):**
```
Task(subagent_type="general-purpose", prompt="Use the ads-checker skill to audit the <portfolio> portfolio…")
```

A daily briefing does **not** invoke this skill — it reads cached results
via `read_latest_ads_checker.py`. Generating fresh cached data requires
running this skill (ad hoc or scheduled). A blank briefing section means
stale cache, not a clean book (`rules.md`).

---

## License

MIT — use freely in your own brain / repo / agency.
