# Worked Examples — Account-Level Negative Keywords

Three reads. Names, CIDs, and IDs are synthetic; console excerpts are derived from the
script's own print statements (paddings and summary lines exact, long runs elided where
marked). Decision logic: `rules.md`. Mechanics: `references/mutation-contract.md`.

---

## Example 1 — Portfolio roll with a curation catch

**Ask:** "Roll the baseline negatives to the Lindenmoor portfolio."

Four accounts in `accounts.json` under portfolio `lindenmoor`: Lindenmoor North (new,
launched last month), Lindenmoor Crossing, Halstead Commons, and Ravenna Flats.

**Curation pass first, not the script.** The exceptions sweep from `rules.md` catches
one account: Ravenna Flats is a 55+ active-adult community. Seven shipped rows —
`senior`, `retirement`, `over 55`, `55 plus`, `55 and over`, `55 and older`,
`55 communities` — are its *core traffic*, not noise. Decision: exclude Ravenna from the
roll (`--exclude-cid 4567890123`); its exclusions belong at campaign level. The baseline
stays intact for the other three.

**Conflict pre-flight:** a keywords pull on the three remaining accounts, grepped
against the baseline. One hit: Halstead Commons bids `income based apartments` as a
positive — a legacy experiment from a prior manager. Halstead's existing account list
turns out to already contain the `income based` row, which explains the keyword's 0
conversions in 12 months: the account-level negative has been silently suppressing it
the whole time — exactly the conflict class `neg-conflict-finder` exists to surface.
The strategy call (made with the account owner, not silently): the row is right, the
dead positive gets paused so the account state stops lying. Recorded, then:

```
python scripts/add_account_negative_keywords.py --portfolio lindenmoor --exclude-cid 4567890123
```

```
Loaded 131 baseline keywords from sample_baseline_keywords.txt

DRY-RUN: querying state for 3 account(s)...

  Querying state: Lindenmoor North (CID: 123-456-7890)...
    -> NO_SET: No ACCOUNT_LEVEL_NEGATIVE_KEYWORDS SharedSet exists

  Querying state: Lindenmoor Crossing (CID: 123-456-7891)...
    -> PARTIAL: SharedSet 11223344556 exists, missing 12 of 131 keywords

  Querying state: Halstead Commons (CID: 234-567-8901)...
    -> COMPLIANT: All 131 baseline keywords present in SharedSet 11223344667

================================================================================
DRY-RUN PREVIEW - ACCOUNT-LEVEL NEGATIVE KEYWORDS
================================================================================
  Target baseline: 131 keywords (PHRASE match)
  SharedSet name: "Account Negative Keywords"

Account                                  CID              Status         Add
--------------------------------------------------------------------------------
Lindenmoor North                         123-456-7890     NO_SET         131
Lindenmoor Crossing                      123-456-7891     PARTIAL         12
Halstead Commons                         234-567-8901     COMPLIANT        0
--------------------------------------------------------------------------------
  NO_SET (full 3-step setup):       1
  PARTIAL (Step 2 only):            1
  COMPLIANT (skip):                 1
  Total keywords to add:            143
  Total API mutations:              145
================================================================================

To execute, run with --execute (a fresh approval code will be generated).
```

The read: North gets the full 3-step build (131 keywords + set + attachment = 133
operations); Crossing picked up 12 new rows since the baseline last grew; Halstead is a
no-op. The plan matches expectations, so re-run with `--execute`, review the identical
fresh preview, and take the code:

```
Approval code: APPROVE-3F81C2AB
Session saved: .claude/skills/add-account-negative-keywords/sessions/account_negs_APPROVE-3F81C2AB.json

To execute the saved plan, re-run with --approval-code APPROVE-3F81C2AB
```

Human reviews, gives the go, execution pass:

```
EXECUTING (approval code: APPROVE-3F81C2AB)
Accounts to mutate: 2

  Lindenmoor North (CID: 123-456-7890) - NO_SET
    OK - Full 3-step: created SharedSet 99887766554, added 131 keywords, CNC customers/1234567890/customerNegativeCriteria/55443322110

  Lindenmoor Crossing (CID: 123-456-7891) - PARTIAL
    OK - Step 2 only: added 12 missing keywords to existing SharedSet 11223344556

================================================================================
EXECUTION SUMMARY
================================================================================
  Accounts mutated successfully: 2
  Accounts failed:               0
  Local log:                     .claude/skills/add-account-negative-keywords/logs/account_negs_mutations.jsonl
================================================================================

Verify in UI: Admin -> Account Settings -> Negative Keywords
```

Close-out: UI spot-check on North, then [`neg-conflict-finder`](../neg-conflict-finder/)
across all three accounts' full negative surface. It confirms the Halstead conflict is
resolved (positive paused) and — the reason the post-roll scan is a rule, not a
nicety — that the 131 rows just landed in North didn't block any of *its* positives.
Done. Ravenna's campaign-level exclusions go on the todo list as a separate, smaller
decision.

---

## Example 2 — Two dry-run reads that prevent bad executions

**Scene A — the error line above the verdict.** Routine drift check on Tolliver Square:

```
Loaded 131 baseline keywords from sample_baseline_keywords.txt

DRY-RUN: querying state for 1 account(s)...

  Querying state: Tolliver Square (CID: 345-678-9012)...
    Layer 1 query error: User doesn't have permission to access customer. Note: If you're accessing a client customer, the manager's customer id must be set in the 'login-customer-id' header.
    Layer 3 query error: User doesn't have permission to access customer. Note: If you're accessing a client customer, the manager's customer id must be set in the 'login-customer-id' header.
    -> NO_SET: No ACCOUNT_LEVEL_NEGATIVE_KEYWORDS SharedSet exists
```

The table below this says `NO_SET / Add 131`, and Tolliver has had a complete list for a
year. The two error lines are the real result: the script couldn't see the account (the
`login_customer_id` in this `google-ads.yaml` doesn't manage it), found nothing, and
categorized the nothing. Executing this plan would create a **second** account-level
set. Action: stop, fix the credentials header, re-run — the account now reads
`COMPLIANT: All 131 baseline keywords present in SharedSet 44556677889`. Rule applied:
an error line invalidates every verdict below it.

**Scene B — COMPLIANT isn't the whole story.** After a roll, the session JSON is the one
place the attachment state surfaces. A post-run habit check:

```
grep -o '"cnc_attached": [a-z]*' sessions/account_negs_APPROVE-3F81C2AB.json
```

Lindenmoor Crossing shows `"cnc_attached": false` — its set predates this skill, built
by a 2-step tutorial that never attached the list. Every keyword is present, the
account reads `COMPLIANT` forever, and **no re-run will ever repair it** — the script
only creates attachments on the `NO_SET` path. The fix is one manual act (attach the
existing list in the UI, or a one-off CustomerNegativeCriterion call), verified the same
way the SKILL always ends: Admin → Account Settings → Negative Keywords actually shows
the keywords. Until that's done, those 131 negatives block nothing.

---

## Example 3 — Asks this skill should decline

**"Negate these 40 search terms from last month's report across the account."** Not this
skill. Query-report harvest is *evidence-driven* negation — individual queries judged on
performance, uploaded campaign-level, with a review gate built for volume. Route to
[`sqr-pipeline`](../sqr-pipeline/). The account-level baseline is for *categorical*
exclusions that hold for every campaign the account will ever run; filling it with SQR
residue turns a curated standard into a junk drawer nobody can audit.

**"Remove `affordable` from the Halstead list — turns out they want that traffic."** Also
not this skill, by invariant: it only adds. The removal is a deliberate act in the UI
(or a dedicated, separately-reviewed script), and worth a note in the portfolio's
baseline doc so next month's drift check doesn't quietly re-add the row — a re-run
*would* re-add it, because the baseline file still contains it. If Halstead is a
permanent exception, the durable fix is `--exclude-cid` on future rolls or a
portfolio-split baseline, per `rules.md`.
