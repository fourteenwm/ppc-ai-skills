# Angle Development Prompt (Phase 5)

You are creating specific ad copy recommendations based on verified client capabilities and competitive gaps.

**CRITICAL:** ONLY recommend angles for gaps the client can verifiably fill. Every recommendation must include source citations.

---

## Task

Given verified gap-to-capability mappings from Phase 4, develop 3-5 specific ad angle recommendations with complete copy.

---

## Input Required

- Verified capabilities inventory (from Phase 4)
- Gap-to-capability mapping (from Phase 4)
- Strategic and tactical analysis (from Phases 1-2)
- Competitive context

---

## Angle Development Process

### Step 1: Review Fillable Gaps

From Phase 4, identify all gaps marked ✅ Can Fill.

**Prioritize angles by:**
1. **Gap value:** How important is this gap? (HIGH > MEDIUM > LOW)
2. **Verification strength:** How strong is the website evidence? (Explicit quote > Implied)
3. **Competitive advantage:** How many competitors are missing this?
4. **Ease of execution:** How simple is it to implement?

**Target:** Develop 3-5 angles (prioritize top gaps)

---

### Step 2: Develop Each Angle

For each prioritized gap, create a complete ad angle with:

#### 1. Angle Name
Short, descriptive name for this approach

**Example:** "Mobile-First Positioning"

---

#### 2. Headline Copy
Specific headline text (max 30 characters per headline)

Google Ads allows 3 headlines, so provide:
- **Headline 1:** Primary message (most important)
- **Headline 2:** Supporting detail
- **Headline 3:** CTA or additional benefit

**Rules:**
- Use only verified claims (from Phase 4)
- Include keyword if relevant for search term relevance
- Lead with benefit or differentiator
- Make it specific, not generic

**Example:**
- H1: "Auto Shop Software - 5,000+ Users"
- H2: "Free 30-Day Trial. No Card Needed"
- H3: "Manage Your Shop From Anywhere"

---

#### 3. Description Copy
Specific description text (max 90 characters per description)

Google Ads allows 2 descriptions, so provide:
- **Description 1:** Primary value proposition + features
- **Description 2:** Social proof + CTA

**Rules:**
- Use only verified claims
- Separate benefits from features
- Include specific numbers/proof if available
- Include CTA

**Example:**
- D1: "All-In-One Cloud Shop Management. DVI, Estimates, Invoices. Unlimited Users. iOS & Android App."
- D2: "Rated 4.8/5 By Shop Owners. Start Your Free 30-Day Trial Now."

---

#### 4. Gap Filled
Which competitive gap(s) does this angle address?

**Format:**
- **Strategic gap:** [What positioning element competitors are missing]
- **Tactical gap:** [What conversion element competitors are missing]

**Example:**
- Strategic gap: No competitor emphasizes mobile app in ads
- Tactical gap: No competitor shows social proof (customer counts/ratings)

---

#### 5. Why It Works
Explain the positioning logic and expected impact

**Address:**
- What makes this different from competitors?
- Why will this resonate with target audience?
- What conversion barriers does it remove?
- What expected impact? (CTR lift, conversion improvement)

**Example:**
"This angle works because: (1) No competitor emphasizes mobile app, creating whitespace; (2) Social proof (5,000+ users + 4.8/5 rating) builds instant credibility competitors lack; (3) Free trial removes risk barrier; (4) Expected 15-25% CTR lift from promotional hook + proof combination."

---

#### 6. Source Citations
Where on client website is each claim verified?

**Format:**
List each claim with source URL + section

**Example:**
- "5,000+ users" - Source: example-client.com/about#customers
- "4.8/5 rating" - Source: example-client.com/#social-proof
- "Free 30-day trial" - Source: example-client.com/pricing#trial
- "iOS & Android app" - Source: example-client.com/features#mobile
- "Unlimited users" - Source: example-client.com/pricing#plans

---

#### 7. Priority Level
Classify this angle as:

- **QUICK WIN:** Easy to implement, high impact, low risk
- **STRATEGIC BET:** Requires more investment, high impact, differentiated positioning
- **EXPERIMENTAL:** Unproven approach, test before scaling

**Criteria:**
- Quick Win: Fills tactical gap (easy fix) + verified capability + high competitive value
- Strategic Bet: Fills strategic gap (positioning shift) + strong verification + significant differentiation
- Experimental: Fills lower-priority gap OR weaker verification + needs testing

---

### Step 3: Rank Angles

Order your 3-5 angles by:
1. Quick Wins first (highest ROI)
2. Strategic Bets second (long-term differentiation)
3. Experimental last (test candidates)

---

## Output Format

Return results in this exact format:

```markdown
## Verified Angle Recommendations

**Client:** [Name]
**Based on:** [X] verified gaps from Phase 4
**Total Angles Developed:** [3-5]

---

### Angle 1: [Name]

**Priority:** QUICK WIN / STRATEGIC BET / EXPERIMENTAL

**Gap(s) Filled:**
- Strategic: [Gap description]
- Tactical: [Gap description]

**Headline Copy:**
- H1: "[Headline 1]"
- H2: "[Headline 2]"
- H3: "[Headline 3]"

**Description Copy:**
- D1: "[Description 1]"
- D2: "[Description 2]"

**Why It Works:**
[Explain positioning logic + expected impact]

**Source Citations:**
- "[Claim 1]" - Source: [URL]#[section]
- "[Claim 2]" - Source: [URL]#[section]
- "[Claim 3]" - Source: [URL]#[section]

**Expected Impact:**
- CTR lift: [X]%
- Conversion improvement: [X]%
- Differentiation: HIGH/MEDIUM/LOW

**Implementation Notes:**
[Any special considerations for using this angle]

---

### Angle 2: [Name]

[Same structure as Angle 1]

---

### Angle 3: [Name]

[Same structure as Angle 1]

---

### Angle 4: [Name] (Optional)

[Same structure]

---

### Angle 5: [Name] (Optional)

[Same structure]

---

### Angle Comparison Matrix

| Angle | Priority | Strategic Gap | Tactical Gap | Expected CTR Lift | Ease of Execution |
|-------|----------|---------------|--------------|-------------------|-------------------|
| [Angle 1] | QUICK WIN | [Gap] | [Gap] | +15-25% | Easy |
| [Angle 2] | STRATEGIC BET | [Gap] | [Gap] | +10-20% | Medium |
| [Angle 3] | QUICK WIN | [Gap] | [Gap] | +5-15% | Easy |
| [Angle 4] | EXPERIMENTAL | [Gap] | [Gap] | +5-10% | Medium |
| [Angle 5] | STRATEGIC BET | [Gap] | [Gap] | +20-30% | Hard |

---

### Recommended Implementation Order

**Phase 1 (Immediate):**
- Launch Angle 1: [Name] (Quick Win)
- Launch Angle 3: [Name] (Quick Win)
- **Rationale:** Easy wins with high ROI, low risk

**Phase 2 (After 2 weeks of data):**
- Launch Angle 2: [Name] (Strategic Bet)
- **Rationale:** Higher investment, needs baseline performance data

**Phase 3 (Test candidates):**
- Test Angle 4: [Name] (Experimental)
- **Rationale:** Unproven approach, test at low budget first

**Phase 4 (If differentiation needed):**
- Launch Angle 5: [Name] (Strategic Bet)
- **Rationale:** Significant positioning shift, use if competing on quick wins isn't enough

---

### Cannot Recommend (Unverifiable Gaps)

**These gaps were identified but CANNOT be filled without additional client confirmation:**

| Gap | Gap Type | Priority | Why Can't Verify | Recommended Action |
|-----|----------|----------|------------------|-------------------|
| [Gap] | Strategic/Tactical | HIGH/MED/LOW | [Reason] | Ask client / Skip |

**Example:**
| Gap | Gap Type | Priority | Why Can't Verify | Recommended Action |
|-----|----------|----------|------------------|-------------------|
| No urgency language | Tactical | MEDIUM | No time-limited offers found on website | Ask client about promotional calendar |
| AI-powered features | Strategic | LOW | No AI mentioned on website | Skip (low priority + no evidence) |

---

### A/B Test Suggestions

**For angles with similar priority, test these variations:**

**Test 1: Social Proof Emphasis**
- Angle A: Lead with customer count ("5,000+ Shops Use [Product]")
- Angle B: Lead with rating ("Rated 4.8/5 Stars By Shop Owners")
- **Hypothesis:** Customer count builds more credibility than rating
- **Test duration:** 2 weeks, equal budget split

**Test 2: Benefit vs Feature Lead**
- Angle A: Lead with benefit ("Save 10 Hours Per Week")
- Angle B: Lead with feature ("All-In-One Cloud Shop Management")
- **Hypothesis:** Benefit-led copy converts better for SaaS
- **Test duration:** 2 weeks, equal budget split

[Add more test suggestions based on angles developed]

---

### Compliance with Ad Copy Verification Standard

**✅ All recommendations comply with Agency B's ad copy verification standard:**
- Every claim is sourced from client website (Phase 4)
- Source citations included for all claims
- No assumptions based on industry standards
- No template language without verification
- Unverifiable gaps clearly flagged as "Cannot Recommend"

**✅ Quality checks passed:**
- [ ] All headlines ≤ 30 characters
- [ ] All descriptions ≤ 90 characters
- [ ] All claims have source citations
- [ ] All gaps mapped to verified capabilities
- [ ] No unverified claims in copy
```

---

## Important Rules

### DO:
1. **Use only verified claims.** Every element of copy must trace back to Phase 4 evidence.
2. **Include source citations.** Every claim needs a URL + section reference.
3. **Be specific.** "Save 10 hours/week" > "Save time"
4. **Prioritize angles.** Quick wins before strategic bets.
5. **Provide complete copy.** Exact headlines and descriptions, not concepts.
6. **Explain why it works.** Include positioning logic and expected impact.
7. **Flag unverifiable gaps.** Clearly state what you CANNOT recommend.

### DON'T:
1. ❌ Recommend angles for unverified gaps
2. ❌ Assume client has features just because competitors do
3. ❌ Use industry templates without verification
4. ❌ Create vague concepts instead of specific copy
5. ❌ Skip source citations
6. ❌ Exceed character limits (30 for headlines, 90 for descriptions)
7. ❌ Make claims not found on client website

---

## Character Limit Guidelines

**Google Ads character limits:**
- Headlines: 30 characters max (3 headlines)
- Descriptions: 90 characters max (2 descriptions)

**Tips to stay within limits:**
- Use abbreviations when natural (e.g., "DVI" instead of "Digital Vehicle Inspections")
- Remove filler words ("the," "and," "with" when possible)
- Use numbers instead of words ("5,000+" vs. "five thousand")
- Prioritize most important information first

**Character count check:**
- Always count characters for each headline/description
- Flag if over limit and provide shortened version

---

## Example Angle Development

**Client:** Example SaaS
**Verified Gaps:** 3 (Free trial, Social proof, Mobile app)

---

### Angle 1: Social Proof + Free Trial Emphasis

**Priority:** QUICK WIN

**Gap(s) Filled:**
- Strategic: Limited social proof in competitor ads (all score 0-1 on Attribute 2)
- Tactical: No promotional hooks across competitors (all ❌ Missing on Attribute 19)

**Headline Copy:**
- H1: "Auto Shop Software - 5,000+ Shops" (35 chars... TOO LONG)
  - **Fixed:** "Shop Software - 5,000+ Shops" (28 chars ✓)
- H2: "Free 30-Day Trial. No Card Needed" (33 chars... TOO LONG)
  - **Fixed:** "Free 30-Day Trial. No Card" (26 chars ✓)
- H3: "Rated 4.8/5 By Shop Owners" (26 chars ✓)

**Description Copy:**
- D1: "All-In-One Cloud Shop Management. DVI, Estimates, Invoices. Unlimited Users." (77 chars ✓)
- D2: "Start Your Free 30-Day Trial Now. No Credit Card Required. Rated 4.8/5 Stars." (78 chars ✓)

**Why It Works:**
1. **Social proof differentiation:** Competitors don't show customer counts or ratings in ads. "5,000+ shops" + "4.8/5" builds instant credibility.
2. **Promotional hook:** No competitor emphasizes free trial. "Free 30-day trial, no card" removes risk barrier.
3. **Tactical optimization:** Fills 2 universal tactical gaps (Attributes 19 & 22).
4. **Expected impact:** 15-25% CTR lift from combined social proof + promotional hook.

**Source Citations:**
- "5,000+ shops" - Source: example-client.com/about#customers
- "4.8/5" - Source: example-client.com/#social-proof
- "Free 30-day trial" - Source: example-client.com/pricing#trial
- "No credit card required" - Source: example-client.com/pricing#trial
- "All-In-One" - Source: example-client.com/#hero
- "Cloud" - Source: example-client.com/features#platform
- "DVI, Estimates, Invoices" - Source: example-client.com/features
- "Unlimited Users" - Source: example-client.com/pricing#plans

**Expected Impact:**
- CTR lift: +15-25%
- Conversion improvement: +10-20% (free trial removes friction)
- Differentiation: HIGH (no competitor uses these elements)

**Implementation Notes:**
- This is the highest-priority angle - launch first
- Monitor free trial sign-up rate (should increase with "no card" emphasis)
- Consider A/B testing customer count vs. rating in H1

---

### Angle 2: Mobile-First Positioning

**Priority:** STRATEGIC BET

**Gap(s) Filled:**
- Strategic: No competitor emphasizes mobile app (whitespace on Attribute 10)
- Tactical: Weak location/audience callouts (all ⚠️ Weak on Attribute 21)

**Headline Copy:**
- H1: "Manage Your Shop From Anywhere" (30 chars ✓)
- H2: "iOS & Android App Included" (26 chars ✓)
- H3: "Auto Shop Management Software" (29 chars ✓)

**Description Copy:**
- D1: "Cloud-Based Shop Management With Mobile App. DVI, Estimates, Invoices On The Go." (81 chars ✓)
- D2: "Unlimited Users. 100+ Integrations. Start Free 30-Day Trial." (61 chars ✓)

**Why It Works:**
1. **Positioning whitespace:** No competitor leads with mobile app in ads, even though it's table stakes.
2. **Benefit-led:** "Manage from anywhere" is the benefit, "iOS & Android" is the feature.
3. **Tactical improvement:** Strengthens audience targeting (mobile = busy shop owners on the go).
4. **Expected impact:** 10-20% CTR lift from unique positioning + benefit clarity.

**Source Citations:**
- "iOS & Android App" - Source: example-client.com/features#mobile
- "Manage from anywhere" - Source: example-client.com/features#mobile ("Access your shop data from any device")
- "Cloud-Based" - Source: example-client.com/features#platform
- "DVI, Estimates, Invoices" - Source: example-client.com/features
- "Unlimited Users" - Source: example-client.com/pricing#plans
- "100+ Integrations" - Source: example-client.com/integrations
- "Free 30-Day Trial" - Source: example-client.com/pricing#trial

**Expected Impact:**
- CTR lift: +10-20%
- Conversion improvement: +5-15%
- Differentiation: HIGH (unique positioning in market)

**Implementation Notes:**
- This is a positioning shift (mobile-first vs. feature-first)
- Launch after Angle 1 to compare performance
- Best for audience segments that value mobility (multi-location owners, busy shop managers)

---

### Angle 3: Unlimited Users Value Play

**Priority:** STRATEGIC BET

**Gap(s) Filled:**
- Strategic: Weak operational benefits across competitors (average 1.5/3 on Attribute 11)
- Tactical: No specificity/numbers in competitor ads (all ❌ Missing on Attribute 20)

**Headline Copy:**
- H1: "Unlimited Users. No Extra Fees." (31 chars... TOO LONG)
  - **Fixed:** "Unlimited Users. No Extra Fee" (29 chars ✓)
- H2: "Auto Shop Management Software" (29 chars ✓)
- H3: "All-In-One. Cloud-Based." (24 chars ✓)

**Description Copy:**
- D1: "Add Staff For Free. Cloud Shop Management For Growing Teams. DVI, Invoices, Scheduling." (89 chars ✓)
- D2: "No Per-User Charges. 100+ Integrations. Start Free 30-Day Trial." (65 chars ✓)

**Why It Works:**
1. **Pricing transparency:** Competitors mention "unlimited users" but don't emphasize the value (no extra fees).
2. **Specificity:** "No per-user charges" is more specific than generic "unlimited."
3. **Tactical gap fill:** Adds numbers/specificity that all competitors lack.
4. **Expected impact:** 10-15% lift from pricing differentiation + specificity.

**Source Citations:**
- "Unlimited Users" - Source: example-client.com/pricing#plans
- "No per-user charges" - Source: example-client.com/pricing#plans
- "Add staff for free" - Source: example-client.com/pricing (implied from unlimited users)
- "Cloud-Based" - Source: example-client.com/features#platform
- "All-In-One" - Source: example-client.com/#hero
- "DVI, Invoices, Scheduling" - Source: example-client.com/features
- "100+ Integrations" - Source: example-client.com/integrations
- "Free 30-Day Trial" - Source: example-client.com/pricing#trial

**Expected Impact:**
- CTR lift: +10-15%
- Conversion improvement: +10-20% (pricing value prop)
- Differentiation: MEDIUM (competitors have this but don't emphasize)

**Implementation Notes:**
- Best for growing shops (2+ technicians)
- Test against Angle 1 for value-conscious audience segments
- Monitor conversion rate (pricing transparency should reduce sticker shock)

---

### Angle Comparison Matrix

| Angle | Priority | Strategic Gap | Tactical Gap | Expected CTR Lift | Ease |
|-------|----------|---------------|--------------|-------------------|------|
| 1: Social Proof + Free Trial | QUICK WIN | Social proof missing | No promo hooks, no social proof execution | +15-25% | Easy |
| 2: Mobile-First | STRATEGIC BET | No mobile emphasis | Weak audience targeting | +10-20% | Medium |
| 3: Unlimited Users Value | STRATEGIC BET | Weak operational benefits | No specificity/numbers | +10-15% | Medium |

---

### Recommended Implementation Order

**Phase 1 (Immediate):**
- Launch Angle 1: Social Proof + Free Trial
- **Rationale:** Fills 2 universal tactical gaps, easy to implement, highest expected impact

**Phase 2 (After 2 weeks of data):**
- Launch Angle 2: Mobile-First Positioning
- **Rationale:** Strategic differentiation, test against baseline from Angle 1

**Phase 3 (If pricing is key differentiator):**
- Launch Angle 3: Unlimited Users Value Play
- **Rationale:** Best for value-conscious segments, medium difficulty

---

### Cannot Recommend (Unverifiable Gaps)

| Gap | Gap Type | Priority | Why Can't Verify | Recommended Action |
|-----|----------|----------|------------------|-------------------|
| No urgency language | Tactical | MEDIUM | No time-limited offers found on website | Ask client about promotional calendar |
| AI-powered features | Strategic | LOW | No AI mentioned on website | Skip (low priority + no evidence) |

---

### A/B Test Suggestions

**Test 1: Social Proof Type**
- Angle 1A: Lead with customer count ("Shop Software - 5,000+ Shops")
- Angle 1B: Lead with rating ("Shop Software - Rated 4.8/5")
- **Hypothesis:** Customer count builds more credibility than rating for SaaS
- **Test duration:** 2 weeks, equal budget split

**Test 2: Mobile Benefit vs Feature**
- Angle 2A: "Manage Your Shop From Anywhere" (benefit-led)
- Angle 2B: "iOS & Android App Included" (feature-led)
- **Hypothesis:** Benefit-led copy resonates more with busy shop owners
- **Test duration:** 2 weeks, equal budget split

---

**All recommendations verified against example-client.com. No unverified claims included.**
