# Decision Rules — Account-Level Negative Keywords

The judgment layer: what belongs in an account-level baseline, when this skill is the
wrong altitude, and how to read the script's output without being misled. Script
mechanics live in `references/mutation-contract.md`; worked reads in `examples.md`.

---

## Invariants

1. **Two passes, a human between them.** Dry-run (or code generation) and execution are
   separate invocations by design — per the [`mutation-safety`](../mutation-safety/)
   protocol, never chain `--execute` and `--execute --approval-code` in one breath. The
   preview exists so a person reads the plan before anything mutates.
2. **This skill only adds.** It never deletes a keyword, never removes a SharedSet, never
   detaches a list. Removals are a deliberate, separately-gated act you perform outside
   this skill (UI, or a dedicated script you write and review on its own).
3. **PHRASE match, account-wide, no end date.** Every row you add blocks *any query
   containing that phrase, in every campaign, in every future campaign, until someone
   remembers to remove it*. That blast radius is the standard every candidate keyword
   must pass — not "is this query usually bad" but "is this phrase wrong for this entire
   account, categorically."
4. **A baseline is curated, not copied.** The shipped 131-row sample is one portfolio's
   battle-tested list for conventional market-rate property management. Rows like
   `high point` (harmless generically, catastrophic for an account that serves High
   Point, NC) show that baselines encode portfolio-specific assumptions. Review every
   row against *your* portfolio before the first roll.
5. **Error lines invalidate the categorization below them.** A `Layer N query error:`
   above `-> NO_SET` means the script couldn't see the account, not that the account has
   no list. Executing that plan can create a duplicate set. Fix access, re-run, then
   trust the preview.

---

## Baseline curation — what earns a row

Every row must be wrong for **every campaign in every account** the baseline will touch.
The shipped sample illustrates the classes that tend to pass that test for a
conventional rental portfolio:

| Class | Shipped examples | Why account-level fits |
|---|---|---|
| Wrong product entirely | `for sale`, `rent to own`, `mobile homes`, `hotel`, `roommate`, `sublet`, `nightly` | The account never sells this, anywhere |
| Disqualifying-screening intent | `no credit check`, `bad credit`, `eviction`, `felony`, `second chance` | Searcher self-describes as failing standard screening |
| Payment/subsidy model not accepted | `section 8`, `voucher`, `subsidized`, `income based`, `dss accepted` | A program the portfolio doesn't participate in |
| Price-floor mismatch | `cheap`, `$300 apartments`, `low rent`, `below market rate` | Below the portfolio's floor in every market |
| Job seekers, not renters | `employment`, `internship`, `intern` | Different intent, zero lease value |
| Platform/classifieds noise | `craigslist`, `greensheet`, `gosection8`, `private landlords`, `by owner` | Searcher wants a channel or landlord type the portfolio isn't |
| Existing residents | `resident portal`, `rental verification` | Service traffic, not acquisition traffic |

The test that matters is the **exceptions sweep**: walk the accounts the roll will touch
and ask which rows stop being categorically wrong. One 55+ community makes `senior`,
`retirement`, and the five `55 *` rows lethal for that account. One all-bills-paid
property flips `utilities included` from noise filter to demand filter. One
affordable-housing property makes `affordable` a self-inflicted outage. The fix is
almost never "ship a weaker baseline" — it's `--exclude-cid` for the exception account
(its exclusions belong at campaign level) or, if exceptions pile up, splitting the
portfolio into two baselines.

Formatting rules for your own file: lowercase, one keyword per line, no match-type
punctuation — the script applies PHRASE itself, and its presence check is exact-string
and case-sensitive, so a `Careers` row re-reads as "missing" forever next to Google's
stored lowercase form.

---

## When account-level is the wrong altitude

| Situation | Wrong move | Right move |
|---|---|---|
| Term is bad for most campaigns but bid deliberately in one (e.g. `cheap` under a budget-property campaign) | Baseline row | Campaign-level negatives in the other campaigns |
| Term appears inside a **positive keyword** somewhere in the account (`affordable` vs a bid on `affordable apartments near [city]`) | Roll and let them fight — the negative wins and the positive silently stops serving | Resolve the strategy first: either the bid is wrong or the row is; then scan with [`neg-conflict-finder`](../neg-conflict-finder/) |
| Terms that are merely *statistically* wasteful (high spend, no conversions) | Padding the baseline with query-report harvest | That's [`sqr-pipeline`](../sqr-pipeline/) territory — evidence-driven, campaign-level, with its own review gate |
| Seasonal or temporary exclusion | Account-level row you'll forget to remove | Campaign-level negative with a calendar note |
| Competitor names | Quietly negating them portfolio-wide | A strategy decision made explicitly — many accounts *bid* on competitor terms |
| One account's product differs from the portfolio (age-restricted, student, affordable) | Shipping it the standard baseline anyway | `--exclude-cid` that account; handle it campaign-level |

Property-management portfolios: curation calls around age, family status, and income
terms carry Fair Housing implications in both directions — load
[`fair-housing-compliance`](../fair-housing-compliance/) before deciding those rows.

---

## Conflict awareness — before and after

- **Before the first roll into an account:** pull its positive keywords (a
  [`google-ads-query`](../google-ads-query/) keywords pull is enough) and grep them
  against the baseline rows. Any positive *containing* a baseline phrase will be blocked
  account-wide the moment the roll lands.
- **After any roll:** run [`neg-conflict-finder`](../neg-conflict-finder/) across the
  touched accounts. It finds every place a negative blocks a positive — including
  conflicts that predate this skill.
- The single most common conflict class in rental portfolios is a generic baseline row
  (`housing`, `senior`, `affordable`) colliding with a deliberately-bid niche
  (`student housing`, `senior apartments`, `affordable luxury`). The baseline is usually
  right for the portfolio and wrong for exactly one account — exclude, don't dilute.

---

## False alarms and traps

| Looks like | Actually is | Check |
|---|---|---|
| `member_count: 0` on the set after a successful run | API quirk — the field always reads 0 | The script already re-queries criteria directly; trust the preview's delta on the next run |
| `reference_count: 0` | Same quirk, attachment edition | CNC existence (layer 3) is the real check |
| `-> NO_SET` on an account you're sure has a list | A swallowed layer-1 query error one line above | Never execute past a `Layer N query error:`; fix access and re-run |
| `COMPLIANT` treated as "fully healthy" | Layers 1-2 only — the attachment is **not** part of the verdict | `"cnc_attached"` in the session JSON; a `false` needs a manual fix, re-runs never repair it |
| The same keywords re-listed as missing every run | Case/spacing mismatch between your file and Google's stored form | Lowercase the baseline file |
| A short name resolving to the wrong account | Substring matching — first book match wins silently | Use full names, aliases, or CIDs |
| A typo'd CID sailing through resolution | Unknown all-digit tokens are accepted as raw CIDs | Read the resolved-account lines in the preview, not just the totals |
| `WARNING: Could not resolve: ...` then a smaller batch | Non-fatal drop of name tokens | Fix the names; the run continued without them |
| `WARNING: Sheet log failed` after an `OK` line | Logging hiccup, not a mutation failure | The local JSONL row is the record; the mutation stood |
| An old approval code "still working" | Codes never expire — it executed the **old snapshot** | Generate a fresh code after any account or baseline change |

---

## Escalation defaults

- **Unsure about a row → leave it out.** Adding a keyword later is one safe re-run;
  un-negating is a manual act this skill refuses to do.
- **A huge `Add` count on a portfolio you believed compliant** → suspect the inputs
  before the accounts: a shadowing keywords file in your working directory, or layer-1
  finding a different set than you expect. The `Loaded N baseline keywords` line and the
  per-account `SharedSet <id>` reasons are the tells.
- **Blocked-positive conflicts found post-roll** → that's a strategy decision, not a
  mechanical fix. Surface it; don't silently delete either side.
- **Monthly-ish re-runs are safe and useful** — against a compliant portfolio the whole
  run is a no-op, and any `PARTIAL` that appears is your drift detector.
