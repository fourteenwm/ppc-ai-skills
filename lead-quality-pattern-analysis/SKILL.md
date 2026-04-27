---
name: lead-quality-pattern-analysis
description: Red flag detection frameworks for lead quality analysis across GA4 behavioral data. Auto-invoke when analyzing lead quality, identifying bot traffic, investigating no-shows/missing contact info, or reviewing conversion patterns. Provides 5 analysis frameworks (landing pages, geo, devices, time, user behavior) with severity classification.
allowed-tools: [Read]
---

# Lead Quality Pattern Analysis Skill

**Purpose:** Provides standardized red flag detection frameworks for identifying lead quality issues through GA4 behavioral data analysis.

**Type:** Domain knowledge skill (auto-invoked)

---

## Quick Reference: Red Flag Decision Tree

**Severity Classification:**
- **🚨 Severe Quality Issues:** >3 red flags detected
- **⚠️ Moderate Quality Concerns:** 1-2 red flags detected
- **ℹ️ Configuration Issues:** 0 red flags but poor performance

**Common Red Flags:**
1. >50% conversions from non-conversion-intent pages (blog/informational)
2. Geographic mismatch (conversions outside target market)
3. Bot indicators (Android Webview dominance, unusual browsers)
4. Suspicious time patterns (1-4 AM peaks, exact intervals)
5. Abnormal device consistency (100% mobile or 100% desktop)
6. 100% new users (no returning visitors)
7. Extremely short session durations (<10 seconds before conversion)
8. Multiple conversions from single user/IP

---

## Framework 1: Landing Page Distribution Analysis

### Purpose
Identify if conversions are coming from high-intent pages (property/product pages) vs low-intent pages (blog/informational content).

### Analysis Method

**Step 1: Categorize Landing Pages**

**High-Intent Pages (Conversion-Focused):**
- Service detail pages (e.g., `/services/`, `/properties/`, `/pricing/`)
- Product pages (e.g., `/contact/`, `/request-quote/`, `/contact/`)
- Pricing pages (e.g., `/pricing/`, `/specials/`)
- Community/amenity pages (e.g., `/about/`, `/gallery/`)

**Low-Intent Pages (Informational/Blog):**
- Blog posts (e.g., `/blog/`, `/blog/`, `/news/`)
- Resource centers (e.g., `/resources/`, `/guides/`)
- General information (e.g., `/about/`, `/faq/`)
- Category pages (e.g., `/neighborhoods/`, `/lifestyle/`)

**Step 2: Calculate Distribution**

```
High-Intent % = (High-Intent Conversions ÷ Total Conversions) × 100
Low-Intent % = (Low-Intent Conversions ÷ Total Conversions) × 100
```

**Step 3: Apply Red Flag Thresholds**

| Low-Intent % | Severity | Action |
|--------------|----------|--------|
| >75% | 🚨 Severe | IMMEDIATE: Add URL exclusions for blog/informational pages |
| 50-75% | ⚠️ Moderate | MEDIUM: Review and selectively exclude low-performing URLs |
| 25-50% | ℹ️ Monitor | OPTIONAL: Consider excluding if CPA significantly higher |
| <25% | ✅ Normal | No action needed (expected mix) |

**Step 4: Document Findings**

**Example Table Format:**
```markdown
| Category | Conversions | % of Total | Top Examples |
|----------|-------------|------------|--------------|
| Blog/Community | 64 | 76.2% | /blog/10-tips, /blog/moving-guide |
| Service Pages | 15 | 17.9% | /pricing/2br, /services/studio |
| Other | 5 | 5.9% | /amenities, /contact |
```

**Red Flag Statement (if >50%):**
> 🚨 **CRITICAL:** 76.2% of conversions from blog/informational content. These users are researching moving tips, not actively seeking services. Leads likely to have low intent and high no-show rates.

---

## Framework 2: Geographic Distribution Analysis

### Purpose
Identify conversions from outside target geography (VPNs, proxies, incorrect IP geolocation, or misconfigured targeting).

### Analysis Method

**Step 1: Map Conversions to Geography**

Extract from GA4:
- City (most specific)
- State/Region
- Country

**Step 2: Compare to Target Market**

**Define Target Geography:**
- Primary market (e.g., the city or metro area the business serves)
- Acceptable radius (e.g., 40-mile radius)
- Explicitly excluded areas

**Calculate Match Rate:**
```
Target Geography Match % = (Conversions in Target ÷ Total Conversions) × 100
```

**Step 3: Identify Patterns**

**Normal Pattern:**
- Most conversions from target geography
- Some variance expected (mobile IP geolocation inaccuracy)
- Scattered outliers (travelers, relocating users)

**Suspicious Patterns:**
- Multiple conversions from single user in distant cities
- Geographic clusters far from target market
- International traffic when targeting domestic only

**Step 4: Cross-Reference with Campaign Settings**

**CRITICAL: Before flagging geographic issues:**
1. Verify campaign location targeting (check radius, included/excluded locations)
2. Check if conversions from wrong geo BUT targeting is correct → IP geolocation issue (NOT targeting problem)
3. Check if conversions from wrong geo AND targeting is wrong → Targeting misconfiguration

**Step 5: Apply Red Flag Thresholds**

| Outside Target % | Pattern | Severity | Action |
|------------------|---------|----------|--------|
| >50% | Distant cities, international | 🚨 Severe | Verify targeting, consider IP exclusions |
| 25-50% | Adjacent markets, mobile variance | ⚠️ Moderate | Review targeting radius, check for VPNs |
| <25% | Scattered outliers | ✅ Normal | Mobile IP variance expected |

**Special Case: VPN/Proxy Detection**

**Indicators:**
- Multiple conversions from same user across different cities
- IP geolocation shows distant city but form data shows local address
- Clustering in VPN-heavy cities (certain international locations)

**Note:** GA4 city data is often inaccurate for mobile users. Always verify campaign targeting before concluding targeting issue.

---

## Framework 3: Device & Browser Pattern Analysis

### Purpose
Identify bot traffic, automation tools, and abnormal device/browser patterns indicating low-quality or fraudulent conversions.

### Analysis Method

**Step 1: Extract Device & Browser Data**

From GA4:
- Device category (mobile, desktop, tablet)
- Operating system (Android, iOS, Windows, Mac)
- Browser (Chrome, Safari, Firefox, WebView)
- Specific browser version

**Step 2: Identify Bot Indicators**

**🚨 SEVERE Bot Indicators:**
- **Android WebView >50%** - In-app browser (often low-quality ad placements)
- **Headless browsers** - Automation tools (Puppeteer, Selenium)
- **Unusual user agents** - Bot signatures in UA string
- **Single browser version >90%** - Bot pattern (not natural distribution)

**⚠️ MODERATE Bot Indicators:**
- **100% mobile or 100% desktop** - Unnatural consistency
- **Old browser versions** - Outdated bots or scrapers
- **Obscure browsers** - Non-mainstream browsers at scale

**ℹ️ MONITORING Indicators:**
- **Very high mobile %** (>85%) - May indicate placement issues
- **Single OS dominance** (>95%) - Check if campaign-specific or bot

**Step 3: Calculate Distribution**

```markdown
| Device/Browser | Conversions | % of Total | Red Flag? |
|----------------|-------------|------------|-----------|
| Android Mobile (WebView) | 70 | 83.3% | 🚨 YES (in-app ads, low quality) |
| iOS Mobile (Safari) | 10 | 11.9% | ✅ Normal |
| Desktop (Chrome) | 4 | 4.8% | ✅ Normal |
```

**Step 4: Apply Red Flag Thresholds**

| Pattern | Severity | Action |
|---------|----------|--------|
| Android WebView >50% | 🚨 Severe | Exclude in-app placements, review mobile network quality |
| Single device type 100% | ⚠️ Moderate | Review placement targeting, check for bot traffic |
| Unusual browser >25% | ⚠️ Moderate | Investigate user agents, consider browser exclusions |
| Diverse distribution | ✅ Normal | No action needed |

**Step 5: Cross-Reference with User Behavior**

**If high Android WebView + high no-shows:**
- Root cause: In-app ad placements (users clicking ads while scrolling, not intentionally seeking services)
- Solution: Exclude mobile app inventory or add audience signals for in-market users

---

## Framework 4: Time Pattern Analysis

### Purpose
Detect suspicious conversion timing patterns indicating bot traffic, automation, or low-quality placements.

### Analysis Method

**Step 1: Extract Hourly Conversion Data**

From GA4:
- Hour of day (0-23 in property timezone)
- Day of week
- Conversion timestamp clustering

**Step 2: Chart Distribution**

```markdown
| Hour | Conversions | % | Notes |
|------|-------------|---|-------|
| 1 AM | 18 | 21.4% | 🚨 Suspicious (off-hours peak) |
| 2 AM | 15 | 17.9% | 🚨 Suspicious |
| 3 AM | 12 | 14.3% | 🚨 Suspicious |
| 4 AM | 9 | 10.7% | ⚠️ Elevated |
| ... | ... | ... | ... |
| 10 AM | 4 | 4.8% | ✅ Normal business hours |
```

**Step 3: Identify Red Flags**

**🚨 SEVERE Patterns:**
- **1-4 AM peak (>30% of conversions)** - Bot traffic or international placements
- **Exact interval timing** (every 5 min, every hour) - Automation script
- **Single hour dominance** (>50% in one hour) - Placement or bot issue

**⚠️ MODERATE Patterns:**
- **Late night elevated** (11 business - 6 AM >40%) - Check for international traffic
- **Weekend-only pattern** - May indicate specific placement or audience

**ℹ️ MONITORING Patterns:**
- **Business hours heavy** (9 AM - 6 business >60%) - Normal for B2B/services
- **Evening peak** (6 business - 11 business >50%) - Normal for consumer/residential

**Step 4: Compare to Industry Benchmarks**

**Service Business - Expected Pattern:**
- Peak: 6 business - 11 business (after work hours) - 40-50%
- Business hours: 9 AM - 6 business - 30-40%
- Late night: 11 business - 6 AM - 5-15%
- Early morning: 6 AM - 9 AM - 5-10%

**Red Flag Threshold:**
- If late night (1-4 AM) >20% → Investigate for bots/international traffic

**Step 5: Cross-Reference with Geography**

**Pattern:** 1-4 AM peak + international cities (Asia, Europe) = International placements
**Pattern:** 1-4 AM peak + domestic cities = Bot traffic or automation

---

## Framework 5: User Behavior Analysis

### Purpose
Detect abnormal user engagement patterns indicating low intent, bot traffic, or form spam.

### Analysis Method

**Step 1: Extract User Engagement Metrics**

From GA4:
- **New vs Returning Users** (% split)
- **Session Duration** (avg seconds before conversion)
- **Pages per Session** (avg pages viewed)
- **Engagement Rate** (% of engaged sessions)
- **Bounce Rate** (% single-page sessions)

**Step 2: Calculate Ratios**

```
New User % = (New Users ÷ Total Users) × 100
Avg Session Duration = Total Session Duration ÷ Total Sessions
Avg Pages per Session = Total Pages Viewed ÷ Total Sessions
```

**Step 3: Apply Red Flag Thresholds**

#### New vs Returning User Ratio

| New User % | Severity | Interpretation |
|------------|----------|----------------|
| 100% | 🚨 Severe | No returning visitors = no brand engagement, possible bots |
| 95-99% | ⚠️ Moderate | Very low returning rate = low intent or one-time form fills |
| 85-95% | ℹ️ Monitor | Slightly elevated (check if new campaign or seasonal) |
| 70-85% | ✅ Normal | Expected for prospecting campaigns |

**Service Business Benchmark:** 75-85% new users (normal for service searches)

#### Session Duration Before Conversion

| Avg Duration | Severity | Interpretation |
|--------------|----------|----------------|
| <10 seconds | 🚨 Severe | Instant form submission = bot or accidental click |
| 10-30 seconds | ⚠️ Moderate | Very quick = low engagement, possible spam |
| 30-120 seconds | ✅ Normal | Quick but engaged (mobile users) |
| 2-5 minutes | ✅ Normal | Researching, reading content |
| >10 minutes | ✅ High Intent | Deep engagement, comparison shopping |

**Service Business Benchmark:** 2-5 minutes (viewing pricing details, amenities, pricing)

#### Pages per Session

| Avg Pages | Severity | Interpretation |
|-----------|----------|----------------|
| 1 page | 🚨 Severe | Bounce and convert = form spam or bot |
| 1-2 pages | ⚠️ Moderate | Low engagement |
| 2-4 pages | ✅ Normal | Viewing property info, amenities |
| 4-8 pages | ✅ High Intent | Comparison shopping, researching |
| >8 pages | ℹ️ Monitor | Very engaged OR bot crawling |

**Service Business Benchmark:** 3-5 pages (service page → pricing details → amenities → convert)

**Step 4: Identify Patterns**

**🚨 SEVERE Combination (Form Spam/Bots):**
- 100% new users
- <10 sec avg session duration
- 1 page per session
- Conclusion: Automated form submission or accidental clicks

**⚠️ MODERATE Combination (Low Intent):**
- >95% new users
- 10-30 sec avg duration
- 1-2 pages per session
- Conclusion: Users filling forms from blog content without property intent

**✅ NORMAL Combination (Engaged Prospects):**
- 75-85% new users
- 2-5 min avg duration
- 3-5 pages per session
- Conclusion: Genuine potential customers researching options

**Step 5: Cross-Reference with Other Frameworks**

**If poor user behavior + blog landing pages:**
- Root Cause: Users reading moving tips, not seeking services
- Solution: Exclude blog URLs

**If poor user behavior + Android WebView:**
- Root Cause: In-app ad clicks while scrolling social feeds
- Solution: Exclude mobile app inventory

**If poor user behavior + 1-4 AM peak:**
- Root Cause: Bot traffic or automation
- Solution: Implement bot protection, review placement quality

---

## Red Flag Summary Table

### Quick Severity Assessment

Use this table to quickly classify lead quality issues:

| Red Flags Detected | Severity Classification | Recommended Action Timeline |
|--------------------|-------------------------|----------------------------|
| 0 flags, poor performance | ℹ️ Configuration Issues | Review targeting, bidding, budgets |
| 1 red flag | ⚠️ Moderate Concerns | Investigate root cause, implement fix this week |
| 2 red flags | ⚠️ Moderate Concerns | Multiple fixes needed, prioritize by impact |
| 3 red flags | 🚨 Severe Quality Issues | Immediate action required (same day) |
| 4+ red flags | 🚨 Severe Quality Issues | Consider pausing campaign until fixed |

---

## Integration with Investigation Workflow

### Step 1: Collect Data
- Run GA4 cross-analysis to get behavioral data
- Extract landing pages, geo, devices, time, user behavior metrics

### Step 2: Apply Each Framework
- Framework 1: Categorize and calculate landing page distribution
- Framework 2: Map geography and compare to target market
- Framework 3: Identify device/browser bot indicators
- Framework 4: Chart hourly patterns and flag suspicious timing
- Framework 5: Calculate user engagement ratios

### Step 3: Count Red Flags
- Tally total red flags across all 5 frameworks
- Apply severity classification (0 / 1-2 / 3+)

### Step 4: Identify Root Causes
- Cross-reference red flags to find patterns
- Example: Blog pages + 100% new users + short duration = informational traffic, not property seekers

### Step 5: Generate Recommendations
- Use severity classification to prioritize
- Reference specific framework findings in recommendations

---

## Real-World Example: PMax Lead Quality Analysis

### Red Flags Detected: 5 (🚨 SEVERE)

1. **Framework 1 (Landing Pages):** 76.2% from blog/community content ✗
2. **Framework 3 (Devices):** 83.3% Android WebView ✗
3. **Framework 4 (Time):** Peak activity 1-4 AM (53.6%) ✗
4. **Framework 5 (User Behavior):** 100% new users ✗
5. **Framework 5 (Engagement):** Likely low engagement (not measured but inferred from blog traffic) ✗

### Severity Classification: 🚨 SEVERE (5 red flags)

### Root Cause Identified:
Performance Max campaign serving in-app ads (Android WebView) that lead users to blog content. Users clicking while scrolling social feeds at night (1-4 AM), filling forms out of curiosity, not genuine purchase intent.

### Recommendations Generated:
- 🚨 IMMEDIATE: Add `/blog/*` to URL exclusions
- 🚨 IMMEDIATE: Review mobile app inventory quality
- ⚠️ MEDIUM: Add audience signals for in-market potential customers
- ⚠️ MEDIUM: Consider reducing budget during 1-4 AM hours

---

## When to Use This Skill

### Auto-Invoked When:
- Investigating lead quality issues
- Analyzing GA4 conversion data
- Identifying bot traffic
- Reviewing no-show rates or missing contact info
- User mentions "low quality leads", "bot traffic", "form spam"
- Creating lead quality analysis reports

### Manual Invocation:
- Baseline analysis for new campaigns
- Monthly quality audits
- Client reporting on lead quality metrics

---

## Related Skills in This Repo

- **[investigation-methodology](../investigation-methodology/)** — Hypothesis-driven framework for diagnosing root causes
- **[mutation-safety](../mutation-safety/)** — Two-step approval before applying URL/placement exclusions

---

Built by [Kurt Henninger](https://fourteenwebmedia.com). More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
