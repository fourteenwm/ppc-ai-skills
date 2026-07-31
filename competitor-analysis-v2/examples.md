# Worked Examples — Competitor Analysis v2

Three reads. All businesses, URLs, and scores are synthetic (`*.example.com` domains
throughout); console excerpts are derived from `scripts/screenshot.cjs`'s own output
statements, with long error text trimmed to its first line. Judgment: `rules.md`.
File authority and numbering: `references/workflow-contract.md`.

---

## Example 1 — Full engagement, both outputs (auto repair)

**Ask:** "Run competitor analysis for Gearline Auto Repair — both outputs."

**Phase 1, the slot test.** Gearline's owner lists seven names they think of as
competition. The five-slot budget (`rules.md`) sorts them:

| Candidate | Verdict |
|---|---|
| Redline Automotive | ✅ Same services, same metro, on their lose-deals-to list |
| Summit Auto Care | ✅ Lose-deals-to list, actively running ads |
| Ironwood Auto Works | ✅ Same market, premium positioning — sharpens the map |
| Beacon Automotive | ✅ Same market, budget positioning — other end of the map |
| Milepost Motors | ✅ Same customer, heavy local advertiser |
| An auto-repair directory site | ❌ Aggregator — nobody chooses between it and Gearline |
| A shop two towns over | ❌ Different market; they've never lost a deal to it |

Both exclusions get one line in the gift's "Who we looked at" section.

**Phase 2, screenshots — client first in the URL order:**

```
node .claude/skills/competitor-analysis-v2/scripts/screenshot.cjs \
  https://gearline.example.com https://redline.example.com https://summit.example.com \
  https://ironwood.example.com https://beacon.example.com https://milepost.example.com \
  --output ./deliverables/gearline/screenshots
```

```
Capturing 6 screenshots...
Output folder: ./deliverables/gearline/screenshots

[1] Navigating to: https://gearline.example.com
[1] Saved: deliverables/gearline/screenshots/1-gearline-example-com.png
[2] Navigating to: https://redline.example.com
[2] Saved: deliverables/gearline/screenshots/2-redline-example-com.png
[3] Navigating to: https://summit.example.com
[3] Saved: deliverables/gearline/screenshots/3-summit-example-com.png
[4] Navigating to: https://ironwood.example.com
[4] Error capturing https://ironwood.example.com: page.goto: Timeout 30000ms exceeded.
[5] Navigating to: https://beacon.example.com
[5] Saved: deliverables/gearline/screenshots/5-beacon-example-com.png
[6] Navigating to: https://milepost.example.com
[6] Saved: deliverables/gearline/screenshots/6-milepost-example-com.png

Retrying 1 failed URL(s) with bot evasion...
[4] Navigating to: https://ironwood.example.com (retry with evasion)
[4] Saved: deliverables/gearline/screenshots/4-ironwood-example-com.png

==================================================
Screenshots captured: 6/6
```

The read: Ironwood's bot protection beat the plain headless pass; the built-in headful
retry got it. `6/6` on the summary line — the line that matters, since a partial run
would still have exited 0 — and `screenshots.json` records `"retried": true` on entry 4.

**Phase 3, extraction — and the thin-fetch catch.** Six parallel agents return XML.
Beacon's profile comes back with `social_proof` empty — but screenshot
`5-beacon-example-com.png` clearly shows a 4.7★ review badge in the hero. That's the
fetch artifact from `rules.md` (JS-rendered element the fetch missed), not a real gap. A
re-fetch fills it. Recording "Beacon shows no social proof" would have handed the client
a false opportunity.

**Phase 4 — ads for 3 of 5.** The owner pastes SERP ads for Redline, Summit, and
Milepost. Strategic + tactical passes (attributes and bands per the two prompts) land
Redline strongest overall with Summit mid-pack, and one pattern across all three sampled
ads: zero promotional hooks and zero quantified proof. Phrased exactly that way in the
outputs — "of the three ads we analyzed" — per the small-sample rule.

**Phases 5-6 — gaps, then the verification gate.** The messaging matrix makes
`family owned` and `free estimates` table stakes (3+ claim them); Redline alone owns
`same-day service`; nobody claims financing, loaner cars, or text-message status
updates. Five candidate gaps go to verification against gearline.example.com:

| Gap | Verdict | Evidence |
|---|---|---|
| Financing | ✅ | "0% financing for 12 months" — /financing |
| Loaner cars | ✅ | "Free loaner cars on repairs over 4 hours" — /services#loaners |
| Text status updates | ❌ | Not found anywhere on the site |
| Master-certified techs | ❌ | "experienced technicians" only — implied ≠ explicit |
| Review volume (612 reviews, 4.8★) | ✅ | Homepage badge + /reviews |

**Angles.** Three verified angles, priority-ordered by the angle prompt's criteria; the
brief's "Angles NOT to Pursue" table gets `same-day service` (Redline owns it;
Gearline's site doesn't promise it) and `cheapest in town` (race to the bottom, and
Beacon owns budget). The two ❌ gaps land in "Cannot Recommend" with next steps ("ask
about the text-update system — if it exists, it's whitespace").

**Phase 7-8.** Client Gift PDF (strategy only, zero ads mechanics) + one-page brief. The
brief then feeds the actual RSA build via `ad-copy-generation-framework` — its 30-char
headline sketches are the input to that build, not the build itself.

---

## Example 2 — Gift-only for a property-management client, no ads available

**Ask:** "Client gift for Fernbrook Pointe" (a managed apartment community).

Output = Client Gift only, so per the contract's run table: phases 1-3, 5-8 — and
Phase 4 drops out anyway because nobody has competitor ad copy for this market. The
workflow's honest skip note goes in the report ("Ad analysis not performed — no
competitor ads provided"); website intelligence carries the gift.

Two judgment beats worth showing:

- **The numbering translation, live.** After verification, `client-verification.md`'s
  output ends "Next Step: Proceed to Phase 5 (Angle Development)." A cold reading of the
  SKILL's map would go to *Gap Identification* (workflow Phase 5) — already done. The
  contract's table decodes it: the prompt's "Phase 5" is angle development, which serves
  the *Ads Brief only* — and this engagement is gift-only, so the actual next step is
  Phase 7. Translate and move on; the prompt's sequence was right, its label is v1.
- **Fair Housing gates an opportunity.** The emotional-landscape pass shows every
  competitor selling amenities while nobody speaks to commute convenience. That's the
  gift's headline opportunity — and because any audience-flavored positioning for
  housing carries Fair Housing exposure, the recommendation is phrased around the
  *property attribute* (walk-to-transit location), never around who should want it,
  with [`fair-housing-compliance`](../fair-housing-compliance/) loaded before writing
  the recommendations section.

Delivery uses the property-management framing and email template from
`sales/service-page-copy.md` — "no action required, just wanted to share what we're
seeing in the market" — because the gift's job here is retention, not upsell.

---

## Example 3 — The ask this skill declines

**Ask:** "What are Redline and Summit spending on Google Ads per month?"

Declined, by invariant: this skill reads public surfaces — websites, screenshots, ad
copy you provide. It has no access to competitor spend, impression share, or auction
data, and estimating spend from ad presence would be exactly the kind of unverifiable
claim the verification phase exists to kill. What it *can* deliver about Redline and
Summit: what they say, how they position, where their messaging is weak, and which of
those weaknesses the client can verifiably exploit — the analysis from Example 1. If
auction-competitiveness data matters, that conversation belongs in the client's own
Google Ads account surfaces (Auction Insights), outside this skill.
