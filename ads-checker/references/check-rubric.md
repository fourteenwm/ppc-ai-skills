# Check Rubric — the 10 checks, exact criteria & the output contract

Per-check firing criteria and severity mapping for the creative-compliance
audit, plus the cached-output contract both scripts share. Use this to answer
"why did this check fire?" or "why is the briefing blank?" without reading
the engines.

> **Source of truth:** `scripts/ads_checker_audit.py` (criteria, severities,
> history/chronic mechanics) and `scripts/read_latest_ads_checker.py` (the
> read side of the output contract). This document mirrors both as of the
> 2026-07-22 revision. If you change a check or the contract in a script,
> update the matching section here and add a CHANGELOG entry.

---

## "10 checks" vs 11 functions

"10 checks" is the reporting frame — summaries, tab columns, and the history
schema all count 10 issue types. The script runs **11 check functions**. The
uncounted one is **Auto-Created Assets Setting** (#6 below): it inspects a
campaign *setting* (`TEXT_ASSET_AUTOMATION` opted in), not an issue volume,
while check #2 already counts the auto-created assets that setting produces.
The setting check **does** feed the account's overall severity and appears in
the `Raw Output` tab, but it has no column in `Account History`, is excluded
from run-over-run comparison and chronic detection, and is not part of the
console "actionable issues" count. Keep "10 checks" in summaries.

---

## The checks

Severity per account = the **worst** single check result
(CRITICAL > HIGH > MEDIUM > OK). Any exception while auditing an account
marks that account ERROR (its row still writes, with `Error` cells).

### 1. DKI Detection → HIGH

- Pattern: `{keyword:...}` / `{KeyWord:...}` etc. (case-insensitive DKI syntax).
- Scans RSA headlines + descriptions where campaign, ad group, AND ad are all
  ENABLED; plus the whole asset library's TEXT / SITELINK / CALLOUT text
  fields (any status, linked or not).
- HIGH if ≥1 match, else OK.

### 2. Google AI Assets → MEDIUM

- Assets with `source = AUTOMATICALLY_CREATED`, from two angles: the asset
  library directly, and RSA-attached assets via `ad_group_ad_asset_view`.
- Deduplicated by type + text prefix. MEDIUM if ≥1.

### 3. URL Validation → CRITICAL

- Collects final URLs from ENABLED ads (campaign + ad group + ad all ENABLED)
  and from ALL sitelink assets, deduplicates, then checks **only the first
  20 unique URLs** (parallel HEAD requests, 5 workers, 5s timeout, redirects
  followed).
- Fires on HTTP ≥ 400, timeout, or connection error. CRITICAL if ≥1.
- Consequences of the design: URL-heavy accounts are sampled, not exhausted;
  a redirect to a live page passes; servers that reject HEAD requests can
  false-positive (see the false-alarm table in `rules.md`).

### 4. Ad Disapprovals → CRITICAL / MEDIUM

- ENABLED ads (all three levels) — paused campaigns' disapprovals are
  deliberately invisible.
- `APPROVED` and `APPROVED_LIMITED` are treated as approved and never
  flagged. `DISAPPROVED` → CRITICAL. `LIMITED` / `AREA_OF_INTEREST_ONLY`
  (eligibility-limited) → MEDIUM. The count column includes every
  non-approved status collected.

### 5. Seasonal Promotions → HIGH

- Case-insensitive substring match against a fixed keyword list: named
  holidays, `<season> sale/special/savings`, `holiday sale/special/savings`,
  `end of year`, `year-end`, `limited time`, `this weekend only`, and
  `<month> special` for all 12 months.
- Scans RSA text of ENABLED ads (**ad status only** — campaign/ad-group
  status is not filtered here) plus ALL sitelink/callout assets. First
  matching keyword per text. HIGH if ≥1.
- The check has no calendar: it flags the *presence* of seasonal language;
  whether the promo is current is operator judgment (`rules.md`).

### 6. Auto-Created Assets Setting → HIGH *(the uncounted 11th — see above)*

- ENABLED campaigns where `TEXT_ASSET_AUTOMATION` is explicitly `OPTED_IN`.
- HIGH if ≥1 opted-in campaign; also reports opted-out and total counts.
  Campaigns with no explicit setting are neither (Google's default varies by
  campaign type).

### 7. Final URL Expansion → MEDIUM

- ENABLED campaigns where `FINAL_URL_EXPANSION_TEXT_ASSET_AUTOMATION` is
  `OPTED_IN` (Google may send traffic to URLs you didn't set). MEDIUM if ≥1.

### 8. Auto-Applied Recommendations → HIGH / MEDIUM

- Reads `recommendation_subscription` rows; **`OPTIMIZE_AD_ROTATION` is
  whitelisted and never flagged** (an auto-apply count of 0 does not mean
  zero subscriptions exist).
- Any other ENABLED subscription is flagged. High-risk types → HIGH:
  `KEYWORD`, `RAISE_TARGET_CPA_BID_TOO_LOW`, `LOWER_TARGET_ROAS`,
  `RESPONSIVE_SEARCH_AD`, `USE_BROAD_MATCH_KEYWORD`, `RAISE_TARGET_CPA`,
  `FORECASTING_SET_TARGET_CPA`, `FORECASTING_SET_TARGET_ROAS`.
  Everything else ENABLED → MEDIUM.

### 9. Inappropriate Content → CRITICAL / HIGH / OK

- Word-boundary match against the blocklist in the script header (a labeled
  starter set: profanity, violence, adult, discriminatory, scam, competitor,
  spam categories — the discriminatory/scam/competitor sections ship
  housing-vertical examples; swap for your vertical). First matched term per
  text is reported.
- Scans RSA text of ENABLED ads (ad status only) plus TEXT / SITELINK /
  CALLOUT / STRUCTURED_SNIPPET assets (any status, headers and values).
- Severity comes from **which term** matched, not the count: terms on the
  critical list (hard profanity, adult content, discriminatory-exclusion
  phrases like "no kids" / "whites only") → CRITICAL; terms on the high list
  (milder profanity, violence terms, "no section 8"-class phrases) → HIGH.
  **Matches outside both lists — the spam/competitor rows — raise the count
  but leave severity at OK.** A nonzero inappropriate count with an OK
  severity means only mild-category matches; read the details column before
  escalating.

### 10. Spelling → HIGH / MEDIUM

- `pyspellchecker` (English, distance=1). Known-word exceptions =
  the `AD_COPY_EXCEPTIONS` starter list in the script header **plus every
  word of every account name in your registry** (brand shield — built from
  the whole registry, not just the audited account; on registry-less
  `--cid`/`--cids` runs there is effectively no brand shield — a
  registry-less `--all` walk builds it from the walked account names).
- Extraction strips DKI patterns, URLs, and numbers, splits hyphenated
  words, drops words under 3 characters and contractions. Skipped: words
  appearing ALL-CAPS in the original (acronyms), digit-containing tokens,
  and words appearing Title-Case in the original (proper-noun heuristic —
  lowercase stylized brand words still flag).
- Findings deduplicate by word. **5+ unique misspellings → HIGH, 1–4 →
  MEDIUM,** 0 → OK.

### 11. Irrelevance → HIGH / MEDIUM

Three sub-checks, one count:

- **URL domain mismatch** — the most common domain across ENABLED ads'
  final URLs + all sitelinks (www-stripped; tracking/social domains ignored)
  is "expected"; any other domain is flagged (capped at 3 findings).
- **Template placeholders** — `[...]`, `{...}` (excluding `{CUSTOMIZER.*}`
  and DKI syntax), `<...>`, `XXXX`, `TODO`, `INSERT HERE`,
  `YOUR PROPERTY/BRAND/NAME/COMPANY`, `PLACEHOLDER`, `LOREM IPSUM` in RSA
  text (capped at 3).
- **Brand-name presence** — expected brand words come from the account name
  (any `Parent Brand - ` prefix dropped, filler words dropped, ≥3 chars).
  Runs **only if that yields 1–5 terms**; flags **only if ALL terms are
  missing from ALL RSA copy**. An unregistered `--cid` run gets the
  placeholder name `Account <cid>` — those literal words become the
  "brand," which is the spurious-HIGH trap in `rules.md`.
- Severity: any template or brand-missing finding → HIGH; 3+ domain
  mismatches → HIGH; 1–2 → MEDIUM; else OK.

### Console "actionable issues" count

The per-account console line sums **DKI + broken URLs + disapprovals +
seasonal + high-risk auto-apply + inappropriate + spelling + irrelevance**.
AI assets, the auto-created setting, URL expansion, and non-high-risk
auto-apply are excluded from the number and print as suffix extras
(`4739 AI, 2 auto-create ON, …`).

---

## Cached-output contract (HARD — both scripts in lockstep)

`read_latest_ads_checker.py` reads **cached rows**; it never calls the
Google Ads API and never re-runs the audit. Any drift in tab name, date
format, or headers makes the reader return nothing — the briefing section
goes **silently blank** with no error. Never change one script without the
other.

**Tabs written per live run** (`--dry-run` writes nothing at all — no
comparison, no chronic detection, no prompt, no rows):

| Tab | Behavior | Contents |
|-----|----------|----------|
| `Raw Output` | **Cleared and rewritten** every run | Current snapshot: one row per account, all check counts/severities/details |
| Per-portfolio tab *(only on portfolio-scoped runs)* | Cleared and rewritten | Same rows, under the portfolio's display name (`all` → `All Portfolios`) |
| `History` | **Appends** one summary row per run | Severity counts + per-type totals (trend surface, read by humans only) |
| `Account History` | **Appends** one row per account per run | **The contract tab** — what the reader consumes |

**`Account History` columns, exactly:** `Audit Date` (format
`%Y-%m-%d %H:%M`), `Portfolio`, `CID`, `Account Name`, `Overall Severity`,
then `DKI Count`, `AI Assets Count`, `Broken URLs Count`,
`Disapprovals Count`, `Seasonal Count`, `URL Expansion Count`,
`Auto-Apply Count`, `Inappropriate Count`, `Spelling Count`,
`Irrelevance Count`.

**Reader behavior:** filters `Audit Date` to the last N hours (default 24,
`--hours-back N`), optionally by exact `Portfolio` value, `--critical-only`
keeps CRITICAL/HIGH; output is briefing text (issue priority: disapprovals →
broken URLs → inappropriate → DKI → spelling → irrelevance → seasonal →
auto-apply, top 3 shown) or `--json`.

**Portfolio labels in rows:** `Account History` rows carry the **run's
scope** — the portfolio name for `--portfolio` runs, `all`, or `custom` for
`--cid`/`--cids` runs. (`Raw Output` rows instead carry each account's
registry portfolio, `unknown` if unregistered — the two tabs can disagree
for the same run; that's expected.)

### Comparison & chronic semantics

- **Sequencing:** run-over-run comparison and chronic detection read the
  history tabs **before** the new rows are appended — each run compares
  against the previous run, then writes its own.
- **Comparison** (`NEW` / `INCREASED` / `DECREASED` / `RESOLVED` / `SAME`):
  per issue type, current count vs the account's most recent prior
  `Account History` row. 0→>0 = NEW, >0→0 = RESOLVED, else
  INCREASED/DECREASED/SAME. No prior row = `FIRST_RUN`.
  Portfolio-scoped runs only match prior rows with the **same** portfolio
  label; `--cid` runs match any. Mixing scopes therefore fragments
  comparison history — an account audited under `custom` yesterday can read
  FIRST_RUN under `--portfolio` today.
- **Chronic detection:** for HIGH/CRITICAL accounts only, counts how many
  `Account History` rows in the last 90 days show each currently-flagged
  issue type at count > 0 — **3+ occurrences = chronic**. Matches by CID
  across all scope labels (unlike comparison). `ai_assets` is excluded as
  informational. Chronic findings trigger the interactive account-file
  prompt (the `echo "no" |` mechanics in SKILL.md).
- **Row hygiene:** past 1,000 `Account History` rows the script prints an
  archive warning (~180-day retention guidance); archiving is manual.

---

## Registry & scope resolution

The `accounts.json` schema is documented in the script header (the script is
its single source of truth). Registry names may follow a
`Parent Brand - Property Name` convention — the text after the first `" - "`
is treated as the brand for spell-check exceptions and the brand-presence
check. Unregistered CIDs run fine but display as `Account <cid>` (see the
brand-presence trap above). Without any registry, `--all` walks the MCC in
your `google-ads.yaml` and every account lands in the `default` portfolio.
