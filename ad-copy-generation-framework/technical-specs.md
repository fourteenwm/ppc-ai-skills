# Technical Specifications

Validation rules, character limits, and formatting requirements for Google Ads RSA copy.

---

## Character Limits (Google Ads Hard Limits)

| Element | Maximum Characters | Note |
|---------|-------------------|------|
| **Headline** | 30 | Including spaces, punctuation |
| **Description** | 90 | Including spaces, punctuation |
| **Callout** | 25 | For reference (extensions) |
| **Sitelink Text** | 25 | For reference (extensions) |
| **Sitelink Description** | 35 | For reference (extensions) |

### Consequences of Exceeding Limits

- Google Ads Editor will **reject** headlines >30 chars
- Google Ads Editor will **reject** descriptions >90 chars
- API uploads will **fail** validation
- Manual entry in UI will **truncate** or **error**

**CRITICAL**: Always validate character counts BEFORE outputting to Google Sheet.

---

## Capitalization Rules

### Title Case (Required for All Headlines & Descriptions)

**Rule**: Capitalize the first letter of each significant word.

**Capitalize**:
- First and last words (always)
- Nouns, pronouns, verbs, adjectives, adverbs
- Words ≥4 letters

**Lowercase** (unless first/last word):
- Articles: a, an, the
- Conjunctions: and, but, or, nor, for, yet, so
- Short prepositions: at, by, for, from, in, of, on, to, with

**Examples**:
- ✅ "Get Your Oil Change Today"
- ✅ "Licensed & Insured Mechanics"
- ✅ "Best Shop in Austin Since 1985"
- ❌ "get your oil change today"
- ❌ "Licensed & insured mechanics"
- ❌ "Best Shop In Austin Since 1985" (overcapitalized "In")

### Special Cases

**Acronyms**: Always ALL CAPS
- ✅ "ASE Certified Technicians"
- ✅ "BBB A+ Rated Shop"
- ❌ "Ase Certified Technicians"

**Symbols & Numbers**: Don't capitalize
- ✅ "Save 20% On Service"
- ✅ "Open 24/7 For Emergencies"

**Ampersand (&)**: Don't capitalize the words around it unless they're significant
- ✅ "Licensed & Insured"
- ✅ "Oil & Filter Change"
- ❌ "Licensed & insured"

---

## Punctuation & Symbols

### Allowed Punctuation (Google Ads)

**Fully Allowed**:
- Period (.)
- Comma (,)
- Exclamation mark (!)
- Question mark (?)
- Apostrophe (')
- Quotation marks (" ")
- Hyphen (-)
- Ampersand (&)
- Parentheses ( )
- Slash (/)
- Colon (:)
- Semicolon (;)
- Dollar sign ($)
- Percent sign (%)
- Plus sign (+)
- Star (★ - for ratings)

**Restricted**:
- Ellipsis (...) - Use sparingly
- Multiple exclamation marks (!!) - Avoid (looks spammy)
- ALL CAPS WORDS - Not allowed
- Emoji - Not allowed in text ads

### Best Practices

**End Punctuation**:
- CTAs: Use ! ("Call Now For Same-Day Service!")
- Questions: Use ? ("Need Emergency Plumbing?")
- Statements: Use . or no punctuation ("Licensed & Insured Mechanics")

**Symbols for Stand-Out** (Element #11):
- Use $ for pricing: "Oil Change From $39.99"
- Use % for discounts: "Save 20% On First Service"
- Use ★ for ratings: "Rated 4.9★ By 2000+"
- Use & for brevity: "Licensed & Insured"
- Use / for options: "Synthetic/Conventional Oil"
- Use + for quantity: "30+ Years Experience"

**Avoid**:
- Multiple punctuation marks: "Call Now!!" (spammy)
- Unnecessary periods: "Expert. Mechanics. Austin." (choppy)
- Excessive symbols: "$$$SAVE NOW!!!" (violates Google policy)

---

## Formatting Rules

### Spacing

**Single Space Between Words**:
- ✅ "Oil Change Service"
- ❌ "Oil Change  Service" (double space)

**No Leading/Trailing Spaces**:
- ✅ "Call Now For Service"
- ❌ " Call Now For Service " (spaces before/after)

**Space After Punctuation**:
- ✅ "Licensed, Insured, Experienced"
- ❌ "Licensed,Insured,Experienced" (no spaces after commas)

### Numbers

**Numeric Format**:
- Use digits for numbers: "30 Years", "2000+ Customers", "4.9★"
- Spell out "24/7" or "24 Hours" (not "twenty-four hours")
- Use + for quantities >10: "30+ Years", "2000+ Customers"

**Pricing Format**:
- Include currency symbol: "$39.99", "From $29"
- Round numbers OK: "$50 Oil Change"
- Ranges: "Oil Change $35-$75"

**Ratings**:
- Format: "X.X★" or "Rated X.X★"
- Include decimal: "4.9★" not "5★" (unless truly 5.0)

### Symbols & Special Characters

**Ampersand (&)**:
- Use instead of "and" to save characters
- ✅ "Licensed & Insured" (19 chars) vs "Licensed and Insured" (23 chars)
- ✅ "Oil & Filter Change" (19 chars) vs "Oil and Filter Change" (23 chars)

**Star (★)**:
- Use for ratings: "Rated 4.9★"
- Unicode: U+2605 (use the filled star, not hollow ☆)
- Alternative: "Rated 4.9 Stars" (if symbol not supported)

**Plus (+)**:
- Use for quantities: "30+ Years", "2000+ Customers"
- Format: Number + "+" + Space + Noun
- ✅ "30+ Years Experience"
- ❌ "30 + Years Experience"

---

## Sentiment Scoring

### Sentiment Scale

**Range**: 0.0 (negative) to 1.0 (positive)

| Score | Classification | Interpretation |
|-------|---------------|----------------|
| 0.9-1.0 | Very Positive | Enthusiastic, exciting, excellent |
| 0.8-0.9 | Positive | Confident, trustworthy, professional |
| 0.6-0.8 | Neutral-Positive | Informative, factual |
| 0.4-0.6 | Neutral | Neither positive nor negative |
| 0.0-0.4 | Negative | Avoid in ad copy |

### Target Sentiment

**For Google Ads RSAs**: Target **0.8-1.0**

**Why**:
- Positive sentiment increases CTR
- Builds trust and confidence
- Reduces perceived risk
- Aligns with purchase intent

### Sentiment Analysis Examples

**Very Positive (0.9-1.0)**:
- "Get Same-Day Service Today!" (0.95)
- "Rated 4.9★ By 2000+ Happy Customers" (0.92)
- "Call Now & Save 20%!" (0.90)

**Positive (0.8-0.9)**:
- "Licensed & Insured Mechanics" (0.85)
- "30+ Years of Experience" (0.82)
- "Free Estimates Available" (0.88)

**Neutral-Positive (0.6-0.8)**:
- "Oil Change Service Austin" (0.70)
- "ASE Certified Technicians" (0.72)
- "Serving Austin Since 1985" (0.68)

**Avoid (<0.6)**:
- "Don't Risk Your Engine" (0.45 - fear-based)
- "Avoid Costly Repairs" (0.52 - negative framing)
- "Stop Overpaying For Service" (0.48 - aggressive)

**Note**: Problem/solution headlines (Element #17) may have lower sentiment scores (0.6-0.7) due to problem acknowledgment, but should pair with positive solution language.

---

## Validation Rules

### Pre-Flight Checklist

**Before generating final output, validate**:

1. **Character Counts**:
   - ✅ All headlines ≤30 chars
   - ✅ All descriptions ≤90 chars
   - ❌ Flag any violations

2. **Capitalization**:
   - ✅ All headlines/descriptions use Title Case
   - ✅ Acronyms are ALL CAPS
   - ✅ First and last words always capitalized

3. **Punctuation**:
   - ✅ CTAs end with !
   - ✅ Questions end with ?
   - ✅ No double punctuation (!!)
   - ✅ Spaces after all punctuation

4. **Sentiment**:
   - ✅ All headlines ≥0.8 sentiment (or ≥0.6 for problem/solution)
   - ✅ All descriptions ≥0.8 sentiment

5. **Verification**:
   - ✅ All USPs found on website
   - ✅ All reviews from website or GMB
   - ✅ All credentials verified
   - ✅ No assumed features/services

6. **Continuity**:
   - ✅ All CTAs appear on landing page
   - ✅ All specific claims (prices, hours, guarantees) visible on page
   - ✅ All credentials mentioned are on page

### Validation Output Format

For each headline/description, output:

```
| Text | Chars | Type | Sentiment | Valid |
|------|-------|------|-----------|-------|
| "Get Oil Change Today!" | 22 | CTA | 0.92 | ✅ |
| "Emergency Plumber Austin TX Near You" | 37 | Keyword | 0.75 | ❌ (>30 chars) |
```

**Valid Column**:
- ✅ = Passes all validation rules
- ⚠️ = Warning (usable but not ideal, e.g., 0.6-0.7 sentiment)
- ❌ = Fail (character limit exceeded, must fix)

---

## Output Format Specifications

### For Google Sheets Export

**Column Structure**:
```
| Account | Campaign | Ad Group | H1 | H2 | ... | H15 | D1 | D2 | D3 | D4 |
```

**Data Format**:
- Plain text (no formatting)
- Title Case applied
- All punctuation included
- No leading/trailing spaces
- No line breaks within cells

**Header Row**:
```
Account, Campaign, Ad Group, Headline 1, Headline 2, ..., Headline 15, Description 1, Description 2, Description 3, Description 4
```

### For Analysis/Review

**Extended Format** (with metadata):
```
| Text | Chars | Type | Sentiment | Framework Elements | Verified |
|------|-------|------|-----------|-------------------|----------|
| "Get Oil Change Today!" | 22 | CTA | 0.92 | #4, #5, #12 | ✅ |
```

**Columns**:
- **Text**: The headline or description
- **Chars**: Character count (including spaces)
- **Type**: Keyword, Social Proof, Generic USP, CTA, Pun, Flexible, Description+CTA, Description (no CTA)
- **Sentiment**: 0.0-1.0 score
- **Framework Elements**: Which of the 23 elements are applied
- **Verified**: ✅ = verified from website, ⚠️ = generic claim, ❌ = not verified

---

## Google Ads Policy Compliance

### Prohibited Content

**Never Include**:
- ❌ ALL CAPS WORDS
- ❌ Excessive punctuation (!!)
- ❌ Emoji or special Unicode characters (except ★ for ratings)
- ❌ Spammy language ("Click here!", "Best deal ever!!!")
- ❌ Unverifiable claims ("World's best", "#1 in the country")
- ❌ Misleading pricing ("Free" when not actually free)
- ❌ Competitor trademarked terms (unless authorized)

### Best Practices

**Do**:
- ✅ Use specific, verifiable claims
- ✅ Include local relevance (city, area)
- ✅ Match landing page content (continuity)
- ✅ Use proper grammar and spelling
- ✅ Follow Title Case rules

**Don't**:
- ❌ Make unsubstantiated superlatives
- ❌ Use clickbait language
- ❌ Repeat same headline 3+ times
- ❌ Include phone numbers in text (use call extensions)
- ❌ Include URLs in text (use display URL field)

---

## Character Count Strategies

### Maximizing 30-Character Headlines

**Space-Saving Techniques**:
- Use & instead of "and": saves 2 chars
- Use + for quantities: "30+ Years" vs "Over 30 Years"
- Use symbols: "4.9★" vs "4.9 Stars"
- Use digits: "24/7" vs "24 Hours A Day"
- Abbreviate where appropriate: "TX" vs "Texas", "Dr" vs "Doctor"

**Examples**:
- "Licensed and Insured Mechanics" (33 chars) ❌
- "Licensed & Insured Mechanics" (28 chars) ✅

- "Over 30 Years of Experience" (28 chars)
- "30+ Years of Experience" (23 chars) ✅ (saves 5 chars!)

- "Rated 4.9 Stars by 2000 Customers" (35 chars) ❌
- "Rated 4.9★ By 2000+ Customers" (30 chars) ✅

### Maximizing 90-Character Descriptions

**Structure Strategies**:
1. **Three-Part Structure**: "[Keyword] [USP1]. [USP2]. [CTA]!"
   - "Oil Change By ASE Certified Techs. Licensed & Insured. Call Today!" (67 chars)
   - Leaves room for expansion

2. **Two-Part Structure**: "[Keyword] [Long USP]. [CTA]!"
   - "Expert Brake Repair With Lifetime Warranty On All Parts & Labor. Book Your Appointment Today!" (95 chars) ❌ (too long)
   - "Expert Brake Repair With Lifetime Warranty. Free Estimates. Book Now!" (71 chars) ✅

3. **Front-Load Keywords**: Start with keyword for relevance
   - "Oil Change" (keyword first) vs "Get Your Oil Change" (filler words)

**Space-Saving Techniques**:
- Same as headlines (use &, +, ★, digits)
- Remove unnecessary adjectives: "very professional" → "professional"
- Use active voice: "We serve Austin" → "Serving Austin"

---

## Error Handling

### Character Limit Violations

**If headline exceeds 30 chars**:
1. **Try space-saving techniques** first
2. **Remove least important words** (adjectives, filler)
3. **Rephrase entirely** if needed
4. **Flag for user review** if can't fix without losing meaning

**Example**:
- Original: "Emergency Plumbing Service Available 24/7" (41 chars) ❌
- Attempt 1: "Emergency Plumbing 24/7 Available" (33 chars) ❌
- Attempt 2: "Emergency Plumbing - 24/7" (26 chars) ✅
- OR: "24/7 Emergency Plumbing Service" (31 chars) ❌
- Final: "24/7 Emergency Plumbing" (23 chars) ✅

### Low Sentiment Scores

**If sentiment <0.8**:
1. **Check if problem/solution headline** (Element #17) - these may be 0.6-0.7 naturally
2. **Add positive language**: "expert", "trusted", "quality"
3. **Change negative framing**: "Avoid costly repairs" → "Save with preventive maintenance"
4. **Flag for user review** if intentionally neutral (e.g., pure keyword headlines)

### Unverified Claims

**If USP/feature not found on website**:
1. **Skip the claim** entirely
2. **Use generic alternative**: "ASE Certified" → "Expert Mechanics" (if no ASE mention)
3. **Flag for user review**: "⚠️ Claim not verified on website"
4. **Never assume** features/services

---

## See Also

- `framework.md` - The 23-element framework
- `distribution.md` - Headline/description distribution formulas
- `examples.md` - Complete RSA examples with analysis
