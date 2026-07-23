# Worked Examples — rsa-single-account

Three runs read end-to-end. All names, CIDs, and figures are synthetic; console excerpts
follow the scripts' real output formats. The judgment applied here comes from
[`rules.md`](rules.md); exact mechanics from
[`references/pipeline-contract.md`](references/pipeline-contract.md).

---

## Example 1 — Full account run: the saturation call (auto repair)

**Ask:** "Create RSAs for Halstead Automotive Group." Registry resolves the name cleanly:

```
1234567890: Halstead Automotive Group - $2,341.87
```

Step 2 votes the domain (6 unique URLs, 5 on the main site — one Facebook URL from an old
ad lost the vote); the site checks out. Step 4 returns 3 ad groups under
`Halstead - Search`: `Brake Repair`, `Oil Change`, `Transmission Repair`. Step 3, before
generation:

```
[VERTICAL] Loaded config for: Auto Repair
Searching for: auto repair Austin TX [auto_repair]

Analyzing 4 paid ads with 39 USP keywords...

Competitor 1: Gearline Auto Repair - Family Owned Since 1998
  Description: Family owned & operated. Free estimates on all repairs. Same day service...
  USP: Family Owned (matched: 'family owned')
  USP: Free Estimates (matched: 'free estimate')
  USP: Same-Day Service (matched: 'same day')
  USP: Years of Experience (matched: 'since 19')
```

(Note the fourth line: "Since 1998" in the *title* also matched the `since 19` fragment —
per-keyword-match counting at work.) The summary settles the positioning:

```
Most Common USPs (across competitors):
  - Family Owned (mentioned by 4 competitors)
  - Free Estimates (mentioned by 3 competitors)
  - Same-Day Service (mentioned by 2 competitors)
  - Years of Experience (mentioned by 2 competitors)
```

Four ads analyzed, and the per-ad `USP:` lines show Family Owned coming from **3 distinct
ads** (one ad matched both `family owned` and `locally owned`) — real saturation, not a
synonym artifact. Free Estimates: 3 mentions from 3 ads. Same-Day: 2, below the bar.

Step 5 extracts 9 services, 3 credentials (`ASE Certified Technicians`,
`AAA Approved Auto Repair`, `NAPA AutoCare Center`), 5 features. The site is family-owned
since 1991 — **and that's the call:** Halstead's real "Family Owned" USP is saturated
(4 mentions, 3 ads), so it moves out of the headline slots and into one description.
No competitor ad mentioned certifications — the credential stack is the unique lead.
Step 6 skipped: the scrape surfaced 3 named customer testimonials (≥ 2 bar met).

Per ad group, the distribution fills with keyword headlines from the ad-group name,
credentials in the first USP slots, verified testimonial quotes for social proof.
Validation passes (all ≤ 30/≤ 90, no "Free" — the *Free Estimates* claim is real on the
site, but the no-"Free" rule excludes it from copy anyway). Step 8:

```
Writing 3 RSA ad groups to sheet...
[SUCCESS] Successfully wrote to Google Sheet
```

Step-9 summary reports the saturation call explicitly, so the reviewer knows why "Family
Owned Since 1991" sits in a description instead of Headline 4.

---

## Example 2 — Thin-review business: the 4.5 gate and the fallback trap

**Ask:** RSAs for `Bridgeline Auto Care` (CID 2345678901, Denver CO). Site scrape finds
**one** testimonial — below the ≥ 2 bar, so Step 6 runs the GBP fallback:

```
Business Found:
  Name: Bridgeline Auto Care
  Rating: 4.2 stars
  Reviews: 87
```

```
Rating: 4.2★ (below 4.5 threshold)
Reviews: 87

Generated Headlines:
  1. "Honest and fast" - Customer (28 chars) [review_snippet]
  2. "Decent work, fair" - Customer (30 chars) [review_snippet]
```

Wait — read before shipping. The 4.2 rating is below the 4.5 gate, so no rating+count
headline exists (correct, automatic). But the snippet list came through the **fallback
path**: no snippet carried an exact 5-star rating, so the script fell back to *all*
snippets. Checking `original_rating` in the JSON: the first quote inherits the business
rating (its review had none of its own); the second is from a **3-star review** — its full
text reads "Decent work, fair price, but they kept my car four days," and the truncation
ladder trimmed it to a length-legal 30 characters. That's the trap: the script referees
*length* (nothing over 30 ever prints), not *meaning* — a lukewarm quote arrives looking
like a clean headline. Only headline 1 survives the read.

**Net social proof: 1 usable headline.** The redistribution scales the no-reviews rule:
each unfilled social-proof slot becomes a *verified* flexible headline — so this set runs
1 social proof + 4 flexible instead of 2 + 3. The Step-9 summary states the 4.2 rating,
the one usable quote, and the slot swap. Nothing rounds 4.2 up; nothing fabricates a count.

---

## Example 3 — The [ERROR] that isn't, and the too-clean SERP (property management)

**Ask:** RSAs for `Fernbrook Flats` (CID 3456789012, Springfield IL). Step 4:

```
Querying customer 3456789012 for Search campaign structure...
Filter: Campaign name contains 'Search'

Found 0 ad groups across campaigns:

[ERROR] Failed to retrieve campaign structure
```

First instinct — API failure. Wrong: the console above the `[ERROR]` line shows the query
*succeeded* and matched nothing. The account's campaigns are named `FF | Brand | Springfield`
and `FF | NonBrand | Springfield` — ENABLED, on the Search channel, but not *named*
"Search," so the production-safety filter excludes them all, and zero rows exits through
the same `[ERROR]` path as a real failure. The fix is a decision, not a retry: adapt the
LIKE clause in your fork to your naming convention (or rename the campaigns), then rerun.

With structure flowing, Step 3 (`--vertical property_management`) returns:

```
Analyzing 1 paid ads with 108 USP keywords...

Competitor 1: Copper Hollow Apartments | 1 & 2 Bed | Pool
  Description: Tour our renovated 1 & 2 bedroom apartments today. Pool, fitness center &...
  USP: Pool (matched: 'pool')
  USP: Fitness Center (matched: 'fitness')
  USP: Fitness Center (matched: 'fitness center')
  USP: Renovated/Updated (matched: 'renovated')
```

One ad analyzed. Every one of Fernbrook's USPs comes back `UNIQUE TO CLIENT` — which
proves nothing: with a single competitor, almost nothing can reach the 2-mention "common"
bar, so uniqueness is the default, not a discovery. The read: **thin SERP, not open
field.** Copy leads with Fernbrook's strongest *verified* claims (in-unit laundry, gated
access — both on the site), ignores the vacuous uniqueness flags, and the Step-9 summary
says "1 competitor ad analyzed — differentiation signals weak." One PM-specific note from
the run: `CTA - Tour` shows up in the USP tally (the PM keyword map counts tour phrasing
both ways) — that's everyone saying "schedule a tour," which belongs in the CTA slots
regardless, not a differentiator to chase.
