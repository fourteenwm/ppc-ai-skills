# Rules — YouTube Placement Audit

Decision logic for reading flag output and deciding what actually gets
negated. Script mechanics live in
[`references/audit-contract.md`](references/audit-contract.md); the
workflow lives in [SKILL.md](SKILL.md).

## Invariants

1. **The sheet is a review surface, not a negate list.** Every row is a
   machine flag from substring matching — the trap table below is why a
   human (or an agent applying these rules) reads before anything is
   excluded. Blind-pasting 9,000 channels into exclusions WILL take out
   legitimate inventory.
2. **Nothing here touches Google Ads.** Both scripts are read-only against
   the account; exclusions are applied by you in the UI or Editor. There
   is no bulk-exclusion script in this folder to be careless with.
3. **A flag is a lead, not a verdict.** The reason string tells you *why
   the pattern matched*, not whether the placement is bad. The call
   belongs to the category table below.
4. **Check `Run Date` before acting on any tab.** A zero-flag run writes
   nothing and a zero-row tab is skipped (not cleared) — either way a tab
   can be showing last month (contract). Per tab, not per sheet.
5. **PMax zeros are an API limitation, not evidence of low harm.** PMax
   rows carry impressions only; clicks/cost/conversions print 0
   regardless of what actually happened. Triage PMax rows on impressions.

## Triage order for an audit read

1. **Run Date sanity** on all four tabs — is everything from this run?
2. **Coverage sanity** — the false-clean check. An account printing
   `No YouTube placements` while sibling accounts with the same campaign
   types return hundreds is a silently-failed account (contract:
   silent-swallow trap), not a clean one. Re-run it alone with
   `--filter` before certifying the portfolio.
3. **Keyword tab, worst first** — sorted by impressions already; work top
   down through the category table.
4. **NEA tab** — same, with the language judgment below.
5. **Build the exclusion list** from the Channels-to-Negate tabs **plus
   the channel-type rows pulled directly from the Bad tabs** — flagged
   channels bypass the extractor entirely (contract), and forgetting them
   is the most common gap in the final list.

## Reading the categories

| Category | Default call | The judgment |
|---|---|---|
| Kids content | Negate | Highest priority: brand-safety risk plus zero purchase intent — kids' autoplay loops generate huge impression counts. Also the biggest false-positive surface (`toy`⊂Toyota, `doll`⊂Dollar) — eyeball the channel name before it goes on the list. |
| Adult content | Negate | No debate. Verify nothing legitimate tripped the substring first. |
| Spam / Spam/Clickbait | Negate | Low-quality inventory; `1-800` catches call-harvesting content farms. |
| Legal | Negate for most brands | `dui` / `bail bonds` content is fine inventory only if that's literally your vertical. Watch `dui`⊂"Duisburg". |
| Gaming content | **Judgment** | The adult-gaming residue (`gaming`, `ninja`, `twitch` — the kids-gaming titles sit in Kids). A gaming audience can be a real buyer for some verticals; for local services it's almost always waste. Decide per client, not per run. |
| Non-English content | **Judgment** | This tab holds non-Latin **scripts** only — Spanish/French/German content never appears here (contract). English-only service area: negate freely. Multilingual market: review — an Arabic-script channel can still be a domestic audience you serve. |
| Null/Empty placement | Mostly informational | An unnamed placement can't be reviewed by name. If the row carries a URL, exclude by URL; if not, there's nothing actionable to exclude — it's a signal about inventory quality, not a work item. |

## When NOT to negate

| Situation | Call |
|---|---|
| Substring artifact on an on-vertical channel (a Toyota-review channel flagged `toy` for an auto-repair client) | Keep it — that may be exactly where your buyers are. The flag was the pattern, not the placement. |
| Gaming channel, gaming-adjacent product | Keep or test; don't reflex-negate your own audience. |
| Non-Latin-script channel in a market you actively serve in that language | Review with someone who reads it before cutting it. |
| A flagged row showing real conversions (Display/DGen rows carry them) | Investigate before negating. Kids-content "conversions" are usually accidental taps — still negate. A gaming channel converting for a parts brand might be earning its spend. |
| You want to stop ALL YouTube serving for a campaign | That's a campaign-settings/channel decision, not a placement-list project — don't build a 9,000-row exclusion list to approximate a checkbox. |

## False alarms

| Looks wrong | Actually |
|---|---|
| "Toyota Camry Reviews" flagged Kids content | `toy` substring. Keep or negate on merits, not on the flag. |
| "Dollar Store Hauls" flagged Kids content | `doll` substring. Same drill. |
| Account prints `No YouTube placements` but ran PMax all month | Likely the silent-swallow trap (contract) — all three queries can fail without an error line. Re-run that account alone. |
| Run says `No flagged YouTube placements found.` but the tabs have rows | Nothing was written this run; you're reading the previous run (Run Date). |
| NEA tab is empty but you know foreign-language placements exist | Latin-script languages are invisible to the check — that's the design boundary, not a failure. Add language-specific keywords via Customization if it matters. |
| Channels you saw flagged are missing from Channels to Negate | They were channel-type placements — the extractor only processes `/video/` rows. Pull them from the Bad tabs directly. |
| A known-bad channel shows only a handful of videos in the channel tab | Deleted/private videos don't resolve (`N not found` line) and a failed 50-video batch drops out silently — counts are floors, not totals. |
| PMax rows all show $0 cost | API limitation; the resource exposes impressions only. |
| `--nea-only --keywords-only` run "found nothing" | Both flags together select zero jobs (contract) — the run did nothing, by construction. |

## Customization judgment

Adding industry-specific keywords (SKILL.md § Customization) inherits
substring semantics: `crack` also matches "firecracker", a bare short word
matches everything containing it. Steal the ` sex ` trick — space-pad a
word (`' rom '`) to isolate it — and remember padded terms miss the word
at a name's start or end (contract). Test any list change with `--test`
against a few accounts before a full run. Keywords are matched against
the placement **name** only, never the URL.

## Cadence and escalation

- **Monthly** full run (SKILL.md's runtime table sizes it), plus a run
  after launching any new PMax or Demand Gen campaign — new campaigns
  find the junk inventory fastest.
- **Hundreds of kids-content placements on one account** is a targeting
  smell, not just an inventory problem — check the campaign's audience
  signals and content exclusions before assuming the list will fix it.
- **Negation is account mutation** — it happens in the UI/Editor today.
  If you script it, that script belongs under
  [mutation-safety](../mutation-safety/) discipline: preview, approve,
  execute, verify.
