# Decision Rules — Competitor Analysis v2

The judgment layer: who earns one of the five analysis slots, what screenshots can and
can't tell you, and how to choose angles across the seven prompts. Stage methodology
lives in `prompts/` (the authority map and numbering translation are in
`references/workflow-contract.md`); worked reads in `examples.md`.

---

## Invariants

1. **Verification is the law, not a phase.** No claim reaches either output without
   explicit client-website evidence and a source citation
   (`prompts/client-verification.md` owns the rules). A brilliant gap the client can't
   prove is a dead gap. This is the
   [`ad-copy-verification-standard`](../ad-copy-verification-standard/) applied
   end-to-end.
2. **The Client Gift carries zero Google Ads mechanics.** Strategy, positioning,
   opportunities — never CPCs, Quality Scores, or campaign anatomy. The brief is where
   practitioner material goes, and the brief never goes to the client.
3. **Public surfaces only.** This skill reads websites, ads you provide, and screenshots.
   It cannot see competitor spend, impression share, or auction data — decline asks that
   require them rather than estimating.
4. **Point-in-time, not monitoring.** The deliverable is a dated snapshot. Re-running
   quarterly is a new analysis, not an update feed.
5. **Client first in URL order.** Screenshot index 1, matrix row 1, positioning-map
   anchor — every downstream surface assumes the client leads the list.
6. **Prompts are the authority — route, don't restate.** When a prompt's internal phase
   label contradicts the SKILL's 8-phase numbers, translate via the contract's table and
   keep moving; never edit a prompt mid-engagement.

---

## Which competitors earn a slot

Five slots is a budget, not a quota. The test for each candidate:

| Earns a slot | Fails the slot test |
|---|---|
| Sells the **same service** in the **same market** to the **same customer** | Aggregators and directories (they rank, but nobody chooses between them and the client) |
| Appears in the client's "we lose deals to them" list — the highest-signal source | Marketplaces / lead brokers — different business model, useless messaging comparison |
| Actively marketing: live site with real messaging, ideally running ads | A dormant site last touched years ago — nothing current to learn |
| Beatable-or-matchable economics | A national brand whose scale the client can't answer — at most **one**, included deliberately as a reference point and labeled as such |
| A genuinely different positioning worth mapping (one premium or one budget player sharpens the map) | The client's own sister brand, or a franchisor's corporate site when the client is a franchisee |

Operational rules:

- **Ask for the lose-deals-to list before searching.** The client's sales reality beats
  any SERP. If they have no list, run the SKILL's search flow (8-10 candidates →
  present → approve 5).
- **An honest 3 beats a padded 5.** Thin markets exist; say so in the report rather than
  padding slots with aggregators — padding dilutes every "3+ competitors claim X"
  table-stakes count downstream.
- **Note what you excluded and why.** One line in the gift's "Who we looked at" section
  preempts the client's "why isn't X here?"

## Screenshot reads — what the image is for

Screenshots answer questions extraction can't, and vice versa. Don't cross the streams:

| Read from the screenshot | Read from the extraction XML |
|---|---|
| Above-the-fold hierarchy — what a visitor actually sees first | Full messaging inventory, services, claims |
| Visual tier (design era, polish, photography) → evidence for the `positioning tier=` call | The stated positioning language |
| Trust-signal *placement* (badges above fold vs buried footer) | Trust-signal *existence* |
| Offer prominence (hero banner vs buried link) | Offer terms |
| Cross-competitor gestalt for the gift's 3×2 grid | Everything quotable — **never quote copy off a screenshot; extraction owns text** |

Failure handling, in order: the script already retried headful with a real user agent
(contract § retry pass). If a site still failed — check `Screenshots captured: X/Y` and
`screenshots.json`, **not the exit code, which is 0 on partial failure** — proceed with
extraction-only for that competitor, say so in the report, and never describe a visual
you don't have. A thin *extraction* on a JS-heavy site is the mirror trap: an empty XML
field can be a fetch artifact rather than a real gap — cross-check against the
screenshot (which renders JS) before recording "no social proof shown" as a finding.

## Angle selection across the seven prompts

The prompts own their mechanics; these are the operator calls between them:

- **Verification strength beats gap value.** A HIGH-priority gap with implied evidence
  loses to a MEDIUM gap with an explicit quote. The angle prompt's own priority criteria
  assume verified inputs — feed it nothing marginal.
- **Small-sample honesty.** Strategic/tactical scores rank *the five ads you were
  given*, not the market. "All competitors miss social proof" means all *sampled* ads
  did — phrase gift and brief claims accordingly ("of the five we analyzed…").
- **Table stakes before whitespace.** If the client is missing a 3+-competitor
  table-stakes claim, fixing that usually outranks any exotic whitespace angle — the
  gap prompt surfaces both; sequence them yourself.
- **Compliance can demote a quick win.** A "quick win" angle that leans on superlatives,
  guarantees, or (for property management) anything audience-flavored takes the brief's
  compliance watch-outs first; a slower, safer angle may ship first. PM clients: load
  [`fair-housing-compliance`](../fair-housing-compliance/) before writing a single
  angle.
- **The brief's headlines are sketches, not the build.** Angle development produces 3
  headline concepts per angle at 30 characters — enough to brief a build, not an RSA.
  The full 15-headline build routes to
  [`ad-copy-generation-framework`](../ad-copy-generation-framework/) and
  [`rsa-single-account`](../rsa-single-account/) with this brief as input.
- **"Cannot recommend" is a deliverable.** The verified-out list (with why) is often the
  most trusted section of the brief — never trim it to look more complete.

## False alarms and traps

| Looks like | Actually is | Check |
|---|---|---|
| Screenshot run "succeeded" (exit 0) | Partial failure — exit 0 covers 3/6 | The `Screenshots captured: X/Y` line + `screenshots.json` |
| 5 screenshots from a 6-URL command, no error | A schemeless URL silently dropped by the http-prefix filter | Every URL starts with `https://` |
| Output landing in `/tmp/competitor-report/screenshots` despite your `--output` | A typo'd flag silently ignored, value dropped | Spelling: `--output` |
| Retry pass crashing on a server | Headful retry needs a display | Run capture on a desktop, or accept extraction-only |
| A competitor with "no social proof" in the XML | Possibly a JS-rendered element the fetch missed | Cross-check the screenshot before recording the gap |
| A prompt telling you to "proceed to Phase 5" that isn't the SKILL's Phase 5 | v1 internal numbering | Contract § numbering translation — sequence is right, labels are old |
| "22 attributes scored" missing from a run | Phase 4 legitimately skipped — no ads were available | The workflow's skip note; website intelligence carries the gift |
| Two prompts sharing one worked example | Deliberate — same ad, same client chain (contract § cross-file facts) | Not duplication to "fix" |

## Escalation defaults

- **Client website can't support their own differentiators** → pause before Phase 7 and
  talk to the client; a brief where verification killed 4 of 5 angles is a website
  problem, not an ads problem. Don't pad — say it.
- **Verification contradicts what the client told you** ("we're the only 24/7 shop" —
  site says business hours) → surface the contradiction in the deliverable's
  cannot-verify list; never silently side with either source.
- **Every credible competitor is national scale** → question the targeting with the
  client before analyzing; the report would map a fight the client shouldn't pick.
- **The ask is spend/budget intelligence** → out of scope by invariant 3; offer the
  positioning analysis this skill actually does.

## Cadence

Quarterly per managed client is the natural rhythm (markets move slowly); always before
a major copy rebuild (the brief is the rebuild's input); immediately when a client
mentions a new competitor by name — that one is never a false alarm.
