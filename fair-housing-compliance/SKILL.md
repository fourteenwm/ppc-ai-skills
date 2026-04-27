---
name: fair-housing-compliance
description: Fair Housing Act compliance requirements for property management advertising. Auto-invoke when creating campaigns, modifying targeting settings, setting up audiences, recommending changes to location/demographic targeting, or ANY discussion of campaign targeting for property management accounts. CRITICAL LEGAL REQUIREMENT - ensures all Google Ads accounts comply with federal housing discrimination laws.
allowed-tools: [Read]
---

# Fair Housing Compliance Skill

**Purpose:** Ensures all property management advertising complies with Fair Housing Act regulations. Auto-invokes when any targeting or audience discussion occurs.

**Type:** Legal compliance skill (CRITICAL - auto-invoked)

**Scope:** ALL property management accounts

---

## CRITICAL LEGAL REQUIREMENT

**All property management accounts are subject to Fair Housing Act regulations.** This is a **legal requirement**, not a client preference.

Violations can result in:
- Federal lawsuits
- Substantial fines
- Client liability
- Account suspension

---

## PROHIBITED Targeting/Signals

**NEVER use these targeting options for property management accounts:**

### Demographic Targeting (PROHIBITED)
- Age targeting or signals (any age ranges, age demographics, age brackets)
- Income/Household income signals (income brackets, affluence targeting, HHI)
- Parental status signals (parents, families with children, "parents of toddlers", etc.)
- Familial status signals (household composition, family size, "married", etc.)
- Gender-specific targeting (when used in discriminatory manner)

### Geographic Targeting (PROHIBITED)
- Zip code targeting (specific zip codes - can be income proxy)
- Neighborhood-level targeting (below city level, unless broad metro area)

### Audience Signals (PROHIBITED)
- Any demographic signals that could be considered discriminatory under Fair Housing laws
- Affinity audiences based on demographic characteristics
- Income-based custom audiences
- Age-proxy audiences (e.g., "College Graduates" may imply age range)

---

## COMPLIANT Targeting/Signals

**Safe to use for property management accounts:**

### Behavioral Targeting (COMPLIANT)
- In-market audiences (apartment shoppers, real estate searchers) - behavioral, not demographic
- Search theme/keyword signals (location + apartment type queries like "2 bedroom apartments [city]")
- Website visitor audiences (remarketing to past site visitors)
- Custom audiences based on website behavior (not demographic data)

### Geographic Targeting (COMPLIANT)
- Metro areas (broad regional targeting)
- Cities (city-level targeting)
- Broad regions (states, multiple-county areas)
- Radius targeting (e.g., 40-mile radius from property address)

### Campaign Optimization (COMPLIANT)
- Conversion-based optimization (optimize for leads/conversions without demographic filters)
- Customer match (existing customer lists - if non-discriminatory)
- Similar audiences (based on converters - if source audience is compliant)

---

## VERIFY BEFORE USE (Gray Areas)

These audience types may be compliant but require verification:

### Life Event Audiences
- "Recently Moved" - Likely compliant (behavioral signal, not protected class)
- "Job Change" - Likely compliant (behavioral signal)
- "College Graduates" - May NOT be compliant (could be age proxy - avoid unless verified)
- Any life event - Evaluate: Could this be a proxy for protected class?

**Decision rule:** If unsure about a targeting option, **default to NOT using it**. Legal risk is too high.

---

## Key Principle: Target the Product, Not the People

**COMPLIANT:** Target properties/apartments (the product)
- "2 bedroom apartments in [city]"
- "Luxury apartments near downtown"
- "Pet-friendly rentals in [neighborhood]"

**NON-COMPLIANT:** Target people demographics
- "Millennials looking for apartments" (age proxy)
- "Young professionals" (age proxy)
- "Families with children" (familial status)
- "High-income renters" (income discrimination)

**Framework:** Optimize for **behavior and intent**, never for **who someone is**.

---

## Campaign Setup Checklist

### When Creating New Campaigns:
- [ ] No age targeting applied
- [ ] No income signals or audience segments
- [ ] No parental/familial status signals
- [ ] No zip code-level geographic targeting
- [ ] Only behavioral audiences (in-market, search themes)
- [ ] Only compliant geo targeting (metro/city level)
- [ ] Campaign focuses on property features, not demographics

### When Optimizing PMAX/Demand Gen:
- [ ] Focus on conversion value optimization and search themes
- [ ] Use in-market audiences for apartment shopping behavior
- [ ] Avoid any audience segment that filters by age, income, family status, or zip codes
- [ ] Review auto-applied audiences for demographic signals (remove if found)

### When Recommending Changes:
- [ ] Verify recommendation doesn't introduce demographic targeting
- [ ] Check that geographic targeting remains compliant (metro/city level)
- [ ] Confirm audience signals are behavioral, not demographic
- [ ] Document compliance reasoning in recommendation

---

## Examples: Compliant vs. Non-Compliant

### COMPLIANT Campaign Example

**Campaign Name:** Pmax: Example Property Apartments
**Geo Targeting:** 40-mile radius from property address (metro area)
**Audience Signals:**
- In-market: Real Estate > Apartments for Rent
- In-market: Travel > Business Travel (relocating professionals)
- Search themes: "apartments [city]", "2 bedroom [neighborhood]", "pet friendly rentals"
- Remarketing: Website visitors (last 30 days)

**Why compliant:** All behavioral/intent signals, no demographics, broad geo

---

### NON-COMPLIANT Campaign Example

**Campaign Name:** Pmax: Example Property Young Professionals
**Geo Targeting:** Specific zip codes (10001, 10003, 10009) — PROHIBITED
**Audience Signals:**
- Age: 25-34 — PROHIBITED
- Income: Top 30% household income — PROHIBITED
- Affinity: Young Urban Professionals — PROHIBITED
- Parental status: No children — PROHIBITED

**Why non-compliant:** Age, income, parental status, zip code targeting all violate Fair Housing Act

---

## When to Flag Violations

### Automatic Flags:
- ANY mention of age targeting in recommendations
- ANY income-based audience suggestions
- ANY parental/familial status signals
- ANY zip code targeting recommendations

### Investigation Flags:
- Existing campaigns with suspicious audience signals
- PMAX/DGen campaigns with auto-applied demographic audiences
- Remarketing audiences that may segment by demographics

**Action:** If violation detected, immediately flag and recommend removal. Document legal compliance reasoning.

---

## When This Skill Auto-Loads

- Creating new campaigns (any type)
- Modifying targeting settings
- Recommending audience additions
- Optimizing PMAX/Demand Gen signals
- Discussing campaign structure changes
- Analyzing campaign settings
- User mentions "targeting", "audiences", "demographics", "geo", or "location"

---

## Related Documentation

- **Google Ads Policy Center** — Fair Housing advertising policies
- **U.S. Department of Housing and Urban Development (HUD)** — Fair Housing Act regulations
- **Fair Housing Act (Title VIII of Civil Rights Act of 1968)** — Federal law

---

## Important Notes

1. **When in doubt, exclude it** — If you're unsure if a targeting option is compliant, default to NOT using it
2. **Behavioral > Demographic** — Always prefer behavioral signals over any demographic characteristic
3. **Broad > Narrow** — Use broad geographic targeting (metro/city) vs narrow (zip codes)
4. **Document compliance** — When making targeting recommendations, explicitly state Fair Housing compliance reasoning
5. **Stay updated** — Fair Housing regulations and Google Ads policies may evolve — review periodically

---

**Legal Basis:** Fair Housing Act (Title VIII of Civil Rights Act of 1968)
**Status:** Active — CRITICAL COMPLIANCE SKILL
