# PM Description Structure & Voice Lifting

## Description Structure (up to 4 total)

Descriptions are generated ONCE per account and applied identically to every ad group.
Customizer descriptions (e.g., `{CUSTOMIZER.Special}`) are preserved in place.

| Slot | Content | Source |
|------|---------|--------|
| Customizer slot | `{CUSTOMIZER.Special}` | Preserved from existing ad |
| Non-customizer 1 | Benefit + amenity proof (unique differentiators) | Formula from verified features |
| Non-customizer 2 | Positioning statement | Website voice lifting |
| Non-customizer 3 | Lifestyle/location + CTA | Website voice lifting |

## Strategy: Hybrid Approach

Use **website voice lifting** for 2 of 3 descriptions, and **formula** for 1.

**Website voice lifting:** An EDITING task, not a writing task. Find a complete sentence on the property website that already sells well, then trim it to 90 chars and Title Case. The result should sound like it could still appear on the property's website -- because it's their words, shortened.

**Formula (amenity-specific):** Build from verified amenities when the specific features ARE the differentiator (e.g., two pools + spa + sauna combo). Feature lists earn their place when the features are genuinely unusual.

**Why hybrid:** Headlines (30 chars) naturally suit one-feature-per-slot. Descriptions (90 chars) have room for a complete thought -- a positioning argument, a value proposition, an emotional hook. Cramming features into comma lists wastes that space doing what headlines already do.

## Voice Lifting Process (for slots 2 and 3)

Voice lifting is EDITING the property's own copy, not WRITING new sentences from extracted keywords.

**Process:**
1. Read `website_text` end to end
2. Find the marketing paragraphs (skip navigation, policies, form labels)
3. Identify 3-5 complete sentences with strong marketing messages
4. For each voice-lifted description, START from one of these sentences
5. Trim to 90 chars by removing clauses, simplifying phrases -- pare down, don't pad
6. Convert to Title Case and append CTA if space allows

**Litmus test:** Could this description appear on the property's website? If not, you're assembling fragments, not lifting voice. Start over from a different source sentence.

**WRONG -- Fragment assembly:**
```
Extracted: "Refined Interiors" + "modern" + "North Stockton"
Built: "Refined Interiors And Modern Floor Plans In North Stockton. Explore Today."
Problem: No sentence on the website says anything like this. These are
section headers and keywords Frankensteined into a new sentence.
```

**RIGHT -- Voice lifting:**
```
Source: "were designed to offer you an unrivaled lifestyle in a private setting"
Trimmed: "Apartments Designed For An Unrivaled Lifestyle In A Private Setting. Tour Today."
Why: This IS the website's sentence, shortened to fit. It sounds like the
property because it literally is the property's voice.
```

## Description Slots

1. **Benefit + amenity proof (formula):** Lead with what the renter experiences, backed by specific amenities as proof. The benefit is the hook; the amenities make it credible. (e.g., "Unwind After Work With Two Pools, A Spa, And A Sauna At RiverEdge.")
2. **Positioning (website voice):** Lift the property's core value proposition from its marketing copy (e.g., "Townhome-Style Residences Designed To Feel Like True Homes With Spacious Layouts.")
3. **Lifestyle/location + CTA (website voice):** Lift the location or lifestyle messaging, append CTA (e.g., "Effortless Access To All San Diego Has To Offer - Shopping, Beaches, And More. Tour Today.")

## Description Rules

- 90 character max per description
- **Title Case** (matches portfolio convention)
- Verified website content only (same standard as headlines)
- Hallucination filter applies to descriptions
- If LLM generation fails, descriptions are left empty (Empty > Inaccurate)

## Description Style Guidelines

- Identify 3-5 COMPLETE SENTENCES from `website_text` that are strong marketing copy (skip nav, policies, forms)
- For voice-lifted slots, START from one of these sentences and trim to 90 chars -- pare down, don't pad
- Do NOT extract individual words/phrases and reassemble into new sentences (that's fragment assembly, not voice lifting)
- Use action verbs in the amenity description: "Relax At Our Courtyard Pool" not just "Courtyard Pool"
- Vary structures across the 3 descriptions:
  - Benefit statement backed by amenity proof (amenity slot)
  - Positioning statement in the property's own words (website voice slot)
  - Location/lifestyle value proposition with CTA (website voice slot)
- Include a CTA in at least one description (Tour, Schedule, Apply)
- Avoid comma-list pattern ("X, Y, And Z") for all 3 -- at most 1 should be a list
