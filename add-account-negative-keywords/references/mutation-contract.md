# Mutation Contract — add_account_negative_keywords.py

> **Source of truth:** `scripts/add_account_negative_keywords.py`. Every claim below is
> derived from that script's code paths (line references in parentheses). If the script
> changes, update this contract and the CHANGELOG in the same commit. The judgment layer
> (which keywords belong in a baseline, when to run this at all) lives in `rules.md`;
> the workflow lives in `SKILL.md`.

---

## The three passes

One script, three distinct invocations. Nothing mutates until the third.

| Pass | Invocation | What happens | What's written |
|---|---|---|---|
| 1. Dry-run | *(no flags)* | Resolves accounts, loads keywords, queries all 3 layers per account, prints the preview table | **Nothing** — no logs, no sessions |
| 2. Code generation | `--execute` | Re-resolves and **re-queries state fresh**, prints the same preview, generates `APPROVE-XXXXXXXX`, snapshots the full plan | One session JSON |
| 3. Execution | `--execute --approval-code APPROVE-XXXXXXXX` | Loads the saved session and executes **that saved plan** | JSONL log rows (+ optional Sheet rows) |

- The approval code is `APPROVE-` + 8 uppercase hex chars (`secrets.token_hex(4).upper()`, :416-417).
- **Codes never expire.** Session files accumulate in `sessions/` and any old code still executes its old plan. Regenerate rather than reuse anything stale.
- **At execution time, the session is authoritative.** The CLI still requires an accounts argument and a readable keywords file (both are validated before the session loads, :646-676), but their *contents are ignored* — `plan` and `set_name` come from the session (:721-722). Typing different account names next to `--approval-code` does not change what executes.
- State is **not re-queried at execution**. An account that changed between code generation and execution is mutated per the snapshot.

## Account resolution (:88-175)

Comma-separated positional input and `--portfolio` **combine additively**; portfolio matching is a case-insensitive equality test on the `portfolio` field (:98-105). Per token:

1. Dashes stripped (:111). All-digit tokens try an exact `id` match in `accounts.json`.
2. An all-digit token **not found in the book is accepted anyway** as `CID <raw>` with portfolio `unknown` (:124-131). A typo'd CID does not error — it becomes a live target that fails later at query time.
3. Non-digit tokens walk a ladder: exact name (case-insensitive) → exact alias → **substring of the account name** (:153-160). First match in the book's insertion order wins, silently — `"north"` resolves to the first account containing "north".
4. Unresolvable name tokens print `WARNING: Could not resolve: ...` and are dropped (non-fatal, :165-166). Zero resolved accounts overall → `ERROR: No accounts resolved.`, exit 1.
5. Results dedupe by CID, order preserved (:169-175). `--exclude-cid` values are dash-stripped and removed after resolution (:656-658).

## Keywords-file resolution (:665-676)

The default is the **bare filename** `sample_baseline_keywords.txt` (:68) — no directory prefix. Resolution probes two locations, in order:

1. The path exactly as given, relative to your **current working directory**.
2. If that path is relative and doesn't exist: the same path **alongside the script** — `scripts/` in this skill, where the shipped sample actually lives (:666-670).

Consequences worth knowing:

- Run from anywhere with no flag and you get the shipped `scripts/sample_baseline_keywords.txt` — *unless* a file named `sample_baseline_keywords.txt` sits in your working directory, which silently wins.
- The `Loaded N baseline keywords from <name>` line prints **only the basename** (:676) — it never tells you which of the two probed locations won. If the loaded count surprises you, check for a shadowing file in your cwd.
- An absolute path skips the fallback; a not-found file prints the cwd-relative form and exits 1 (:671-673).
- Lines are stripped; blank lines are skipped (:674-675). The shipped sample is 131 keywords.
- On the execution pass the file is re-read but its contents are ignored (the session's `target_keywords` snapshot governs, :704).

## State query — the three layers (:189-251)

| Layer | Query | What it establishes |
|---|---|---|
| 1 | `shared_set` WHERE type = `ACCOUNT_LEVEL_NEGATIVE_KEYWORDS` AND status = `ENABLED` | The **first** ENABLED set returned wins (`break`, :209). The query has **no name filter** — `--set-name` plays no role in finding a set. |
| 2 | `shared_criterion` keyword text for that set (:216-228) | The existing-keyword set. Runs only if layer 1 found a set. |
| 3 | `customer_negative_criterion` WHERE type = `NEGATIVE_KEYWORD_LIST` (:234-245) | Whether **any** negative-keyword-list attachment exists. The API can't confirm it points to *this* set (the read-back quirk below), so existence is the whole check. |

Three facts that shape triage:

- **Layer errors print and are swallowed** (:210-211, :227-228, :244-245). A failed layer-1 query leaves `shared_set = None`, and the account is then categorized `NO_SET` — a permissions hiccup can make an account with an existing list look brand-new. Executing that plan would create a **second** set. The `Layer N query error:` lines above the categorization are the only tell; treat them as invalidating everything below.
- **The keyword delta is exact-string and case-sensitive** (:263). Google stores negative keyword text in its own normalized (lowercase) form, so a baseline row differing only in case or spacing re-counts as "missing" on every run. Keep baseline files lowercase, one keyword per line.
- **`cnc_attached` is recorded but never printed and never routes** (:254-276 consults only layers 1-2). It surfaces in exactly one place: the session JSON written by pass 2.

## Categorization and its blind spot (:254-276)

| Status | Condition | Execution path |
|---|---|---|
| `NO_SET` | No ENABLED account-level set found | Full 3-step: SharedSet → SharedCriteria → CustomerNegativeCriterion |
| `PARTIAL` | Set exists, some baseline keywords absent | Step 2 only — adds the missing SharedCriteria to the **found** set (:319-326) |
| `COMPLIANT` | Set exists, all baseline keywords present | Skipped entirely |

**The skill attaches a CustomerNegativeCriterion only on the `NO_SET` path** (:301-308). A set that exists but was never attached — the fragile 2-step state this skill's README warns about, or the residue of a 3-step run that died between steps 2 and 3 — reads `PARTIAL` or `COMPLIANT` and **never gets its attachment repaired**. After any roll, check `"cnc_attached"` in the session JSON; a `false` on a set-having account is a manual fix (UI or a one-off), not something a re-run heals.

Because `--set-name` only names sets the script *creates*, delta adds land in whichever ENABLED account-level set layer 1 found first, regardless of its name.

## Mutation mechanics (:283-352)

- Keywords are added as `SharedCriterion` entries, **PHRASE match hardcoded at the mutation site** (:345). The `DEFAULT_MATCH_TYPE` constant (:70) has no consumers — editing it changes nothing, and there is no match-type flag.
- Adds are batched at 1000 operations per request (:337-338). The preview's `Total API mutations` counts *operations* (NO_SET = 1 + N + 1; PARTIAL = M, :484-491), not requests.
- Per-account isolation: each account executes inside its own try/except (:515-558); a failure logs and the batch continues. `GoogleAdsException` messages are semicolon-joined (:543-544); anything else is stringified.
- A mid-3-step failure is **not transactional**: a set created in step 1 survives a step-2/3 failure. The next dry-run sees it as `PARTIAL` — keywords heal on re-run, the attachment does not (above).

## Logging (:359-409)

- **Local JSONL — always on during execution.** `logs/account_negs_mutations.jsonl`, one row per account: `timestamp_utc`, `approval_code`, `account_cid`, `account_name`, `action_type` (`ADD_ACCOUNT_NEGATIVE_KEYWORDS`), `details`, `success` (bool), `error`. Dry-runs and code generation write no JSONL.
- **Sheet log — opt-in** via `--log-sheet-id`. Appends to `A:H` (RAW, INSERT_ROWS): Timestamp, Account, CID, Action Type, Details, Success (`YES`/`NO`), Error, Approval Code. Auth rebuilds from the `refresh_token` in your `google-ads.yaml` with the spreadsheets scope only, **refreshing once per logged row** (:379-390).
- Asymmetric sheet-failure handling — three cases, by account outcome: on a *successful* account, a failed sheet append prints `WARNING: Sheet log failed: ...` (:540-541); on a `GoogleAdsException` failure, the append is attempted and any sheet error swallowed silently (:549-552); on a *generic-exception* failure, the sheet write is never attempted at all — the account is simply absent from the Sheet log (:554-558 has no log-sheet block). The JSONL row exists in all three cases — the local log is the audit trail of record.
- Default locations derive from the **script's own path**, not your working directory: `<skill folder>/logs/` and `<skill folder>/sessions/` (:74-76). Both are created on demand. Session files contain resolved account names, CIDs, and the full keyword list — treat them as operator-sensitive and keep them out of version control.

## Console anatomy

Emitted shapes (all from :440-501 and :684-745; table paddings are `<40`/`<16`/`<12`/`>5`, account names truncated to 38 chars, CIDs displayed dashed `xxx-xxx-xxxx`):

```
Loaded 131 baseline keywords from sample_baseline_keywords.txt

DRY-RUN: querying state for 3 account(s)...

  Querying state: <Account Name> (CID: 123-456-7890)...
    -> PARTIAL: SharedSet 11223344556 exists, missing 12 of 131 keywords
```

then the 80-char `DRY-RUN PREVIEW` table with the five summary lines (`NO_SET (full 3-step setup)` / `PARTIAL (Step 2 only)` / `COMPLIANT (skip)` / `Total keywords to add` / `Total API mutations`). Pass 2 prints `EXECUTE (pending approval):` instead of `DRY-RUN:`, then `Approval code:` / `Session saved:` / `To execute the saved plan, re-run with --approval-code ...`. Pass 3 prints `EXECUTING (approval code: ...)`, `Accounts to mutate: N`, per-account `OK - <details>` or `FAILED: <errors>` lines, and the `EXECUTION SUMMARY` block whose counts are **accounts**, not keywords. The final line is always the habit the skill wants you to keep: `Verify in UI: Admin -> Account Settings -> Negative Keywords`.

## The API quirks this script is built around

| Quirk | Impact | How the script responds |
|---|---|---|
| `shared_set.member_count` always reports 0 | Can't verify keyword adds from the set object | Re-queries `shared_criterion` directly (layer 2) |
| `shared_set.reference_count` always reports 0 | Can't verify attachment from the set object | Checks `customer_negative_criterion` directly (layer 3) |
| `negative_keyword_list.shared_set` reads back empty in GAQL | The write succeeds; the read can't confirm *which* set is attached | Treats CNC existence as the signal (:231-232) and defers final confirmation to the UI |
| The GAQL field is `customer_negative_criterion.id`, not `criterion_id` | Wrong field name silently returns nothing | Uses the correct field (:235) |

## Defaults and exits

| Surface | Value |
|---|---|
| `--accounts-json` | `accounts.json` in the **current directory** (:617); missing → exit 1 |
| `--credentials` | `google-ads.yaml` in the current directory (:623) |
| `--set-name` | `"Account Negative Keywords"` — applies only when a set is created |
| Exit 1 | Missing accounts.json; zero resolved accounts; keywords file not found; unknown approval code |
| Windows consoles | stdout/stderr rewrapped UTF-8 (:45-47) |
