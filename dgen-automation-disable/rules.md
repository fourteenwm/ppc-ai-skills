# Rules — the dry-run read, when NOT to disable, and what the code does and doesn't prove

Judgment layer for a MUTATION skill. The two-step flow is only as safe as
the human read between the steps — this file is that read.
[`references/mutation-contract.md`](references/mutation-contract.md) owns
the exact selection/hash/write mechanics;
[`examples.md`](examples.md) shows worked runs.

## Invariants (never break these)

- **The dry-run READ is the safety layer.** The approval code proves one
  thing only: the account state at execute time equals the state you saw at
  dry-run time. It does not prove the change is right — that's the
  operator, reading the diff. Never execute against a diff nobody read.
- **Never skip the dry-run, never auto-approve.** The
  [`mutation-safety`](../mutation-safety/) pattern this skill implements:
  preview first, human decides, then execute with the code from THAT
  preview. A code from an old session or someone else's run is a re-read,
  not a shortcut.
- **Per-account atomic, per-batch resumable.** One failed account never
  stops the batch, and within an account the mutation is all-or-nothing
  (contract). Re-running after a partial batch is safe — already-fixed ads
  simply leave the pending set.
- **Read-only until a code is passed.** Dry-runs mutate nothing and write
  nothing — run them as freely as any audit.

## Reading the dry-run diff (before you approve anything)

Work the diff top to bottom; approve only when all five reads pass:

1. **Account count and identity.** Does `Accounts to process` match what
   you asked for — and did any `ERROR querying account …` line print? An
   erroring account silently leaves the pending set and the code; `All
   accounts are compliant` below an error line is the false-compliance trap
   (contract). Fix access/typos first (CIDs are used exactly as typed — a
   dashed CID is an error, not a match).
2. **Ad counts against your expectation.** A handful of ads per account is
   the normal shape. A surprisingly LARGE diff usually means a fresh
   creative launch just landed (new ads arrive `OPTED_IN` by default) —
   coordinate with whoever launched before flipping their week-one test.
3. **Settings-per-ad sanity.** Multi-asset ads fix at most 2 settings,
   video-responsive at most 3. The `Total settings to change` line should
   reconcile with the per-ad blocks — it counts settings, not ads.
4. **`GENERATE_LANDING_PAGE_PREVIEW` in the diff = a flag, not a default.**
   It ships OFF (contract, taxonomy). Seeing it `OPTED_IN -> OPTED_OUT`
   means a human or a Google-side change turned it ON — find out who via
   [`change-history-checker`](../change-history-checker/) (inside 30 days
   its detailed view names the actor) before overwriting their choice.
5. **`Settings to change` lines that aren't `OPTED_IN`.** The diff prints
   the current value verbatim; an `UNSPECIFIED -> OPTED_OUT` line is the
   same fix with a different starting point — fine — but note it, because
   it means the ad predates the setting's API surface.

## When NOT to disable

| Situation | Why you hold | Instead |
|---|---|---|
| The account has no uploaded video assets and relies on generated video | `GENERATE_VIDEOS_FROM_OTHER_ASSETS` is what's feeding DGen video inventory — opting out trades reach for control | Check the asset library first; if generated video carries real volume, get real video assets in place, THEN disable |
| Another manager or the client runs the account with you | The mutation silently overwrites their deliberate choice — automation ON is sometimes a decision, not an oversight | Coordinate; `change-history-checker` tells you whose choice it was |
| A creative experiment is mid-flight measuring automation impact | Flipping settings mid-test destroys the test | Wait for the test to conclude, or scope the run to other accounts |
| The diff is bigger or stranger than expected | You're about to approve something you don't understand | Investigate first (reads 2 and 4 above); the dry-run costs nothing to re-run |
| The client explicitly wants Google's auto-formats | Their account, their call — document it | Record the exception in your own account notes; exclude the CID from batch runs |

Portfolio default remains: managed accounts with brand standards run with
automation OFF — *Empty > Inaccurate*
([`ad-copy-verification-standard`](../ad-copy-verification-standard/)).
The table is the exception list, not the rule.

## The mismatch is a feature

`ERROR: Approval code mismatch.` means the account moved between your
dry-run and your execute — new ads, a Google-side re-enable, a colleague's
fix, or a different account list on the execute command. Never retry the
old code and never treat the mismatch as a bug:

1. Re-run the dry-run.
2. **Diff the diffs** — what appeared or disappeared since the last read is
   the interesting part (a new ad = launch landed; a vanished ad = someone
   else is working this account).
3. Re-read, re-decide, execute with the fresh code.

## Cadence

- **Post-onboarding:** once, after taking over any account with DGen
  campaigns.
- **Monthly drift re-run:** settings are observed to reset silently after
  certain campaign edits, and every new ad arrives with automation ON.
  The monthly dry-run costs nothing when clean.
- **After re-enabling paused campaigns:** paused campaigns were invisible
  to every earlier run (contract, selection) — the re-enabled campaign has
  never been fixed.
- **Before a brand-sensitive launch:** confirm nothing auto-generates right
  before new creative goes live.

## False-alarm table

| Signal | Likely cause | Verify by | Then |
|---|---|---|---|
| `All accounts are compliant` but an `ERROR querying account` line printed above | The erroring account was never audited — dropped from the pending set (contract) | The error line; the CID format (dashes are NOT stripped) | Fix the CID/access, re-run; never trust the summary over the error line |
| Approval code mismatch on execute | State drift since the dry-run — that's the design | Re-run the dry-run; compare diffs | Re-read, re-approve; never retry the stale code |
| Same settings back `OPTED_IN` a month after you fixed them | Known drift: certain campaign edits reset them; new ads default ON | Diff scope: new ads only vs. previously-fixed ads | Normal → monthly cadence. Previously-fixed ads re-flipped with no campaign edits → `change-history-checker`, find the actor |
| `--verify` printed nothing | Dry-run, already-compliant, or multi-account run — three silent no-op cases (contract) | Which of the three applies | For a no-mutation compliance check, use a dry-run, not `--verify` |
| `Warning: Could not log to Google Sheet` | Sheet logging failed — scope, sheet ID, or network | The JSONL row for the same account | Mutation stands (JSONL is the authority); fix the token scope or sheet ID for next time |
| `No DGen ads need fixing` on an account that definitely runs DGen | All its DGen campaigns are paused/ended, its ads are paused, or it's genuinely compliant | Campaign + ad status (the selection filters both; ended campaigns drop out) | If paused-by-season: re-run after re-enabling. If truly compliant: done |
| `Failed: N ads` count looks inflated | It counts every ad of each failed account, not settings, and the account is all-or-nothing | The per-account `ERROR executing mutation` line + the JSONL `success: false` row | Read the API error; fix cause; re-run — already-fixed accounts drop out automatically |
| Dry-run shows fewer ads than the account's DGen ad count | Carousel/Product ads have no automation settings; already-compliant ads don't queue; paused ad groups' ads DO queue but paused ads don't | The contract's selection rules | Expected — the pending set is "fixable and needing fix", not "all ads" |
| A code from yesterday refuses today with no visible change | Anything in the pending set moved — including an account dropping to an error today | Re-run the dry-run and read its error lines | Same as any mismatch: fresh read, fresh code |

## Escalation default

When the diff contains something you can't explain — settings ON that
nobody in your shop enabled, ads you don't recognize, a mismatch whose
delta makes no sense — STOP at the dry-run. Attribute first
([`change-history-checker`](../change-history-checker/); for access-level
questions, [`mcc-hack-audit`](../mcc-hack-audit/)), coordinate with
whoever owns what you found, and only then approve. An unexplained diff
approved anyway is exactly the failure the two-step flow exists to prevent
— the dry-run is free; un-mutating someone's deliberate config is not.
