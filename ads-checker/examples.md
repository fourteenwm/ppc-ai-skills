# Examples — worked audit reads

Three worked triage decisions applying `rules.md`. All accounts, names,
CIDs, and numbers are synthetic.

## 1. Portfolio run with a chronic tag — ordering the fixes

**Run:** `--portfolio north` (Northgate Group registry, 3 accounts), live
run, Sheet written. Console:

```
[1/3] Auditing Northgate Group - Cedar Point Lofts... CRITICAL (6 issues, 2 disapprovals, 1 DKI, 3 seasonal)
[2/3] Auditing Northgate Group - Juniper Row... HIGH (6 issues, 2 auto-create ON, 6 spelling)
[3/3] Auditing Northgate Group - Bexley Commons... OK (0 issues)

COMPARISON TO PREVIOUS RUN
INCREASED ISSUES (1 accounts):
  • Northgate Group - Cedar Point Lofts: disapprovals (+1)

Detecting chronic issues...
CHRONIC ISSUES DETECTED - MANUAL REVIEW REQUIRED
🔴 Northgate Group - Cedar Point Lofts (1234567890)
   - Disapprovals: 3 occurrences (2026-05-02 to 2026-07-01)
```

**Reasoning:** Severity picks the account (Cedar Point first), but the
chronic tag changes what the disapprovals *are*: third time in 90 days means
the copy process keeps producing policy-tripping ads — resubmitting a fourth
rewrite without changing what the ads say is churn (rules: chronic before
new). The DKI string rides along in the same rewrite batch. The 3 seasonal
flags are "summer special" variants — it's July; the false-alarm table says
the check has no calendar, so these are current copy carrying a standing
flag, not work. Juniper Row's 6 spelling flags: 4 are coined amenity words
("petcierge", "skylounge" — on the property's own site), 2 are real typos.
The auto-create opt-ins compound while waiting (rules: structural before
copy).

**Decision:** (1) Cedar Point disapprovals → `rsa-refresh` for replacement
copy under the verification standard, AND a policy read of the disapproval
topics so the rewrite changes what tripped — the chronic note goes in the
summary. (2) Juniper Row auto-create → `pmax-asset-automation` to opt the
two campaigns out (its own preview + approval). (3) The 2 real typos →
`rsa-bulk-edit` find/replace; the 4 coined words → added to
`AD_COPY_EXCEPTIONS` in the script header so they stop flagging — copy
untouched. (4) Seasonal: noted current-until-promo-rotates, no action.
Nothing mutated from this session; every change goes through its own gate.

## 2. Edge case: the spurious HIGH on an unregistered account

**Run:** `--cid 0987654321` for a one-off account not yet in
`accounts.json`. Result: HIGH — `BRAND_MISSING` (irrelevance) plus 9
spelling flags on an account whose copy looked fine last week.

**Reasoning:** The row's account name reads `Account 0987654321` — the
registry placeholder. That's the tell (false-alarm table): the brand-
presence check extracted "account" + the CID digits as the expected brand
words and found them in no ad copy — of course. And with no registry entry,
the spelling brand-shield is empty, so every property-name word in the copy
flagged too. The HIGH is real script behavior on a misconfigured input, not
a creative problem.

**Decision:** Add the account to `accounts.json` (name + portfolio), re-run.
Result: OK, 0 issues. Zero copy edits — the fix was configuration. The
first-run row stays in `Account History` as scored (never overrule);
the triage note explains the artifact so the next operator doesn't read the
HIGH → OK transition as a fix.

## 3. Edge case: the blank briefing read as all-clear

**Situation:** The daily briefing's creative section has shown nothing for
three days. The operator is about to write "creative compliance clean this
week" in a client summary.

**Reasoning:** The reader only surfaces audits from the last 24 hours —
blank means *no recent audit data*, never *no issues* (false-alarm table:
blank = stale). Check the source: the last `Audit Date` row in
`Account History` is four days old. The Tuesday "run" was a `--dry-run`
(console output existed, so it *felt* like an audit) — and dry runs write
nothing: no rows, no comparison, no chronic scan. The pipeline has been
dark since Friday.

**Decision:** Don't ship the claim. Run the audit live
(`echo "no" | … --sheet-id …`), then read the briefing. The re-run surfaces
one CRITICAL (a broken sitelink URL from a weekend site deploy) that would
have sat invisible behind "clean this week." Lesson: the briefing is a
cache; `Audit Date` is the freshness check, and console output from a dry
run is not an audit of record.
