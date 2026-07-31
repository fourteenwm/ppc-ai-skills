# Rules — Geo Conflict Analyzer

Decision logic for reading PASS/FAIL output and separating real conflicts
from noise. Script mechanics live in
[`references/analysis-contract.md`](references/analysis-contract.md); the
classification rules the model applies live in [prompt.md](prompt.md) —
that file is the runtime ruleset, this file is how a human reads its
output.

## Invariants

1. **FAIL is a protection, not an accusation.** A FAIL means "negativing
   this query would collide with a geo you actively bid on" — the query
   stays live and comes OFF the negative list. That's the skill doing its
   job, even when the query looks like junk.
2. **PASS means geo-safe, not "should be negatived."** The intent decision
   (is this query worth blocking?) happened upstream in classification —
   this check is the last safety gate before upload, not the
   decision-maker. A PASS on "san diego apartments" tells you negativing
   it won't break targeting; whether to block metro-level traffic is
   strategy, not geo-safety.
3. **The cost asymmetry runs one way.** Wrongly negativing an active geo
   silently blocks live traffic — expensive and hard to notice, because
   the account just goes quiet in that area. Wrongly keeping one junk
   query costs a few clicks. That asymmetry is why prompt.md rule 5 says
   default to FAIL when in doubt, and why you honor FAILs even when they
   look over-cautious.
4. **Column H is the ground truth the model sees.** The check is only as
   current as the geo lists in the sheet — retire an ad group without
   updating column H and the model keeps FAILing queries that are now
   safe to negative. Refresh the lists when campaign structure changes.
5. **Flip Status yourself after each accepted batch.** The script never
   writes the input tab (contract) — skip the flip and the next run
   re-spends the same OpenAI call and appends duplicates.

## Reading verdict + confidence together

| Verdict | Action |
|---|---|
| FAIL / HIGH | Off the negative list, no discussion. This is the save the skill exists for. |
| FAIL / MEDIUM or LOW | Verify before honoring blindly: is the named `Conflicting_Geo` still an active ad group? If the geo list is stale (invariant 4), fix the list and re-run rather than overriding by hand. |
| PASS / HIGH | Geo-safe. Proceed with whatever the upstream classification said. |
| PASS / MEDIUM | Skim — usually a partial token overlap the model resolved sensibly. |
| PASS / LOW | **Manual read mandatory before upload** — the console's `[!]` line exists for exactly these. The property-name-vs-geo ambiguity lives here. |
| Confidence `N/A` | The model returned 4-column rows (contract fallback) — verdicts are usable, but treat every row like MEDIUM at best. |

## Real conflict vs noise — the classes you'll actually see

| Pattern | What it is | The call |
|---|---|---|
| Query matches an active geo with fuzzy variation (typo, preposition, modifier, plural) | **Real conflict.** The typo query IS live traffic reaching your broad/phrase keywords — a phrase negative built from it blocks that traffic. | Honor the FAIL. |
| Query names a *different directional slice* of a geo you target specifically (active "West Chula Vista", query "east chula vista apartments") | **Real, but not a negation question.** The account's granular geo structure treats sibling slices as live inventory decisions. | Honor the FAIL — and treat it as an *expansion candidate* (maybe that slice deserves its own ad group), not a query to fight over. |
| Query token could be a neighborhood OR a property/brand name ("westgate manor apartments") | **The classic noise case.** The model flags it MEDIUM/LOW because it can't know your market's proper nouns. | Resolve by hand: check the geo list, then a map/brand search. Property name → the PASS stands; what to do about a *competitor* name is brand policy, not geo policy. |
| Client operates in a geo that isn't in column H (presence without targeting) | **Not a conflict by definition.** The check protects *targeting*, not footprint — PASS is correct. | If the geo should be targeted, that's a build conversation. Don't hand-edit verdicts to encode strategy. |
| Query names a broader region than any target ("san diego apartments" over a Chula Vista ad group) | **PASS by design** — broader ≠ the target. | Geo-safe; the metro-traffic decision is upstream's. |

## Operational rules

- **Count check every run:** `Found N pending` vs `Parsed M results`. A
  small gap = malformed model rows; they're still Waiting and retry next
  run — don't hand-enter them. A large gap (half the batch) = output
  truncation; lower `--batch-size` (the 4,000-token output cap,
  contract).
- **Verify both tabs exist before a paid run.** A mistyped
  `--output-tab` fails *after* the OpenAI call; `--dry-run` won't catch
  it because dry runs skip the write entirely (contract).
- **Batch size is a cost/reliability dial, not a throughput dial.** One
  run = one model call; 500 rows means ten runs at 50, not one run at
  500 (truncation risk).
- **Dedupe before uploading** if there's any chance a batch ran twice —
  duplicate CID+Query pairs in the output tab are the tell (no run-date
  column exists; position is the only ordering).

## Escalation defaults

- **The model contradicts what you know about the account** → trust the
  account: override that row manually, then consider whether the case
  belongs in prompt.md as a new worked example. prompt.md is a runtime
  dependency — edit it, test with `--dry-run`, and know that every
  future run inherits the change.
- **A LOW-confidence storm on one CID** (many LOWs in one account) →
  suspect the column H list before suspecting the model: wrong
  delimiter, empty entries, or property names mixed into the geo list.
- **Rows that never process** run after run → empty column H (silent
  skip, contract) before anything else.
- **Verdicts feel systematically too strict** → that's the designed
  default-to-FAIL bias (invariant 3). Loosening it means editing
  prompt.md's rule 5 — a deliberate, tested change, not a per-row
  override habit.
