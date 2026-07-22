# Rules — reading and triaging an audit run

Decision logic for what happens AFTER the script prints its severities.
`examples.md` has worked reads; `references/check-rubric.md` has per-check
criteria and the output contract; `SKILL.md` is the run guide.

## Invariants (never break these)

- **Read-only on Google Ads.** The audit never mutates an account — its only
  writes are the audit Sheet and (optionally, behind the interactive prompt)
  local chronic-issue files. Every fix is a separate step through the
  routing table below, with its own review gate.
- **The audit Sheet is the instrument's memory.** Run-over-run comparison,
  chronic detection, and the briefing feed all read what previous runs
  wrote. Don't hand-edit or prune the `History` / `Account History` tabs
  outside the documented archive maintenance — deleted rows rewrite trend
  truth, and edited rows corrupt every future comparison.
- **Severity ranks urgency class; count ranks effort.** An account's overall
  severity is its single worst check — one broken URL makes the account
  CRITICAL while forty AI assets leave it MEDIUM. Triage by check, not by
  the account label alone, and never read CRITICAL as "most issues."
- **Never overrule a finding — contextualize it.** If a flag matches a
  false-alarm class below, the count stays in the Sheet exactly as scored;
  your triage note explains why no action follows. Rewriting or suppressing
  results destroys the run-over-run comparison.

## Triage order

1. **CRITICAL checks, in exposure order:** disapprovals (ads not serving —
   spend and policy standing both at risk), broken URLs (live spend landing
   on dead pages), then CRITICAL inappropriate matches (discriminatory-
   exclusion phrases are legal exposure — for housing advertisers route to
   [`fair-housing-compliance`](../fair-housing-compliance/) alongside the
   copy fix).
2. **Chronic before new.** A 3+/90d tag means the fix isn't sticking —
   that's a process problem (regenerating automation, an upstream copy
   template, someone re-enabling a setting), not a copy problem. Fixing the
   instance a fourth time without finding the source is churn.
3. **NEW and INCREASED before SAME.** Something changed since the last run —
   find what (a new ad push, a setting flip, a site deploy) before it
   compounds. SAME + not chronic = known backlog; schedule it.
4. **HIGH structural before HIGH copy.** Automation opt-ins (auto-create ON,
   high-risk auto-apply) compound while you wait — Google keeps generating.
   Copy issues (DKI, seasonal, 5+ misspellings) are static until touched.
5. **MEDIUM batches into routine maintenance.** Nothing MEDIUM justifies an
   emergency.

**What each severity buys you:** CRITICAL = act today, it's costing money or
legal standing right now. HIGH = fix within the day; static-but-serious.
MEDIUM = this week's maintenance batch. OK = no action — but a nonzero
inappropriate count at OK severity still deserves a glance at the details
column (mild-category matches only; see the rubric).

## Reading the history tags

Tag mechanics live in the rubric; what they *mean* for triage:

- **FIRST_RUN** — no baseline exists. Everything looks new; report the
  findings, not "N new issues" (there's nothing to compare against). Note
  that a scope switch can also produce this (rubric: comparison is
  scope-bound).
- **NEW** — appeared since last run. Correlate with what changed:
  [`change-history-checker`](../change-history-checker/) shows who touched
  the account and when.
- **INCREASED** — the existing problem is growing; move it up a tier.
- **RESOLVED** — verify *fixed* vs *vanished*. Pausing an ad, a campaign
  losing ENABLED status, or a URL rotating out of the 20-URL sample all
  drop counts to zero without anyone fixing anything. Confirm the fix
  happened before reporting a win.
- **SAME** — the backlog. If it's been SAME for weeks on a HIGH account,
  expect it to surface as chronic soon; deal with it on your terms first.

## False-alarm classes — rule these out before acting

| Fired | Benign cause to rule out | Verify by | If benign |
|-------|--------------------------|-----------|-----------|
| Spelling flags on brand/coined words | Stylized spellings, coined amenity words, sub-brand nicknames aren't in the registry name (the only auto-loaded exceptions) | Does the word appear on the account's own website? | Add it to the `AD_COPY_EXCEPTIONS` block in the script header (a marked adaptation hook) — don't "fix" the copy |
| Spelling flags on lowercase stylized words | The proper-noun skip only catches Title-Case and ALL-CAPS forms | Same | Same |
| Auto-apply count is 0 but subscriptions exist | `OPTIMIZE_AD_ROTATION` is whitelisted by design | The rubric's whitelist note | Expected — not a blind spot |
| Seasonal flag on a current promo | The check has no calendar — it flags presence, not staleness ("summer special" in July still fires) | Promo end date with the owner | Keep the copy; carry the standing flag until the promo rotates. `limited time` / `this weekend only` are permanent-flag styles — accept the standing flag or change the copy style |
| Broken URL on a working page | Some servers reject HEAD requests (403/405) but serve the page fine; slow sites time out at 5s | Open the URL in a browser | Not broken — note it as a standing flag for that domain |
| Findings in assets no campaign uses | The DKI/seasonal/inappropriate/spelling asset scans read the whole library, linked or not | Asset linkage in the UI | Clean up the library at leisure, or accept the flag |
| Copy flags inside a campaign you paused | Seasonal/inappropriate/spelling/irrelevance filter **ad** status only; DKI/URLs/disapprovals require ENABLED at all three levels (rubric: scope asymmetry, by design) | Status of the named campaign | Fix at leisure — it isn't serving; expect old disapprovals to surface if you ever re-enable it |
| BRAND_MISSING HIGH on a `--cid` run | The account isn't in `accounts.json`, so its "name" is the placeholder `Account <cid>` — those literal words become the expected brand, and the spelling brand-shield is empty too | Is the CID in your registry? | Add the registry entry and re-run; the finding evaporates. Configuration fix, not a copy fix |
| RESOLVED tag with no fix shipped | Paused ad/campaign, or URL sampling (first 20) | Change history; what the "fix" actually was | Treat as vanished-not-fixed; re-check when reactivated |
| Blank briefing section | The reader shows the last 24h only — the audit didn't run, or ran `--dry-run` (which writes nothing) | The last `Audit Date` in `Account History` | **Blank = stale, never all-clear.** Run the audit |
| Inappropriate count > 0, severity OK | Matched terms outside the critical/high lists (spam/competitor starter rows) | The details column + the rubric's severity lists | Review the copy in the weekly batch; don't escalate the account |

## Chronic issues — what 3+/90d actually means

Chronic detection only scans HIGH/CRITICAL accounts and ignores `ai_assets`
(informational). A chronic tag means the same issue type has been present in
3+ audits inside 90 days — the question is never "how do I fix it again" but
"why does it come back":

- **Chronic auto-apply / auto-create** — someone or something keeps
  re-enabling it. Pull [`change-history-checker`](../change-history-checker/)
  for the actor before flipping it off a fourth time.
- **Chronic DKI / templates / spelling** — the upstream copy process keeps
  shipping the problem. Fix the template or the workflow that generates the
  ads, not just the live assets.
- **Chronic disapprovals** — the copy that gets written keeps tripping the
  same policy. The rewrite needs to change what's being said, not just
  resubmit it.
- **Chronic broken URLs** — the site changes under the ads. The fix is a
  process link between whoever deploys the site and whoever owns the ads.

The interactive account-file offer (the `echo "no" |` prompt — mechanics in
SKILL.md) is the memory surface for chronic accounts: say yes from a real
terminal when you want a per-account markdown dossier started.

## Routing table — where each finding goes next

Every route is read-only analysis or a human-gated change. Nothing executes
off the back of an audit without a human approving it.

| Finding | Route to |
|---------|----------|
| Disapproved / policy-limited ads needing rewrites | [`rsa-refresh`](../rsa-refresh/) (replace weak or non-compliant assets) or [`rsa-single-account`](../rsa-single-account/) (full rebuild for one account); all copy work under [`ad-copy-verification-standard`](../ad-copy-verification-standard/) + [`ad-copy-generation-framework`](../ad-copy-generation-framework/) |
| DKI in copy or assets | Same RSA family; [`rsa-bulk-edit`](../rsa-bulk-edit/) when the same DKI string repeats across many ads |
| Stale seasonal copy (confirmed stale, not a current promo) | [`rsa-bulk-edit`](../rsa-bulk-edit/) — find/replace the seasonal phrase at scale |
| Discriminatory-category inappropriate matches (housing) | [`fair-housing-compliance`](../fair-housing-compliance/) for the compliance layer, plus an immediate rewrite via the RSA skills |
| AI assets present / auto-create ON / URL expansion ON (checks 2, 6, 7) | [`pmax-asset-automation`](../pmax-asset-automation/) — campaign-level asset-automation opt-outs; for Demand Gen **ad-level** automation, [`dgen-automation-disable`](../dgen-automation-disable/) is the twin fixer |
| Auto-apply subscriptions enabled (check 8) | UI change (Recommendations → Auto-apply) — no API write path; list exactly which types to switch off |
| Broken URLs (verified real) | Landing-page/site fix, or a final-URL update — the ad edit is a gated mutation |
| Account health beyond creative | [`account-diagnostic`](../account-diagnostic/) — the 42-point full inspection |
| Ad-hoc verification pulls (which ads carry a phrase, where a URL is used) | [`google-ads-query`](../google-ads-query/) |
| Credentials / first-time API setup | [`google-ads-api-setup`](../google-ads-api-setup/) |

## Escalation default

When a finding is ambiguous — can't tell false alarm from real, a count
looks implausible, a RESOLVED tag has no fix behind it — report what you see
and verify against the live account before recommending anything. Never bulk-
rewrite copy from audit rows alone: the RSA skills exist precisely because
compliant replacement copy has to come from verified source material, not
from the audit's 40-character detail snippets.
