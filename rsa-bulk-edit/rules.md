# Rules — when bulk is right, and reading the sheet before Editor

Decision logic around a mechanical instrument. The script finds literal
text and writes a proposal sheet; every judgment — whether bulk is the
right tool, what the matches mean, what's safe to paste — is the
operator's. [`examples.md`](examples.md) has worked reads;
[`references/edit-contract.md`](references/edit-contract.md) has the exact
match/output mechanics.

## Invariants (never break these)

- **Preview instrument, not a mutation tool.** Nothing changes in Google
  Ads until a human posts the paste in Google Ads Editor. The sheet is a
  proposal; the Editor review screen is the last gate, and it is part of
  this workflow.
- **Literal text only — zero judgment in the replace.** The script applies
  your replacement to every substring match, in context or out. If the
  change requires reading the sentence it lands in, it is not bulk work
  (see the boundary below).
- **The script validates nothing.** No length checks, no casing
  adaptation, no meaning checks. A 34-character headline writes to the
  sheet as silently as a 24-character one. The review checklist below IS
  the validation layer.
- **All selected ads ship to the tab, matched or not** — filter on
  `Has Match`. And absence is not evidence: a failed account prints one
  console error and vanishes from the sheet entirely (contract
  §isolation).
- **Each run clears the tab.** Finish (or export) a review before
  re-running; use dated `--tab-name` values for history.

## When bulk is the WRONG tool

Route away before running anything:

| The ask | Why bulk fails | Route |
|---|---|---|
| "Make the ads sound better / more premium / rewrite the weak ones" | That's copy generation with performance context, not string replacement | [`rsa-refresh`](../rsa-refresh/) (existing ads, label-guided) |
| "Write ads for the new account" | Nothing to find-and-replace in | [`rsa-single-account`](../rsa-single-account/) |
| A swap that changes meaning per-context ("update all our service claims") | Each instance needs reading; substrings don't carry meaning | [`rsa-refresh`](../rsa-refresh/) under [`ad-copy-verification-standard`](../ad-copy-verification-standard/) |
| Replacement text introduces a **new claim** ("replace the promo customizer with '24/7 Towing Available'") | The mechanical swap works, but the claim itself needs verification first | Verify per [`ad-copy-verification-standard`](../ad-copy-verification-standard/), then bulk-edit the verified string |
| "Fix the text in our sitelinks / callouts / paths" | Headlines and descriptions are the only searched fields — paths are carried through untouched, and extensions are a different asset type entirely | Paths/extensions: Google Ads UI or Editor directly |

Writing genuinely new copy into slots is
[`ad-copy-generation-framework`](../ad-copy-generation-framework/)
territory — bulk-edit only ever moves text you already decided on.

## Pre-flight — before the first real run

1. **Dry-run first, always.** The match count is the cheapest sanity check
   you get (`--dry-run` previews the first 10 matched ads).
2. **Audit the search string for substring collateral.** No word-boundary
   mode exists: `car` hits `Carefree`, `special` hits `Specialists`. Short
   or common strings need lengthening with surrounding context (a space, a
   preceding word) or a case-sensitive pass.
3. **Plan the casing.** Case-insensitive matching inserts the replacement
   *exactly as typed* — Title Case portfolios need either
   `--case-sensitive` passes per casing variant (`Color`→`Colour`, then
   `color`→`colour`) or a post-write casing scan of every changed cell.
4. **Customizer intent check.** Replacing a whole `{CUSTOMIZER.X}` token
   with static text is a legitimate retirement move; matching text *inside*
   the braces corrupts the token. Search for the full token when a token is
   the target.

## Sheet review checklist — every run, before any paste

1. Filter `Has Match` = YES.
2. **Length-audit every changed cell** — headlines ≤30, descriptions ≤90.
   The script writes overflows unflagged; catching them here beats
   Editor rejecting them (or worse, trimming meaning) later. A helper
   column with `=LEN()` over the changed fields takes a minute.
3. **Casing scan** — look for lowercase replacements mid-Title-Case
   (the literal-replacement effect).
4. **Read the collateral** — scan `Changes Made` for fields you didn't
   expect (a `D2` hit when you were targeting headlines says the string
   lives in more places than you thought).
5. **Per-account paste discipline** — filter to one account, open that
   account in Editor, paste columns C→Z, review Editor's change preview
   (pasted rows carry no ad identity — contract §paste), post, next
   account.

## False-alarm table

| Signal | Likely cause | Verify by | Then |
|---|---|---|---|
| 0 matches but the text is visible in the UI | The ad/campaign holding it isn't ENABLED (paused anything is out of scope), or the text lives in paths/extensions (never searched), or `--case-sensitive` is on | The ad's status; which field the text sits in | Not a bug — adjust scope expectations, or edit those surfaces directly |
| Far more matches than expected | Substring collateral (`car` in `Carefree`) | Dry-run preview + `Changes Made` | Lengthen the search string; re-run |
| An account missing from the sheet | Its query failed — per-account isolation, console-only error | The `Querying {cid}...` block in the console | Fix access/CID, re-run; never read absence as "no matches there" |
| Replaced text is lowercase mid-headline | Case-insensitive match + literal replacement | The changed cells | Case-sensitive passes per variant, or fix cells in the sheet before pasting |
| Editor's preview shows changes on ads you didn't mean to touch | Unfiltered paste — non-matching rows went in too | What you copied vs the `Has Match` filter | Undo in Editor, re-paste filtered rows only |

## Escalation default

When you can't tell whether a swap is mechanical or editorial, treat it as
editorial and route it (boundary table). When a match count surprises you
in either direction, stop and read before re-running. And nothing gets
posted from Editor until the length audit has run — the script writes
over-limit text unflagged, so the sheet is the last place a length error
is still *your* problem instead of an import-time surprise.
