# PM Headline Structure (15 total)

1 customizer is preserved from the existing ad. Claude Code provides 14 headlines:

| Type | Count | Description | Example |
|------|-------|-------------|---------|
| **Keyword-driven** | 2 | Based on ad group type (BDRM/GEO/Brand) | "2 Bedroom Apartments" |
| **Standard CTA** | 2 | Required calls to action | "Schedule A Tour", "Call Us Now" |
| **Outcome CTA** | 1 | Apartment-specific action | "Find Your Next Apartment" |
| **Unit-type** | 1 | Available floor plans | "Studio, 1 & 2 BR Apts" |
| **Brand** | 1 | Property name | "Maple Ridge Apartments" |
| **Feature** | 4 | Verified amenities with action verbs | "Swim In Our Courtyard Pool" |
| **Benefit** | 3 | Lifestyle outcomes from verified features | "Come Home To Your Private Retreat" |

## Feature Headline Guidelines

- Use action verbs: "Enjoy Our Rooftop Lounge" not "Rooftop Lounge"
- Use the full 30-char budget (aim for 22-26 chars, not 14-16)
- Prioritize unique differentiators from competitor analysis
- Every feature must be verified from the property website
- When the website provides specific numbers (pool count, square footage, floor count), use them: "2 Resort-Style Pools" > "Resort-Style Pool". Specificity builds trust.

## Benefit Headline Guidelines

**MANDATORY: Feature-Forward Process (do NOT brainstorm benefits then justify them)**

Generate benefits in this exact order:

1. **List the property's distinctive features** from `website_text` (skip generic ones like "air conditioning")
2. **For each feature, ask: "What changes for the renter?"** — write the human outcome, not the amenity name
3. **Write the headline from that change** — the headline describes the renter's new reality, not the feature
4. **Rejection test:** "Could this headline apply to ANY apartment?" If yes, the benefit is too generic. Go back to step 2 with a more specific change.

**You must produce a `feature_to_benefit` worksheet before writing any benefit headlines:**

| Verified Feature | What Changes For The Renter? | Headline | Pass/Fail |
|---|---|---|---|
| Double sink vanity | No more sharing the sink during morning rush | "Two Sinks For Busy Mornings" | Pass - specific to this property |
| Indoor + outdoor social kitchens | Can host friends in purpose-built spaces, inside or outside | "Host Friends In Or Outdoors" | Pass - not all apts have dual social kitchens |
| Large walk-in closets | Room for everything without cramming | "Space For Everything You Own" | Pass - grounded in verified closets |
| *(vibe: "relaxation")* | *(generic unwinding)* | "Come Home And Truly Unwind" | **Fail - started from vibe, not feature** |

**Common failure mode:** Brainstorming catchy benefit phrases first, then reverse-justifying them by attaching a feature. This produces generic headlines that could apply to any property. Always start from the feature and work forward.

**Rules:**
- Describe what CHANGES for the renter, not what EXISTS at the property
- Must still be grounded in verified features (benefit of what?)
- Avoid generic lifestyle claims not tied to a specific feature
- If fewer than 3 benefits pass the rejection test, fill remaining slots with additional feature headlines (Empty > Generic)

## Voice Consistency

Google serves random subsets of your 15 headlines together. All 14 non-customizer headlines must read as if they came from the same marketing voice.

- Do NOT mix urgent/transactional tone ("Act Now") with warm/lifestyle tone ("Your Peaceful Retreat") in the same ad
- Pick the property's natural voice from their website copy and hold it across all headlines
- Litmus test: Could any 3 headlines appear side by side without tonal whiplash?

## Competitor Differentiation

If `competitor_data` is present in the context JSON, use it to find gaps:

- Scan competitor headlines for repeated themes (e.g., every competitor says "luxury")
- Deprioritize words/angles the competition already saturates
- Prioritize the property's unique features that NO competitor mentions
- Goal: Fill competitive gaps, don't echo the crowd

## Keyword Headlines by Ad Group Type

**BDRM Ad Groups** (e.g., "2 Bedrooms"):
```
"2 Bedroom Apartments"
"2 BR Apts For Rent"
```

**GEO Ad Groups** (e.g., "Summerlin"):
- If property IS IN geography: `"Summerlin Apartments"`
- If property NEAR geography: `"Apts Near Summerlin"`

**Brand Ad Groups**:
```
"[Property] Apts"
"[Property] Austin"
```
