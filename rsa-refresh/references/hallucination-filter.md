# Hallucination Filter (Defense-in-Depth)

The hallucination filter is a **secondary defense**, not the primary one. The primary defense is verified-only content generation. The filter catches patterns that slip through.

## Filtered Terms

- **Property types:** townhome, condo, single-family (apartments only)
- **Proximity claims:** "near the strip", "minutes from", "steps from", "walking distance", "close to downtown", "near everything"
- **Unverified luxury:** upscale, exclusive, elite, premier, world-class, best in class, top-rated, high-end
- **Unverified newness:** brand new, newly built, new community, just opened, grand opening, now open, new construction
- **Unverified amenities:** pet park, dog park, bark park, rooftop, sky lounge, infinity pool
- **Superlatives:** "best apartments", "top apartments", "#1", "number one", "most affordable", "lowest prices", "cheapest"
- **Pricing:** from $, starting at $, starting from, prices from, /mo, /month, per month, a month
- **Promotional:** free, weeks free, month free, specials, deal, offer, limited time, discount, save, savings, reduced, waived, no deposit, zero deposit, move-in special, application fee, admin fee, look and lease

## Allowed

- Geographic terms from ad group names (Summerlin, Spring Valley, etc.)
- Terms explicitly found on website
- Generic CTAs (Schedule A Tour, Call Us Today, etc.)
- Terms that appear in the property name itself (e.g., "Homes" in a property literally named "Harbor Homes")

## Benefit Headline Verification

Benefit headlines (3 per ad) require stricter verification than feature headlines because their abstract language is harder to trace back to the source website.

**Rule:** Every benefit headline must be generated using the **feature-forward process** defined in `pm-headline-structure.md`. Start from the feature, identify what changes for the renter, then write the headline. Never brainstorm a catchy phrase and reverse-justify it with a feature.

**Required output:** When generating benefit headlines, produce a `feature_to_benefit` worksheet alongside the headlines. The worksheet must show the feature-forward chain:

| Verified Feature (from website) | What Changes For The Renter? | Benefit Headline | Pass/Fail |
|---|---|---|---|
| Double sink vanity | No more sharing sink in morning rush | "Two Sinks For Busy Mornings" | Pass - specific change, specific feature |
| Indoor + outdoor social kitchens | Host friends in purpose-built spaces | "Host Friends In Or Outdoors" | Pass - dual kitchens are distinctive |
| *(vibe: "relaxation")* | *(generic)* | "Come Home And Truly Unwind" | **Fail - started from vibe, not feature** |

**Rejection criteria for benefit headlines:**
- Cannot cite a specific verified feature from `website_text` → reject
- Benefit is a generic lifestyle claim that could apply to any property → reject
- Benefit implies an amenity not confirmed on the website (e.g., "Relax By The Fire" when no fireplace verified) → reject
- Benefit uses filtered terms from the list above (superlatives, unverified luxury, etc.) → reject
- "What changes?" column is vague or could apply to any apartment → reject (the change must be specific to the feature)

**Empty > Ungrounded.** If fewer than 3 benefits pass verification, generate fewer benefit headlines and fill remaining slots with additional verified feature headlines. Never pad with ungrounded benefits.

## Output Format

### Tab 1: Original RSAs
Shows existing state with performance ratings for comparison.

| Column | Content |
|--------|---------|
| A | Account Name |
| B | Customer ID |
| C | Campaign |
| D | Ad Group |
| E-S | Headline 1-15 + Performance ratings |
| T-W | Description 1-4 |
| X-Z | Path 1, Path 2, Final URL |

### Tab 2: Refreshed RSAs (Google Ads Editor Format)
Import-ready format with changes logged.

| Column | Content | Limit |
|--------|---------|-------|
| A | Account Name | - |
| B | Customer ID | - |
| C | Campaign | - |
| D | Ad Group | - |
| E-S | Headline 1-15 | 30 chars |
| T-W | Description 1-4 | 90 chars |
| X | Path 1 | 15 chars |
| Y | Path 2 | 15 chars |
| Z | Final URL | - |
| AA | Ad ID | - |
| AB | Changes Made | - |
