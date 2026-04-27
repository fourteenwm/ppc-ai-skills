---
name: client-communication-standards
description: Client-facing report formatting standards. Auto-invoke when creating client summaries, investigation reports, monthly reviews, performance analyses, or any communication for stakeholders. Applies mandatory Background → Analysis → Conclusions framework with required "What We Looked At" data source attribution for all findings.
allowed-tools: [Read]
---

# Client Communication Standards Skill

**Purpose:** Ensures all client-facing communications follow the "Background → Analysis → Conclusions" framework with proper data transparency.

**Type:** Communication standards skill (auto-invoked for client reports)

---

## Core Framework: Background → Analysis → Conclusions

**When to use:** Investigation summaries, monthly reviews, strategy presentations, performance reports for client stakeholders

**CRITICAL:** Use EXACTLY 3 sections (no more, no less)

---

## Section 1: Background

**Purpose:** Set context for the reader

**What to include:**
- Client concern (what they're seeing/experiencing)
- Investigation scope (what we analyzed and why)
- Keep concise (2-3 paragraphs maximum)

**Example:**
```
## Background

Example Account PMAX campaign performance declined from 23x ROAS in August to
16x ROAS in October, prompting client concern about campaign efficiency.
The client wanted to understand whether this decline was campaign-related
or market-driven.

We conducted a comprehensive analysis of search demand trends, competitive
landscape, and campaign performance metrics across multiple time periods
to identify root causes.
```

---

## Section 2: Analysis

**Purpose:** Present data findings with full transparency

**REQUIRED for every finding:**
- **"What We Looked At:"** statement showing data source
- Logical sequence of findings
- Data presented in tables when comparing periods/channels
- Each subsection ends with **"Finding:"** statement (key insight)

### "What We Looked At" Requirements

**MUST specify:**
1. Which report/tool (Search term reports, Google Trends, Google Ads API, GA4, etc.)
2. Time period analyzed (last 30 days, Sep 1 - Oct 1, year-over-year, etc.)
3. Methodology used (categorization, statistical analysis, correlation, etc.)
4. Any filters/segments applied

**Format:**
```
**What We Looked At:** [Data source], [time period], [methodology]
```

### ✅ Good Examples:

```
**What We Looked At:** Search term reports from Google Ads for three time
periods (March-April 2025, August-September 2025, September-October 2025),
categorizing each query as high-intent, informational, or brand.

**Finding:** High-intent search queries decreased 35% from August to October.
```

```
**What We Looked At:** Google Trends data for apartment-related searches
in the NYC market over a 5-year period to identify seasonal demand patterns.

**Finding:** Apartment search demand follows predictable seasonal decline
of 25-50% from peak (March-August) to low season (October-January).
```

```
**What We Looked At:** GA4 conversion data for Example Account PMAX campaign
(last 30 days), analyzing landing page distribution, user geography, and
device patterns to identify lead quality signals.

**Finding:** 70% of conversions originated from blog/informational pages
rather than property listing pages, indicating potential traffic quality issues.
```

### ❌ Bad Examples:

```
Search CPC increased 274%
```
❌ Missing: What data source? What time period? How calculated?

```
We found that conversions dropped significantly.
```
❌ Missing: What data? What time period? How much is "significantly"?

```
Campaign performance declined due to seasonality.
```
❌ Missing: What data proved this? What analysis was done?

### Data Presentation Format

**When comparing periods:**
Use tables for clarity:

```
| Metric | August | October | Change |
|--------|--------|---------|--------|
| ROAS | 23.1x | 16.9x | -27% |
| CPC | $2.10 | $5.75 | +274% |
| Conversions | 245 | 180 | -27% |
```

**When presenting multi-dimensional data:**
Break into subsections with clear headers:

```
### Search Demand Analysis

**What We Looked At:** [data source]

[Present findings]

**Finding:** [key insight]

### Competitive Landscape Analysis

**What We Looked At:** [data source]

[Present findings]

**Finding:** [key insight]
```

---

## Section 3: Conclusions

**Purpose:** Tie everything together with action plan

**REQUIRED subsections:**

### What's Happening (The Dynamics)
- Explain cause-and-effect relationships
- Connect findings from Analysis section
- Show how different factors interact
- Tell the complete story

**Example:**
```
## Conclusions

### What's Happening

Example Account's 27% ROAS decline is primarily driven by seasonal market shifts,
not campaign issues. Apartment search demand declined 25% from August to
October (Google Trends), while competitive pressure increased (274% CPC
increase). The campaign is performing as expected given market conditions.
```

### What We're Doing About It
- Actions already taken (if any)
- Recommended next steps
- Specific, actionable items
- Owner/timeline for each action

**Example:**
```
### What We're Doing About It

**Immediate Actions (Already Implemented):**
1. Reduced daily budget from $750 to $600 to align with lower demand
2. Paused underperforming ad variants in brand campaign

**Recommended Next Steps:**
1. Monitor weekly through November for further seasonal decline
2. Prepare for demand recovery in January-February (budget increase)
3. Consider increasing brand campaign cap to 20% during low season
   (brand maintains 35x ROAS vs 17x for PMAX)
```

### Expected Timeline
- When client should expect changes
- When to review/reassess
- Key dates or milestones

**Example:**
```
### Expected Timeline

- **Through November:** Continued ROAS pressure (expect 15-18x range)
- **December-January:** Seasonal low point (12-15x ROAS expected)
- **February-March:** Demand recovery begins (return to 20x+ ROAS)
- **Next Review:** Mid-November (assess if additional adjustments needed)
```

### Key Takeaways for Client
- 3-5 bullet points summarizing everything
- Written for non-technical stakeholders
- Focus on business impact, not technical details

**Example:**
```
### Key Takeaways

- Example Account PMAX is performing as expected given seasonal market decline
- ROAS drop is market-driven (25% demand decrease), not campaign quality
- Budget reduced proactively to maintain efficiency during low season
- Performance will recover naturally in Q1 2026 as demand returns
- No major campaign restructuring needed - this is normal seasonality
```

---

## Why This Framework Works

**For Clients:**
- Matches how they think (problem → evidence → solution)
- Data transparency builds credibility ("What We Looked At")
- Clear action plan reduces anxiety
- Timeline sets expectations

**For You:**
- Consistent format across all reports
- Forces rigorous analysis (must show data sources)
- Prevents unsupported claims
- Creates reproducible methodology

---

## What NOT to Do

### ❌ Don't:
1. Add extra sections beyond the 3 (keep to exactly 3)
2. Present data without source attribution (always include "What We Looked At")
3. Include technical implementation details (save for internal notes)
4. Make recommendations without supporting data
5. Use jargon without explanation (ROAS, CPC, CTR need context for some clients)
6. Skip the "Expected Timeline" (clients need to know when things will improve)

### ✅ Do:
1. Keep it concise (Background = 2-3 paragraphs)
2. Show your work (Analysis = transparent methodology)
3. Be specific (Conclusions = actionable steps with owners/timelines)
4. Use tables for data comparisons (improves readability)
5. End with Key Takeaways (executives read this first)

---

## Templates & Examples

### Template Location:
`.claude/templates/client_summary_template.md` (provide your own template)

### Example Reports:
Save your example client reports in your project's documents/output folder for reference.

---

## Format Variations by Report Type

### Investigation Summary (Most Common)
- **Background:** Issue description + scope
- **Analysis:** Data findings with "What We Looked At" for each
- **Conclusions:** Root cause + action plan + timeline

### Monthly Performance Review
- **Background:** Month overview + KPIs checked
- **Analysis:** Performance vs targets (with data sources)
- **Conclusions:** What changed + why + what's next

### Strategy Presentation
- **Background:** Current state + strategic question
- **Analysis:** Options evaluated (with supporting data)
- **Conclusions:** Recommended strategy + implementation plan

---

## Data Transparency Best Practices

### Always Attribute:
- Google Ads reports (specify which report, time period)
- GA4 data (property, conversion events, date range)
- Google Trends (search terms, geography, time period)
- Third-party tools (Semrush, Google Search Console, etc.)
- Internal spreadsheets (specify tab name, date updated)

### Methodology Clarity:
- Categorization: "categorizing each query as high-intent, informational, or brand"
- Statistical: "calculating year-over-year change for each metric"
- Correlation: "correlating CPC increases with impression share changes"
- Segmentation: "segmenting conversions by landing page type"

---

## Integration with Agents

### This skill auto-loads when:
- Creating client summaries or reports
- Writing investigation findings
- Documenting performance reviews
- Generating monthly reports
- User asks to "create a summary for the client"
- User mentions "client-facing" or "stakeholder report"

### Agents that use this skill:
- Any agent creating client-deliverable output (investigation agents, performance review agents, monthly reporting agents)
- Replace with your own agents as needed — this skill is protocol-only and works with any agent setup

---

## Quality Checklist

Before sending any client communication, verify:

- [ ] Exactly 3 sections (Background, Analysis, Conclusions)
- [ ] Every data finding has "What We Looked At" statement
- [ ] "What We Looked At" specifies: data source, time period, methodology
- [ ] Analysis section uses tables for comparisons
- [ ] Each analysis subsection ends with "Finding:" statement
- [ ] Conclusions include: What's Happening + What We're Doing + Timeline + Key Takeaways
- [ ] Key Takeaways has 3-5 bullet points
- [ ] No technical jargon without explanation
- [ ] Action items are specific with owners/timelines
- [ ] Timeline sets realistic expectations

---

## Related Documentation

- Your own CLAUDE.md — for any project-specific reporting conventions
- `.claude/templates/client_summary_template.md` — blank template (provide your own)
- Your own examples folder — store delivered client reports for reference

---

**Created:** 2025-10-28
**Based On:** Client communication best practices
**Status:** Active - MANDATORY FOR CLIENT REPORTS
