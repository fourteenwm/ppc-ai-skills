---
name: ad-copy-verification-standard
description: Mandatory verification requirements for all ad copy creation (RSAs, extensions, callouts, structured snippets). Auto-invoke when generating ad copy. Enforces website-sourced claims only — no assumptions, no templates-as-content, no unverified placeholders. Core principle — Empty > Inaccurate.
allowed-tools: [Read]
---

# Ad Copy Verification Standard

**Purpose:** Mandatory verification requirements for ALL ad copy creation (RSAs, extensions, callouts, etc.).

**Type:** Universal skill — auto-invoked for any ad copy generation task

**Status:** MANDATORY — All ad copy must follow this standard

---

## Core Principle

**ABSOLUTE REQUIREMENT: Only create ad copy based on EXPLICITLY VERIFIED information from the business's website.**

**NEVER create ad copy based on:**
- ❌ "Common industry practices"
- ❌ "What most businesses do"
- ❌ Assumptions about services offered
- ❌ Template libraries used as source of truth
- ❌ Generic best practices without verification
- ❌ Generic placeholders or unverified ratings/counts

**CRITICAL:** This verification requirement applies to ALL ad copy elements - headlines, descriptions, CTAs, flexible headlines, and ALL other copy. No exceptions.

---

## Universal Verification Rules

### Rule 1: Website Verification is MANDATORY

Before creating ANY ad copy (headlines, descriptions, callouts, structured snippets):

1. **Scrape the website using Firecrawl**
2. **Extract explicit claims, services, features, credentials**
3. **Document source for each claim** (which page, exact wording)
4. **Only use verified information in ad copy**

### Rule 2: Source Citation Required

Every piece of ad copy must have a source citation:

```
✅ CORRECT:
Headline: "ASE-Certified Technicians"
- Source: About page states "Our ASE-certified master technicians"
- Verified: YES

❌ WRONG:
Headline: "ASE-Certified Technicians"
- Reason: Most auto shops have ASE certification
- Verified: NO (ASSUMPTION)
```

### Rule 3: When Website Scraping Fails

If Firecrawl cannot access the website OR website has limited content:

**DO:**
- State limitation clearly to user
- Only use existing account data (current ads, extensions)
- Suggest manual website review by user
- Create generic structural improvements only

**DO NOT:**
- Guess at services/features
- Use industry templates as content source
- Make assumptions about business offerings
- Recommend unverified claims

### Rule 4: Template Usage Guidelines

**Templates are for FORMATTING, not CONTENT:**

✅ **Correct Use:**
- Website says "family owned since 1986"
- Template suggests format: "Family-Owned Since 1986" (proper capitalization)
- Result: Use template formatting for verified claim

❌ **Incorrect Use:**
- Template has "Open Saturdays"
- Website doesn't mention Saturday hours
- Result: DO NOT add "Open Saturdays" just because template has it

### Rule 5: "Free" Exclusion Rule

**EXCLUDE any copy referring to "Free" - even if verified on the website:**

❌ **Prohibited (even if on website):**
- "Free Estimates"
- "Get Your Free Quote Today!"
- "Free Diagnostics"
- "Free Inspections"
- "Free Consultation"

✅ **Alternative Copy:**
- "Get Your Quote Today!"
- "Request A Quote!"
- "Call For Your Estimate!"
- "Schedule Your Inspection!"

**Reason:** Targeting premium customers, not price-sensitive shoppers. "Free" copy attracts wrong customer avatar regardless of whether claim is true.

**Application:** This filter applies AFTER verification - first verify the claim exists on website, then exclude if it contains "Free".

---

## Ad Copy Types - Specific Requirements

### Responsive Search Ads (RSAs)

**Headlines (15 max):**
- Each headline must cite website source
- No generic headlines without verification ("Great Service", "Quality Work")
- Use actual business differentiators from website

**Descriptions (4 max):**
- Must reference verified services/features
- No generic value propositions without evidence
- Include verified CTAs only

**Example Verification Process:**

```
WRONG Approach:
"Let's add these common auto shop headlines:
- Expert Auto Repair (generic - no verification)
- Open 7 Days a Week (unverified assumption)
- Free Estimates (violates Rule 5 - no 'Free' copy)
- Rated 5★ By Happy Customers (generic placeholder - no source)"

RIGHT Approach:
"Website scrape results:
- Page: About - 'ASE-certified technicians since 1986'
- Page: Services - 'Specializing in diesel repair'
- Page: Contact - 'Monday-Friday 8AM-6PM'
- Page: Homepage - Customer testimonial: 'Best shop in town'

Verified Headlines:
- ASE-Certified Since 1986 (Source: About page)
- Diesel Repair Specialists (Source: Services page)
- Open Weekdays 8AM-6PM (Source: Contact page)
- \"Best Shop In Town\" - Customer (Source: Homepage testimonial)"
```

### Callout Extensions

**Requirements:**
- Maximum 25 characters
- Every callout must have website source
- No industry standard callouts without verification

**Forbidden Without Verification:**
- "Same Day Service"
- "Open Saturdays"
- "Lifetime Warranty"
- Any hours/amenities/services not explicitly stated

**Forbidden Even WITH Verification (Rule 5):**
- Any copy containing "Free" (estimates, quotes, diagnostics, etc.)

### Structured Snippets

**Service catalog header:**
- Only include services explicitly listed on website
- Do NOT add "common" services without verification
- Minimum 3 services (from website only)

**Brands header:**
- Only include brands explicitly mentioned on website
- Do NOT infer brands from "all makes/models" language
- Need specific brand names stated

**Types header:**
- Only include vehicle types if explicitly mentioned
- Can infer basic types (Sedans, SUVs, Trucks) from "all vehicles" ONLY IF defensible
- Flag as "inferred" if not explicit

### Sitelinks

**Requirements:**
- Link text must match actual page/service on website
- Description must reference verified content
- Landing page URL must exist and be relevant

---

## Verification Workflow

### Step 1: Website Discovery
Get the business website URL — either from the Google Ads account (query `ad_group_ad.ad.final_urls`) or from the user directly.

### Step 2: Website Scraping
Scrape the site using Firecrawl, Jina Reader, or any scraper that returns clean markdown. The goal is structured claims you can cite.

**Output includes:**
- Services offered (explicit list)
- Credentials (ASE, BBB, NAPA, AAA, etc.)
- Features (shuttle, WiFi, loaner cars, warranties)
- History (established year, family-owned)
- Hours (operating schedule)
- Specializations (diesel, import, fleet, etc.)

### Step 3: Extract Verified Claims

Review Firecrawl JSON output and extract:

```json
{
  "verified_claims": [
    {
      "claim": "ASE-Certified Technicians",
      "source": "About page",
      "exact_wording": "Our ASE-certified master technicians",
      "confidence": "verified"
    },
    {
      "claim": "Open Weekdays 8AM-6PM",
      "source": "Contact page",
      "exact_wording": "Monday-Friday: 8:00 AM - 6:00 PM",
      "confidence": "verified"
    }
  ],
  "inferred_claims": [
    {
      "claim": "All Makes & Models",
      "source": "Services page",
      "inference": "States 'domestic, foreign, and diesel' - implies all makes",
      "confidence": "inferred"
    }
  ]
}
```

### Step 4: Create Ad Copy

Only use verified_claims for ad copy. Flag inferred_claims for user review.

### Step 5: Document Sources

Present ad copy with source citations:

```
=== PROPOSED HEADLINES ===

1. "ASE-Certified Technicians"
   ✅ Source: About page - "Our ASE-certified master technicians"

2. "Serving [City] Since 1986"
   ✅ Source: Homepage - "Family owned and operated since 1986"

3. "Diesel Repair Specialists"
   ✅ Source: Services page - "Specializing in diesel truck repair"

=== EXCLUDED ===

4. "Open 7 Days a Week"
   ❌ NOT FOUND on website - Violates Rule 1 (verification required)

5. "Free Estimates"
   ❌ FOUND on website BUT excluded - Violates Rule 5 (no "Free" copy)

6. "Rated 5★ By Happy Customers"
   ❌ Generic placeholder - Violates Rule 1 (no verified source for rating/count)
```

---

## Quality Assurance Checklist

Before submitting ANY ad copy to user:

- [ ] Website scraping completed successfully
- [ ] Every claim has source citation (including flexible headlines and all copy)
- [ ] No assumptions or "industry standards" used
- [ ] No generic placeholders (e.g., "Happy Customers", "Rated 5★" without verified count)
- [ ] Template library used for formatting only (not content)
- [ ] All copy containing "Free" has been excluded (Rule 5)
- [ ] Inferred claims clearly flagged as such
- [ ] User notified of any limitations (website unavailable, etc.)

---

## Error Handling

### Website Unavailable

```
⚠️ WEBSITE SCRAPING LIMITATION

Website: [URL]
Status: Unable to access / Heavy JavaScript / No content

IMPACT:
- Cannot verify services, features, or credentials
- Recommendations limited to existing account data only
- No new claims or differentiators can be suggested

RECOMMENDATION:
Please manually review [URL] and provide:
- Services offered
- Credentials (ASE, BBB, etc.)
- Unique features (shuttle, warranty, etc.)
- Operating hours
- Any specializations

Then I can create verified ad copy based on your input.
```

### Partial Website Access

```
⚠️ LIMITED WEBSITE DATA

Successfully scraped: Homepage, Contact page
Unable to access: Services page, About page

VERIFIED CLAIMS:
- [List what was found]

CANNOT VERIFY:
- Detailed service list
- Credentials
- Company history

RECOMMENDATION:
Proceeding with verified claims only. Suggest manual review
of [URL]/services and [URL]/about for additional content.
```

---

## Examples by Ad Copy Type

### Example 1: Responsive Search Ad Creation

**User Request:** "Create RSAs for [auto repair shop client]"

**Correct Workflow:**

1. ✅ Scrape the business website
2. ✅ Extract verified claims:
   - "Established 1978" → Headline: "Serving You Since 1978"
   - "AAA-Approved" → Headline: "AAA-Approved Repair Shop"
   - "36 months/36,000 miles warranty" → Description: "36-month warranty on all repairs"
3. ✅ Document sources for each headline/description
4. ✅ Present to user with verification status

**Incorrect Workflow:**

1. ❌ Look at RSA best practices templates
2. ❌ Add generic headlines: "Expert Auto Repair", "Quality Service"
3. ❌ Add assumed features: "Same Day Service", "Free Estimates"
4. ❌ No website verification

### Example 2: Callout Extension Audit

**User Request:** "Add callouts for [auto repair shop client]"

**Correct Workflow:**

1. ✅ Scrape the business website
2. ✅ Find: "BBB accredited", "Financing available", "Fleet services"
3. ✅ Create callouts:
   - "BBB Accredited Business" (Source: Homepage)
   - "Financing Available" (Source: Services page)
   - "Fleet Service Available" (Source: Services page — "fleet service department")
4. ✅ Do NOT add: "Open Saturdays" (not on website)

**Incorrect Workflow:**

1. ❌ Use callout template library
2. ❌ Add "common" callouts without verification: "Same Day Service", "Open Saturdays"
3. ❌ Add "Free Estimates" even if on website (violates Rule 5)
4. ❌ No verification from actual website

---

## Integration with Agents

Any agent that creates ad copy must:

1. **Import this skill at start:**
   ```markdown
   Before creating any ad copy, review the ad-copy-verification-standard skill
   for mandatory requirements.
   ```

2. **Follow verification workflow:**
   - Website scraping → Claim extraction → Source documentation → User review

3. **Never skip verification:**
   - Even for "simple" or "obvious" claims
   - Even when user seems to be in a hurry
   - Even when template seems perfect

---

## Code Implementation Requirements

**CRITICAL: When writing code that generates ad copy, these rules MUST be enforced in the code itself:**

### No Fallbacks Rule

```python
# ❌ WRONG - Using fallbacks when data is missing
if not social_proof:
    headlines.append("5-Star Reviews")  # Generic placeholder

# ✅ CORRECT - Empty string when data is missing
if not social_proof:
    headlines.append("")  # Leave empty, do not fabricate
```

### Policy: Empty > Inaccurate

**Better to have an empty headline field than an unverified claim.**

- If website data is missing → use empty string
- If review data is missing → use empty string
- If warranty not found → use empty string
- NEVER substitute generic placeholders

### Code Must Reference This Skill

All RSA generation scripts should include a header reference:

```python
"""
MUST FOLLOW: ad-copy-verification-standard

Key rules:
  - NO generic placeholders
  - NO fallbacks when data missing
  - Empty string > unverified claim
"""
```

---

## Enforcement

**This standard is MANDATORY for:**
- ✅ Responsive Search Ad creation
- ✅ Callout extension recommendations
- ✅ Structured snippet recommendations
- ✅ Sitelink creation
- ✅ Any ad copy generation task

**Agents that must comply:**
- Any RSA creation agent
- Any ad copy generation agent
- Any portfolio audit agent that surfaces copy recommendations

**Non-compliance consequences:**
- User will request removal of unverified claims
- Creates cleanup work and wastes time
- Damages trust in AI-generated recommendations

---

## Success Criteria

Ad copy creation is successful when:

1. ✅ Every claim is verified from website scraping
2. ✅ Every claim has documented source
3. ✅ No assumptions or "industry standards" used
4. ✅ User can trust all recommendations are factual
5. ✅ Cleanup/removal work is not needed post-creation

---

## Related Skills in This Repo

- **[mutation-safety](../mutation-safety/)** — Two-step approval protocol that prevents writing unverified copy to live accounts
- **[investigation-methodology](../investigation-methodology/)** — Hypothesis-driven framework for diagnosing ad copy issues

---

Built by [Kurt Henninger](https://fourteenwebmedia.com). More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
