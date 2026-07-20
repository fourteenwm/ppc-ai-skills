---
name: competitor-analysis-v2
description: Comprehensive competitive analysis combining website intelligence, 22-attribute ad copy framework, automated screenshots via Playwright, and verification rigor. Auto-invoke when user says "analyze competitors", "competitor report", "competitive intelligence", "market positioning analysis", or "client gift". Outputs Strategic Client Gift OR tactical Ads Angle Brief.
allowed-tools: [Bash, Read, Write, WebFetch, WebSearch, Task]
---

# Competitor Analysis v2

**Auto-invoke when:** User asks for competitive analysis, competitor research, market positioning analysis, or says "competitor report", "analyze competitors", "competitive intelligence", or "client gift".

---

## What This Skill Does

Comprehensive competitive analysis combining:
- **Website Intelligence** - Deep extraction of competitor messaging, positioning, and gaps
- **Ad Copy Analysis** - 22-attribute framework for Google Ads evaluation
- **Visual Documentation** - Automated screenshots via Playwright
- **Two Output Types** - Strategic Client Gift OR tactical Ads Angle Brief
- **Verification Rigor** - All recommendations verified against client website

**Credentials Required:** None. The whole workflow runs on Playwright plus web fetches. Competitor ad copy for the optional ad-scoring phase comes from a SERP tool or is pasted in — no Google Ads API access needed.

---

## When to Use This Skill

### Auto-invoke triggers:
- "Analyze competitors for [client]"
- "Competitive analysis for [market]"
- "What are [client]'s competitors doing?"
- "Create a competitor report"
- "Client gift for [client]"
- "Market positioning analysis"

### Use cases:

| Use case | Output |
|----------|--------|
| White-label deliverable for a partner agency's clients | Client Gift + Ads Brief |
| Relationship/retention tool for your own managed accounts | Client Gift (as a gift) |
| Positioning input before an ad copy build | Ads Brief |

---

## The 8-Phase Workflow

### Phase 1: Gather Inputs

**Required:**
```
- Client name
- Client URL
- Industry/market
- 5 competitor URLs (or request search assistance)
- Output type: "Client Gift" | "Ads Brief" | "Both"
```

**If user doesn't have competitor URLs:**
1. Use WebSearch to find 8-10 competitors in the same market
2. Present options with brief descriptions
3. Get approval on 5 to analyze

---

### Phase 2: Capture Screenshots (MANDATORY)

**Run the screenshot script:**

```bash
node .claude/skills/competitor-analysis-v2/scripts/screenshot.cjs \
  https://client.com \
  https://competitor1.com \
  https://competitor2.com \
  https://competitor3.com \
  https://competitor4.com \
  https://competitor5.com \
  --output /tmp/competitor-report/screenshots
```

**Prerequisites:**
```bash
# Check Playwright is installed
node -e "require('playwright')" 2>/dev/null && echo "Ready" || echo "Need install"

# If not installed:
npm install playwright
```

**Output:**
- 6 full-page screenshots (PNG)
- `screenshots.json` metadata file

---

### Phase 3: Extract Website Content (Parallel)

**Launch 6 parallel Task agents** to fetch all websites simultaneously:

```
For each URL (client + 5 competitors):
- subagent_type: "general-purpose"
- prompt: "Use WebFetch to analyze [URL]. Use this extraction prompt: [paste from prompts/website-extraction.md]. Return only the XML output."
```

**Why parallel:** Serial fetching takes 5-6 minutes. Parallel completes in ~1 minute.

**Output:** Structured XML data for each site including:
- Business name, headline, value proposition
- Services, trust signals, unique claims
- Social proof (ratings, review counts, testimonial themes)
- Risk reversal tactics (guarantees, offers)
- Emotional triggers, objection handling
- Target audience, positioning tier, brand tone

---

### Phase 4: Analyze Competitor Ads (If Available)

**If SERP API results or pasted ads are provided:**

1. Run `prompts/strategic-analysis.md` - 15 attributes (0-45 points)
2. Run `prompts/tactical-scan.md` - 7 attributes (0-21 points)
3. Score each competitor
4. Identify ad-specific gaps

**If no ads available:**
- Skip this phase
- Note: "Ad analysis not performed (no competitor ads provided)"
- Website analysis from Phase 3 is sufficient for Client Gift

---

### Phase 5: Gap Identification

**Use `prompts/gap-identification.md` enhanced with:**

#### A. Messaging Matrix
| Competitor | Headline | Main Claim | USP | CTA | Proof Type | Pricing? |
|------------|----------|------------|-----|-----|------------|----------|

**Analysis:**
- What claims appear in 3+ competitors? (Table stakes)
- What claims appear in only 1? (Differentiator)
- What's missing from all? (Opportunity)

#### B. Positioning Map
2x2 grid with appropriate axes:
- **Service:** Price vs Specialization
- **Speed:** Speed vs Quality
- **Local:** Scale vs Personalization

**Identify:**
- Where competitors cluster
- Where white space exists
- Where client currently sits (or should sit)

#### C. Gap Categories
- **Strategic gaps** - Positioning no competitor owns
- **Tactical gaps** - Weaknesses everyone shares
- **Whitespace** - Unmet market needs

---

### Phase 6: Client Verification (MANDATORY)

**Use `prompts/client-verification.md`**

**Process:**
1. Scrape client website (WebFetch/Firecrawl)
2. Extract verified capabilities with sources
3. Map gaps to capabilities:
   - ✅ **Can fill** - Gap + website evidence
   - ❌ **Cannot verify** - Gap but no evidence

**Output:**
- Verified capabilities inventory
- Gap-to-capability mapping
- Source citations for all claims
- "Cannot recommend" list

**CRITICAL:** No recommendations without verification. This phase is NON-NEGOTIABLE.

---

### Phase 7: Generate Output(s)

**Based on user's output preference:**

#### Output 1: Client Gift (10-15 pages)
Strategic document for the CLIENT. **NO Google Ads mechanics.**

Uses `templates/client-gift.md` structure:
1. Cover page
2. Executive summary (3 key findings)
3. Who we looked at (competitor profiles)
4. Screenshots grid (3x2)
5. Messaging matrix
6. Table stakes (what everyone says)
7. Opportunities (what no one says)
8. How competitors sell (pain/outcome/proof)
9. Positioning map
10. Emotional landscape
11. Customer concerns
12. Implications
13. Recommendations
14. Full screenshots comparison
15. Summary

**Tone:** Strategic, insight-driven, no jargon.

#### Output 2: Ads Angle Brief (1 page)
Tactical document for the PRACTITIONER.

Uses `templates/ads-angle-brief.md` structure:
1. Primary positioning axis
2. Top 3 angles (with proof required)
3. Angles NOT to pursue
4. Headlines by angle
5. Campaign-to-angle map
6. Compliance watch-outs
7. Ad-to-page rules

**Uses:** Verified angles from Phase 6 only.

---

### Phase 8: PDF Generation (For Client Gift)

**Generate professional PDF:**

1. Create HTML with embedded CSS from `templates/template.css`
2. Include screenshots at appropriate positions
3. Render positioning maps as CSS grids
4. Generate PDF via Playwright:

```javascript
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + process.cwd() + '/[client]-competitor-report.html', { waitUntil: 'networkidle' });
  await page.pdf({
    path: '[client]-competitor-report.pdf',
    format: 'A4',
    printBackground: true,
    margin: { top: '0', right: '0', bottom: '0', left: '0' }
  });
  await browser.close();
})();
```

---

## Output Selection

**Ask user at start:**

```
Which output would you like?

1. Client Gift - Strategic document for the client (10-15 pages, PDF)
2. Ads Angle Brief - Tactical document for you (1 page, markdown)
3. Both - Full analysis with both outputs

For white-label partner work, "Both" is recommended.
For a client-relationship gift, "Client Gift" alone is usually right.
```

---

## Common Use Cases

### Use Case: White-Label Partner Work

**Context:** Generate deliverables for a partner agency to re-brand and deliver to their clients

**Workflow:**
1. Run full analysis for the target vertical
2. Generate both outputs (Client Gift for partner to deliver, Ads Brief for internal use)
3. Save deliverables to your project's output folder (e.g., `./deliverables/competitor-analysis/`)

### Use Case: Internal Portfolio Tool

**Context:** Run as a relationship/retention tool across your managed accounts

**Workflow:**
1. Run full analysis for each account's vertical
2. Generate Client Gift (as relationship gift to the client)
3. Ads Brief optional (for your internal optimization work)
4. Save to your output folder

---

## Quality Checklist

Before delivery:
- [ ] All 6 screenshots captured successfully
- [ ] Website content extracted for all 6 URLs
- [ ] Client verification completed (Phase 6)
- [ ] All recommendations have source citations
- [ ] Client Gift has NO Google Ads mechanics
- [ ] Ads Brief uses ONLY verified angles
- [ ] Positioning maps are accurate
- [ ] No unverified claims in any output

---

## File Locations

**Prompts:**
- `prompts/website-extraction.md` - Website content extraction (XML)
- `prompts/strategic-analysis.md` - 15 strategic attributes
- `prompts/tactical-scan.md` - 7 tactical attributes
- `prompts/gap-identification.md` - Gap analysis + positioning
- `prompts/client-verification.md` - Mandatory verification
- `prompts/angle-development.md` - Verified angle creation
- `prompts/analysis-framework.md` - Templates for matrices

**Scripts:**
- `scripts/screenshot.cjs` - Playwright screenshot capture

**Templates:**
- `templates/client-gift.md` - Client Gift structure
- `templates/ads-angle-brief.md` - Ads Brief structure
- `templates/template.css` - PDF styling

**Sales:**
- `sales/service-page-copy.md` - Marketing copy templates for offering this as a service

---

## Integration

### Ad Copy Verification Standard
This skill enforces the `ad-copy-verification-standard` skill from this catalog (install it alongside):
- All claims verified from client website
- Source citations required
- "Cannot recommend" list for unverifiable gaps

### Related Skills
- `ad-copy-generation-framework` - 23-element RSA copywriting framework for turning verified angles into copy
- `rsa-single-account` - Full single-account RSA build; use after this when the brief feeds ad creation
- `fair-housing-compliance` - Required when the client is property management / housing

---

## Example Usage

### Full Analysis

**User:** "Run competitor analysis for Smith Auto Repair"

**Claude:**
1. "Which output - Client Gift, Ads Brief, or Both?" → Both
2. "Client URL?" → smithautorepair.com
3. "Competitor URLs (or should I search)?" → [5 URLs provided]
4. Runs 8-phase workflow
5. Delivers Client Gift PDF + Ads Brief markdown

### Quick Gift

**User:** "Create a client gift for Example Property"

**Claude:**
1. Output: Client Gift only
2. Runs phases 1-3, 5-7 (skips ad analysis)
3. Delivers strategic Client Gift PDF

---

## Version History

- **v2.0** (2026-01) - Merged the 22-attribute ad analysis framework and the strategic competitor report into a single 8-phase workflow
- **v1.0** (2025-12) - Original 22-attribute ad copy analysis framework

---

**Compliance:** All recommendations pass the ad copy verification standard — no unverified claims
**Outputs:** Client Gift, Ads Angle Brief, or Both
