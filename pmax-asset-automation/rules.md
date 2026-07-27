# Rules — PMax Asset Automation

Decision logic for reading audits and deciding what to flip. Script
mechanics live in [`references/audit-contract.md`](references/audit-contract.md);
the workflow lives in [SKILL.md](SKILL.md).

## Invariants

1. **A `[!]` row is a finding, not a work order.** The audit reports state;
   whether OPTED_IN is a problem is a judgment call this file owns. Some ONs
   are deliberate (table below) — flipping them without attribution can undo
   a colleague's or a client's decision.
2. **Absence of findings ≠ a healthy portfolio.** `All accounts fully
   compliant!` can print over an account that errored out of the run, and an
   account with no PMax campaigns is out of scope, not certified. Count
   account blocks against `Total accounts audited:` before reporting a
   portfolio clean.
3. **The fix is a mutation, and mutations follow
   [mutation-safety](../mutation-safety/).** Dry-run preview → explicit
   approval → execute → verify. Never batch-fix a portfolio on audit output
   alone — per-account dry runs, no exceptions.
4. **The default stance is all five OPTED_OUT.** Google's generated assets
   ship without per-asset approval, and the burden of proof sits on leaving
   automation ON, never on turning it off.

## Triage order for an audit read

1. **Error lines first.** Any `ERROR querying account ...` voids the
   summary's completeness — the errored account is unaudited (and still
   counted in `Total accounts audited:`). Resolve access and re-run before
   certifying anything.
2. **Count sanity.** Account blocks seen = accounts audited? Settings
   checked = 5 × campaigns reported? No-PMax accounts recognized as
   out-of-scope rather than clean?
3. **Then the `[!]` rows, worst first** (risk ranking below), each through
   the when-ON-is-legitimate table before any fix list is drafted.

## Which of the five matters most

Risk ranking when you can't fix everything at once:

| Rank | Setting | Why |
|---|---|---|
| 1 | **Image extraction from URLs** | Google pulls images from ANY page on the landing domain — including pages nobody would put in an ad. Least predictable, hardest to catch in review. Opt out even where you tolerate the others. |
| 2 | **Auto-created text** | Generated headlines/descriptions can contradict verified business claims — the exact failure mode the [ad-copy-verification-standard](../ad-copy-verification-standard/) exists to prevent (*Empty > Inaccurate*). |
| 3 | **Final URL expansion** | Traffic lands on pages you didn't choose, with auto-copy to match. Also the one most often ON *deliberately* — check before flipping. |
| 4 | **Auto-created videos** | Cuts both ways: on accounts with produced, brand-controlled video, OPTED_IN means Google may serve trimmed/remixed variants of creative someone signed off frame-by-frame — treat as priority. On accounts with NO uploaded video, OPTED_IN means Google may assemble a video from your other assets: an entire format entering rotation that nobody reviews. Either way it belongs OFF; which argument you make to the stakeholder differs. |
| 5 | **Auto image enhancement (cropping)** | Lowest blast radius — recrops of images you supplied. Still off by standard; last in line when triaging. |

## When OPTED_IN is legitimate (check before flipping)

| Situation | Call |
|---|---|
| High-volume ecommerce with thin creative and DATA showing text automation lifts performance | Leave `TEXT_ASSET_AUTOMATION` ON for that account — documented, with the evidence linked. Audit still reports it; you carry the exception knowingly. |
| URL expansion used deliberately to widen PMax reach | Legitimate strategy: opt out of text automation only, keep expansion ON — and commit to reviewing the expanded-URL set on a cadence. |
| A running experiment someone set up | Don't end a test mid-flight by "fixing" its variable. Attribute, ask, then decide. |
| The account is co-managed (client has UI access, another agency, in-house team) | The mutation would silently overwrite someone else's deliberate choice. Coordinate before flipping — same discipline as any shared-management account. |
| All five ON on a brand-new campaign | Usually nobody ever configured it (Google's defaults), not sabotage. Confirm via change history, then fix as routine setup. |
| You can't explain WHY it's ON | That is not a green light — it's the trigger for the escalation ladder below. |

## False alarms and traps

| Symptom | What it actually is |
|---|---|
| `All accounts fully compliant!` after an `ERROR querying account` line | False compliance — the errored account was never audited. The error line is the only trace (invariant 2). |
| `No PMAX campaigns found` counted as a win | Vacuous compliance — out of scope, not clean. Matters when someone later launches PMax there. |
| `OPTED_IN` on a setting nobody remembers touching | The audit seeds absent settings to OPTED_IN (Google's default) — "explicitly on" and "never configured" print identically. Change history separates them. |
| A PAUSED campaign full of `[!]` rows | Real, but dormant — the settings bite when it re-enables. Fix before re-enabling rather than treating as live-fire. |
| Same account twice in the summary with doubled counts | `--cids` does not dedup — you listed the CID twice. |
| `- CID 1234567890 (1234567890)` name/CID redundancy | Display rule, not a bug — `--cid`/`--cids` runs have no registry, so the name IS the CID. Only `--all` shows real names. |
| Settings compliant yesterday, OPTED_IN today with no change-history actor | Google has been observed re-enabling automations after certain campaign edits. This is WHY the audit has a cadence — re-audit, re-fix, and log it. |
| A sixth automation type you know exists isn't in the report | The audit's scope is fixed to the five listed types — anything newer is invisible until the script's list is extended (contract § fixed scope). |

## Escalation ladder for an unexplained OPTED_IN

Cheapest discriminating check first:

1. **Date and attribute the flip** — [change-history-checker](../change-history-checker/)
   (who changed it, when, via UI/API; note its 90-day window). Creation-date
   settings with no later edits = default-config case, fix freely.
2. **Ask the human it points to** before touching a co-managed account.
3. **Fix via the mutation pattern** (SKILL.md § fix) under
   [mutation-safety](../mutation-safety/) — dry run, approval, execute.
4. **Re-audit next day** to confirm the settings stuck; redirect both runs
   to files so the before/after pair is on disk (the audit itself writes
   nothing).

## Cadence

- **New account / new PMax campaign:** audit immediately after creation —
  and after every [pmax-builder](../pmax-builder/) Editor import (the CSV
  bakes the opt-outs; the audit proves they landed).
- **Monthly:** portfolio-wide `--all` pass — catches Google's silent
  re-enables and teammates' UI changes.
- **Client handoff:** audit before taking over; the report is the baseline.
- **24h after any fix:** verification re-run.
