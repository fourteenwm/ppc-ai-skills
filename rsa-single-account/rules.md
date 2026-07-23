# Decision Rules — rsa-single-account

The judgment layer for running the pipeline. Exact script mechanics live in
[`references/pipeline-contract.md`](references/pipeline-contract.md); copy-quality law
lives in the two companion skills. This file is what you decide with.

---

## Invariants (never trade these away)

1. **Every claim traces to the scrape or a verified review.** The Step-5 extraction (plus
   Step-6 review data) is the complete universe of usable facts. A scrape failure is a full
   stop — no generic fallback, no industry-template copy. *Empty > Inaccurate.*
2. **Read-only on Google Ads.** The pipeline queries accounts and writes a review Sheet.
   Nothing here mutates ads; the human import through Google Ads Editor is the approval
   gate, and this skill never automates it.
3. **The scripts validate structure, never copy.** The only validation any script performs
   is JSON key presence at Step 8. Character limits (30/90), headline/description counts,
   Title Case, claim verification, the no-"Free" rule — all of it is enforced by you at
   Step 7 or not at all. Never assume a script caught something.
4. **The generation is yours, not the scripts'.** Steps 1–6 gather verified inputs; Step 8
   lands output. No script writes a headline — which means no script error can explain bad
   copy, and no script can be blamed for an unverified claim.
5. **One scrape, one SERP pass per account.** Every Firecrawl scrape and SERP lookup costs
   an API credit. Cache artifacts (`--output`, `competitive_insights.json`) and reuse them
   across every ad group in the account; re-runs resume from cache, not from re-scraping.
6. **The output Sheet is dedicated.** Step 8 erases A:Z on the first tab every run. Never
   point `--sheet-id` at a spreadsheet whose first tab holds anything worth keeping.

---

## Step sequencing — what's skippable, and when

The numbered workflow is the default path, not a ritual. Steps bind to each other through
artifacts, so what you can skip depends on what you already hold:

| Step | Skip when | Never skip when |
|---|---|---|
| 1 — account list | The CID is already known (user gave it, or it's in your registry) | The account name is ambiguous across the book |
| 2 — website discovery | The user handed you the site URL (get the business name from Step 1/4 output instead) | You'd be guessing which of several domains is canonical |
| 3 — competitive analysis | No `SERP_API_KEY`, or a genuinely uncontested niche — and you accept generic-risk copy positioning | The account competes in a crowded local SERP; differentiation is the whole point of this skill |
| 4 — structure | Never — it defines the units of work (one RSA set per ad group) | — |
| 5 — scrape | Never — it is the verification source; without it there is no verified copy | — |
| 6 — reviews | The Step-5 scrape already surfaced ≥ 2 usable testimonials (that ≥ 2 bar is this workflow's rule, not a script's) | Fewer than 2 site testimonials and you still want social-proof headlines |
| 8 — sheet write | You have no Sheets access and deliver `rsa_data.json` for manual paste instead | The Sheet is the review surface anyone else will read |

**Ordering freedom:** Step 3's only consumer is Step 7, so it can run any time before
generation — its position before the scrape in the numbered flow is convention, not a
dependency. Steps 4–5–6 likewise only need to precede 7.

**Resume logic:** `competitive_insights.json` + the Step-5 cache present → jump straight to
Step 7. Both missing → full run. Only the sheet write failed (`[ERROR]` at Step 8 with
`rsa_data.json` on disk) → fix auth and re-run Step 8 alone; nothing upstream needs to
repeat.

---

## Reading the competitive JSON

The saturation **counts** are real account data. Almost everything phrased about "the
client" is not — the script computes its gap examples against four hardcoded sample USPs
(the contract's example-USP artifact section). Judgment calls this creates:

- **Never paste `unique_client_usps` or `prioritize_in_headlines` from the JSON into
  copy decisions.** At Step 7, take the client's *real* USPs from the scrape and re-apply
  the logic yourself: a claim category 3+ competitors hit is saturated (de-emphasize, or
  bury it inside a description); a real client USP absent from the competitor counts is
  your headline lead.
- **Discount saturation by the counting method.** Counts are per keyword match, so synonym
  fragments inside one ad inflate a category ("24-hour fitness center" alone scores
  Fitness Center ×3). Before treating a category as saturated, glance at the per-competitor
  console lines — 3 mentions from 3 ads is saturation; 3 mentions from 1 ad is not.
- **"Everything came back unique" is a thin SERP, not a green light.** One or two ads
  analyzed → almost nothing reaches the 2+ "common" bar → every USP flags unique. That's
  absence of evidence. Position on the strongest *verified* claims instead, and say the
  SERP was thin in the Step-9 summary.
- **`Competitors Found` ≠ competitors analyzed.** The count includes everything returned;
  analysis caps at 5 ads + 3 LSAs. Report the analyzed number honestly.
- **Property-management runs double-count CTAs.** The PM keyword map routes tour/apply
  phrases into both the USP and CTA tallies — don't read "CTA - Tour" appearing as a
  saturated *USP* as competitors owning tours; it means everyone says "schedule a tour,"
  which belongs in your CTA slots regardless.

---

## Review usability — what social proof survives

- **The 4.5 gate is absolute for rating headlines.** Below 4.5, no rating+count headline —
  in either mode (`--apartment` changes the attribution noun, not the threshold). A 4.2★
  business gets snippet or no social proof, never a rounded-up rating.
- **Verify the panel is the client.** The GBP lookup trusts whatever local panel the SERP
  returns for "name + location." Same-named business two towns over = borrowed reviews.
  Check the printed `Name:` line; when it doesn't match, treat the lookup as failed.
- **Snippet fallback can hand you sub-5-star text.** When no snippet passes the exact
  5-star filter, the script falls back to *all* snippets — a lukewarm or negative quote can
  arrive formatted as a headline. Read `original_rating` and the full quote; ship nothing
  you haven't read in context.
- **The ≥ 2 site-testimonial bar is yours to enforce** before falling back to GBP — the
  scripts never count testimonials.
- **Zero usable reviews anywhere → the 5-flexible redistribution** (drop the 2 social-proof
  slots, add 2 more *verified* flexible headlines). Never a placeholder rating, never an
  unverified count — that redistribution is this workflow's rule, enforced by you at
  Step 7.

---

## False alarms and misreads

| Looks like | Usually is | Check |
|---|---|---|
| Account missing from the Step-1 list | Zero MTD spend — zero-spend accounts print nothing | `Total accounts checked:` vs list length; query the CID directly |
| `{cid}: {name} - Error` at Step 1 | That one account's query failed (canceled registry row, no access) — not "no spend" | Registry entry status; try the CID alone |
| `[ERROR] Failed to retrieve campaign structure` at Step 4 | Zero ENABLED ad groups in ENABLED campaigns *named* "Search" — same exit as an API failure | Console above the error: `Found 0 ad groups` = naming/filter miss, not an outage. LIKE-clause conventions differ per book |
| Wrong site scraped at Step 5 | Step-2 domain vote counted tracking/microsite URLs (paused-campaign ads included; count = unique URLs, not ads) | Eyeball the voted domain before scraping; hand the skill the real URL |
| Services-page facts absent from extraction | The 10,000-char truncation — a long homepage crowds out sub-pages | `Services page found: yes` + missing facts = truncation; scrape the services URL directly as the input |
| `SERVICES (0):` from a content-rich site | Extraction returned off-schema or thin JSON — schema is prompt-enforced, not validated | Read the `JSON OUTPUT:` block; re-run Step 5 |
| Every client USP flagged unique | Thin SERP or the example-USP artifact | `Analyzing N paid ads` count; re-derive vs real USPs |
| A USP "saturated" you can't see in the ads | Synonym multi-count inside one or two ads | Per-competitor `USP:` console lines |
| `[WARNING] No local results found` | Query too vague or name mismatch — not proof the business has no reviews | Retry with `"{name}" "{city} {state}"`; verify spelling |
| Sheet columns misaligned after a run | More than 15 headlines (or 4 descriptions) in one `rsa_data.json` entry — the writer pads but never truncates | Entry lengths; fix the JSON, re-run Step 8 |
| Old rows "still there" after a partial write | The write failed before clearing — or you're reading a non-first tab; only the first tab is touched | `[SUCCESS]` in the console; Sheet revision history |

---

## Escalation default

When a claim can't be verified, **leave the slot empty and say so in the Step-9 summary** —
short sets are a finding, not a failure. When identity is ambiguous — which account, which
website, which GBP panel — **stop and ask; never guess an identity input**, because every
downstream verification inherits it. When validation flags a violation (length, casing,
unverifiable claim), flag it in the summary with its location; never silently drop or
silently ship.
