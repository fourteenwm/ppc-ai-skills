# Client Verification Prompt (Phase 4)

You are verifying client capabilities before making any ad copy recommendations.

**CRITICAL REQUIREMENT:** This phase is MANDATORY before any ad angle recommendations. Complies with Agency B ad copy verification standard.

---

## Task

Given competitive gaps identified in Phase 3, verify which gaps the client can actually fill by scraping their website and extracting capabilities.

**Core Rule:** ONLY use information EXPLICITLY VERIFIED from the client's website. NO assumptions, NO industry standards, NO templates.

---

## Input Required

- Client website URL
- Competitive gaps from Phase 3 (prioritized list)
- Gap types: Strategic gaps, tactical gaps, positioning whitespace

---

## Website Scraping Process

### Step 1: Scrape Client Website

Use WebFetch or Firecrawl to extract content from key pages:

**Priority pages to scrape:**
1. **Homepage** - Primary messaging, hero copy, main value prop
2. **Features page** - What they offer, capabilities list
3. **Pricing page** - Plans, what's included, free trial info
4. **About page** - Company credentials, awards, stats, customer counts
5. **How It Works page** - Process, use cases, applications
6. **Testimonials/Reviews page** - Social proof, ratings, customer quotes
7. **Support/Contact page** - Support availability, guarantees

**Scraping checklist:**
- [ ] Homepage scraped
- [ ] Features page scraped
- [ ] Pricing page scraped
- [ ] About page scraped
- [ ] Other relevant pages scraped

**Tools:**
- Prefer Firecrawl for comprehensive extraction
- Fall back to WebFetch for simple pages
- Use multiple tool calls in parallel for efficiency

---

### Step 2: Extract Capabilities with Sources

For each page scraped, extract:

**1. Features & Capabilities**
- What specific features are offered?
- What integrations are available?
- What platforms (mobile, web, cloud)?

**Format:**
```
✅ [Feature] - Source: [URL]#[section]
Example: ✅ "Mobile app (iOS & Android)" - Source: example-client.com/features#mobile
```

---

**2. Benefits & Outcomes**
- What results do they promise?
- What metrics or improvements are claimed?
- What pain points do they address?

**Format:**
```
✅ [Benefit] - Source: [URL]#[section]
Example: ✅ "Save 10 hours per week" - Source: example-client.com/#hero
```

---

**3. Social Proof & Credibility**
- Customer counts
- Ratings/reviews
- Awards/certifications
- Testimonials

**Format:**
```
✅ [Proof] - Source: [URL]#[section]
Example: ✅ "Used by 5,000+ businesses" - Source: example-client.com/about#customers
```

---

**4. Pricing & Offers**
- Free trial availability (duration?)
- Discounts or promotions
- What's included in each plan
- Pricing transparency

**Format:**
```
✅ [Offer] - Source: [URL]#[section]
Example: ✅ "30-day free trial" - Source: example-client.com/pricing
```

---

**5. Technical Details**
- Cloud-based or on-premise
- API availability
- Integration count
- Mobile app availability

**Format:**
```
✅ [Tech] - Source: [URL]#[section]
Example: ✅ "Cloud-based SaaS" - Source: example-client.com/features#platform
```

---

**6. Operational Details**
- User limits (unlimited vs. per-seat?)
- Support availability (24/7, business hours?)
- Setup time
- Training offered

**Format:**
```
✅ [Operational] - Source: [URL]#[section]
Example: ✅ "Unlimited users included" - Source: example-client.com/pricing#plans
```

---

**7. Target Audience Indicators**
- Who do they say they're for?
- What customer segments mentioned?
- Geographic targeting?

**Format:**
```
✅ [Audience] - Source: [URL]#[section]
Example: ✅ "Built for independent auto shops" - Source: example-client.com/about#mission
```

---

### Step 3: Map Gaps to Capabilities

For EACH gap identified in Phase 3, determine:

**Can the client fill this gap?**

**Format:**

| Gap | Gap Type | Can Fill? | Evidence | Source |
|-----|----------|-----------|----------|--------|
| [Gap description] | Strategic/Tactical | ✅ Yes / ❌ No | [Quote from website OR "Not found"] | [URL#section OR "N/A"] |

**Rules:**
- ✅ **Yes** = Explicit evidence found on website
- ❌ **No** = No evidence found (cannot verify)
- NEVER assume "Yes" based on industry standards
- NEVER use templates or common practices as justification

---

### Step 4: Create Capability Inventory

Organize all verified capabilities by category:

**Verified Capabilities:**

#### Features
- ✅ [Feature 1] - Source: [URL]
- ✅ [Feature 2] - Source: [URL]

#### Benefits
- ✅ [Benefit 1] - Source: [URL]
- ✅ [Benefit 2] - Source: [URL]

#### Social Proof
- ✅ [Proof 1] - Source: [URL]
- ✅ [Proof 2] - Source: [URL]

#### Pricing/Offers
- ✅ [Offer 1] - Source: [URL]
- ✅ [Offer 2] - Source: [URL]

#### Technical
- ✅ [Tech 1] - Source: [URL]
- ✅ [Tech 2] - Source: [URL]

#### Operational
- ✅ [Operational 1] - Source: [URL]
- ✅ [Operational 2] - Source: [URL]

#### Audience
- ✅ [Audience 1] - Source: [URL]
- ✅ [Audience 2] - Source: [URL]

**Cannot Verify:**
- ❌ [Capability] - Not found on website
- ❌ [Capability] - Not found on website

---

## Output Format

Return results in this exact format:

```markdown
## Client Verification

**Client:** [Name]
**Website:** [URL]
**Date Scraped:** [Date]

---

### Website Scrape Summary

**Pages Scraped:**
- ✅ Homepage ([URL])
- ✅ Features ([URL])
- ✅ Pricing ([URL])
- ✅ About ([URL])
- ✅ Other: [List any additional pages]

**Total Capabilities Verified:** X

---

### Verified Capabilities Inventory

#### Features & Capabilities
- ✅ [Feature] - Source: [URL]#[section]
- ✅ [Feature] - Source: [URL]#[section]
[List all verified features]

#### Benefits & Outcomes
- ✅ [Benefit] - Source: [URL]#[section]
- ✅ [Benefit] - Source: [URL]#[section]
[List all verified benefits]

#### Social Proof & Credibility
- ✅ [Proof element] - Source: [URL]#[section]
- ✅ [Proof element] - Source: [URL]#[section]
[List all verified proof]

#### Pricing & Offers
- ✅ [Pricing detail] - Source: [URL]#[section]
- ✅ [Offer] - Source: [URL]#[section]
[List all verified pricing/offers]

#### Technical Details
- ✅ [Tech spec] - Source: [URL]#[section]
- ✅ [Tech spec] - Source: [URL]#[section]
[List all verified tech details]

#### Operational Details
- ✅ [Operational detail] - Source: [URL]#[section]
- ✅ [Operational detail] - Source: [URL]#[section]
[List all verified operational details]

#### Target Audience Indicators
- ✅ [Audience mention] - Source: [URL]#[section]
- ✅ [Audience mention] - Source: [URL]#[section]
[List all audience indicators]

---

### Gap-to-Capability Mapping

**From Phase 3, these gaps were identified:**

| # | Gap Description | Gap Type | Priority | Can Fill? | Evidence | Source |
|---|-----------------|----------|----------|-----------|----------|--------|
| 1 | [Gap] | Strategic/Tactical | HIGH/MED/LOW | ✅ Yes / ❌ No | [Quote OR "Not found"] | [URL OR "N/A"] |
| 2 | [Gap] | Strategic/Tactical | HIGH/MED/LOW | ✅ Yes / ❌ No | [Quote OR "Not found"] | [URL OR "N/A"] |
| 3 | [Gap] | Strategic/Tactical | HIGH/MED/LOW | ✅ Yes / ❌ No | [Quote OR "Not found"] | [URL OR "N/A"] |
| 4 | [Gap] | Strategic/Tactical | HIGH/MED/LOW | ✅ Yes / ❌ No | [Quote OR "Not found"] | [URL OR "N/A"] |
| 5 | [Gap] | Strategic/Tactical | HIGH/MED/LOW | ✅ Yes / ❌ No | [Quote OR "Not found"] | [URL OR "N/A"] |

---

### Fillable Gaps (Verified)

**These gaps CAN be filled based on verified website evidence:**

#### 1. [Gap Description]
- **Gap type:** Strategic/Tactical
- **Priority:** HIGH/MEDIUM/LOW
- **Evidence:** "[Exact quote from website]"
- **Source:** [URL]#[section]
- **Competitive advantage:** [Why this gap is valuable + why client can fill it better than competitors]
- **Recommendation readiness:** ✅ Ready for angle development (Phase 5)

#### 2. [Gap Description]
[Same structure]

---

### Cannot Verify (Unverifiable Gaps)

**These gaps CANNOT be filled without additional client confirmation:**

#### 1. [Gap Description]
- **Gap type:** Strategic/Tactical
- **Priority:** HIGH/MEDIUM/LOW
- **Why we can't verify:** [Not mentioned on website / Unclear from website / Contradictory information]
- **Recommendation:** ❌ Do not create ad angles for this gap without client confirmation
- **Action needed:** Ask client directly OR skip this gap

#### 2. [Gap Description]
[Same structure]

---

### Verification Summary

**Total Gaps Analyzed:** X
**Gaps Client Can Fill:** X (X%)
**Gaps Cannot Verify:** X (X%)

**Fillable Gap Breakdown:**
- Strategic gaps fillable: X
- Tactical gaps fillable: X

**Cannot Verify Breakdown:**
- High priority gaps we can't verify: X
- Medium/Low priority gaps we can't verify: X

**Recommendation:**
- ✅ Proceed to Phase 5 for [X] verified gaps
- ⚠️ Consider reaching out to client for [X] unverifiable high-priority gaps
- ❌ Skip [X] unverifiable low-priority gaps

---

### Example Ad Elements (Verified)

**Based on verified capabilities, these ad elements CAN be used:**

**Headlines (verified):**
- "[Verified claim from website]" - Source: [URL]
- "[Verified claim from website]" - Source: [URL]

**Descriptions (verified):**
- "[Verified benefit from website]" - Source: [URL]
- "[Verified feature list from website]" - Source: [URL]

**CTAs (verified):**
- "[Verified offer from website]" - Source: [URL]
  Example: "Start Free 30-Day Trial" (if 30-day trial is on pricing page)

**Social Proof (verified):**
- "[Verified proof from website]" - Source: [URL]
  Example: "Used by 5,000+ businesses" (if on about page)

---

### Cannot Use Without Verification

**These elements CANNOT be used in ads (not verified on website):**

❌ [Claim] - Not found on website
❌ [Claim] - Not found on website

**Examples of what NOT to assume:**
- ❌ "24/7 support" (unless explicitly stated)
- ❌ "Best in class" (unless award/rating proves this)
- ❌ "Most integrations" (unless count is provided and verified as highest)
- ❌ Industry-standard features (e.g., "automated reporting" unless mentioned)

---

### Compliance with Ad Copy Verification Standard

**✅ This analysis complies with Agency B's ad copy verification standard by:**
- Using ONLY information explicitly found on client website
- Including source citations for all claims
- Flagging unverifiable gaps clearly
- Never assuming industry standards apply
- Never using templates or best practices as justification

**❌ This analysis does NOT:**
- Assume capabilities based on competitor tactics
- Use generic SaaS feature templates
- Recommend unverified angles

**Next Step:** Proceed to Phase 5 (Angle Development) using ONLY verified gaps.
```

---

## Important Rules

1. **Never assume.** If it's not on the website, it cannot be verified.

2. **Use exact quotes.** Copy phrases directly from the website as evidence.

3. **Include source citations.** Every claim must have a URL + section reference.

4. **Distinguish explicit from implicit.** Only use explicit claims. Don't infer.
   - ✅ Explicit: "30-day free trial" (stated clearly)
   - ❌ Implicit: "Try it free" (duration not specified = cannot verify "30-day")

5. **Flag unverifiable high-priority gaps.** If a high-value gap cannot be verified, recommend asking the client directly.

6. **Map ALL gaps from Phase 3.** Go through each gap and determine fillability.

7. **Organize capabilities by category.** Makes it easy to reference in Phase 5.

8. **Be conservative with "Can Fill?"** When in doubt, mark ❌ Cannot verify. Better to under-recommend than over-recommend.

9. **Use WebFetch or Firecrawl.** Don't ask user to manually provide info. Scrape automatically.

10. **If scraping fails, state limitation clearly.** "Unable to scrape [page] - recommend manual review."

---

## Example Analysis

**Client:** Example SaaS
**Website:** example-client.com
**Competitive Gaps:** 5 identified from Phase 3

---

### Website Scrape Summary

**Pages Scraped:**
- ✅ Homepage (example-client.com)
- ✅ Features (example-client.com/features)
- ✅ Pricing (example-client.com/pricing)
- ✅ About (example-client.com/about)

**Total Capabilities Verified:** 12

---

### Verified Capabilities Inventory

#### Features & Capabilities
- ✅ "Mobile app (iOS & Android)" - Source: example-client.com/features#mobile
- ✅ "Digital vehicle inspections" - Source: example-client.com/features#dvi
- ✅ "Cloud-based platform" - Source: example-client.com/features#cloud
- ✅ "Inventory management" - Source: example-client.com/features#inventory

#### Benefits & Outcomes
- ✅ "Streamline your shop operations" - Source: example-client.com/#hero
- ✅ "Save time on paperwork" - Source: example-client.com/features#benefits

#### Social Proof & Credibility
- ✅ "Used by 5,000+ auto shops" - Source: example-client.com/about#customers
- ✅ "4.8/5 star rating" - Source: example-client.com/#social-proof

#### Pricing & Offers
- ✅ "30-day free trial" - Source: example-client.com/pricing#trial
- ✅ "Unlimited users included" - Source: example-client.com/pricing#plans

#### Technical Details
- ✅ "Cloud-based SaaS" - Source: example-client.com/features#platform
- ✅ "100+ integrations" - Source: example-client.com/integrations

---

### Gap-to-Capability Mapping

| # | Gap Description | Gap Type | Priority | Can Fill? | Evidence | Source |
|---|-----------------|----------|----------|-----------|----------|--------|
| 1 | No promotional hooks (free trial) | Tactical | HIGH | ✅ Yes | "30-day free trial" | example-client.com/pricing |
| 2 | Limited social proof in ads | Strategic | HIGH | ✅ Yes | "5,000+ auto shops" + "4.8/5 star rating" | example-client.com/about + homepage |
| 3 | No mobile app emphasis | Strategic | MEDIUM | ✅ Yes | "Mobile app (iOS & Android)" | example-client.com/features#mobile |
| 4 | No urgency language | Tactical | MEDIUM | ❌ No | Not found - no time-limited offers on site | N/A |
| 5 | No AI/automation claims | Strategic | LOW | ❌ No | Not found - no AI features mentioned | N/A |

---

### Fillable Gaps (Verified)

#### 1. No promotional hooks (free trial)
- **Gap type:** Tactical
- **Priority:** HIGH
- **Evidence:** "30-day free trial, no credit card required"
- **Source:** example-client.com/pricing#trial
- **Competitive advantage:** No competitor mentions free trial in ads, but Example SaaS clearly offers it
- **Recommendation readiness:** ✅ Ready for angle development

#### 2. Limited social proof in ads
- **Gap type:** Strategic
- **Priority:** HIGH
- **Evidence:** "Used by over 5,000 auto shops nationwide" + "4.8 out of 5 stars from verified users"
- **Source:** example-client.com/about#customers + example-client.com/#social-proof
- **Competitive advantage:** Stronger social proof than competitors who either don't show numbers or show lower counts
- **Recommendation readiness:** ✅ Ready for angle development

#### 3. No mobile app emphasis
- **Gap type:** Strategic
- **Priority:** MEDIUM
- **Evidence:** "Manage your shop from anywhere with our iOS and Android mobile app"
- **Source:** example-client.com/features#mobile
- **Competitive advantage:** Competitors mention cloud/web but don't emphasize mobile app availability
- **Recommendation readiness:** ✅ Ready for angle development

---

### Cannot Verify (Unverifiable Gaps)

#### 1. No urgency language
- **Gap type:** Tactical
- **Priority:** MEDIUM
- **Why we can't verify:** No time-limited offers or seasonal promotions found on website
- **Recommendation:** ❌ Do not create urgency-based angles without client confirmation of promotional calendar
- **Action needed:** Ask client if they run time-limited promotions

#### 2. No AI/automation claims
- **Gap type:** Strategic
- **Priority:** LOW
- **Why we can't verify:** No mention of AI, machine learning, or automated features on website
- **Recommendation:** ❌ Do not create AI-focused angles
- **Action needed:** Skip this gap (low priority + not supported by website)

---

### Verification Summary

**Total Gaps Analyzed:** 5
**Gaps Client Can Fill:** 3 (60%)
**Gaps Cannot Verify:** 2 (40%)

**Fillable Gap Breakdown:**
- Strategic gaps fillable: 2 (Social proof, Mobile app)
- Tactical gaps fillable: 1 (Free trial)

**Cannot Verify Breakdown:**
- High priority gaps we can't verify: 0
- Medium/Low priority gaps we can't verify: 2 (Urgency, AI)

**Recommendation:**
- ✅ Proceed to Phase 5 for 3 verified gaps
- ⚠️ Consider asking client about promotional calendar (urgency gap)
- ❌ Skip AI gap (low priority + not supported)

---

### Example Ad Elements (Verified)

**Headlines (verified):**
- "Auto Shop Software - Used by 5,000+ Shops" - Source: example-client.com/about
- "Manage Your Shop From Anywhere - iOS & Android App" - Source: example-client.com/features#mobile
- "Shop Management Software - Rated 4.8/5 Stars" - Source: example-client.com/#social-proof

**Descriptions (verified):**
- "Start Your Free 30-Day Trial. No Credit Card Required." - Source: example-client.com/pricing
- "Unlimited Users. Cloud-Based. 100+ Integrations." - Source: example-client.com/pricing + example-client.com/integrations
- "Save Time On Paperwork. Streamline Your Shop Operations." - Source: example-client.com/#hero

**CTAs (verified):**
- "Start Free 30-Day Trial" - Source: example-client.com/pricing#trial

**Social Proof (verified):**
- "5,000+ Shops" - Source: example-client.com/about
- "Rated 4.8/5 Stars" - Source: example-client.com/#social-proof

---

### Cannot Use Without Verification

❌ "AI-Powered Scheduling" - Not found on website
❌ "24/7 Live Support" - Support page mentions "business hours" only
❌ "Limited Time: 50% Off" - No promotional offers found
❌ "Fastest Setup in the Industry" - No setup time mentioned

---

**Next Step:** Proceed to Phase 5 (Angle Development) using ONLY the 3 verified gaps.
