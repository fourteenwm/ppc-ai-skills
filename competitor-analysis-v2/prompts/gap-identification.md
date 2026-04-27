# Gap Identification Prompt (Phase 5 - Enhanced)

You are analyzing competitive intelligence data to identify exploitable opportunities.

**Enhancement over v1:** Now includes messaging matrix, positioning maps, and emotional landscape analysis.

---

## Task

Given:
- Website extraction data (Phase 3 XML outputs)
- Strategic scores and tactical flags (Phase 4, if ads analyzed)
- Screenshot comparisons (Phase 2)

Identify gaps and opportunities across multiple dimensions.

**CRITICAL:** This phase identifies opportunities but does NOT recommend specific ad copy yet. Recommendations require client verification (Phase 6).

---

## Input Required

- Website extraction XML for all competitors (from Phase 3)
- Strategic analysis results (if ads analyzed)
- Tactical scan results (if ads analyzed)
- Keyword/market context

---

## Analysis Process

### Step 1: Build Messaging Matrix

**Create side-by-side comparison:**

| Competitor | Headline | Main Claim | USP | CTA | Proof Type | Pricing Visible? |
|------------|----------|------------|-----|-----|------------|------------------|
| Client | [From XML] | [From XML] | [From XML] | [From XML] | [From XML] | [From XML] |
| Comp 1 | [From XML] | [From XML] | [From XML] | [From XML] | [From XML] | [From XML] |
| Comp 2 | | | | | | |
| Comp 3 | | | | | | |
| Comp 4 | | | | | | |
| Comp 5 | | | | | | |

**Analysis questions:**
- What claims appear in 3+ competitors? → **Table stakes**
- What claims appear in only 1? → **Potential differentiator**
- What's missing from all? → **Opportunity**

---

### Step 2: Create Positioning Map

**Select appropriate axis pair:**

| Business Type | X-Axis | Y-Axis |
|---------------|--------|--------|
| **Service businesses** | Price (Low → High) | Specialization (Generalist → Specialist) |
| **Speed-focused** | Speed (Slow → Fast) | Quality (Basic → Premium) |
| **Local businesses** | Scale (Single → Multi-location) | Personalization (Transactional → Relationship) |
| **B2B** | Company size served (SMB → Enterprise) | Solution complexity (Simple → Comprehensive) |

**Map creation:**
1. Assign each competitor coordinates based on positioning signals
2. Plot on 2x2 grid
3. Identify client's current position
4. Identify white space (where no competitors exist)

**Output format (for CSS rendering):**

```
Positioning Map: [Title]
X-Axis: [Label Low] → [Label High]
Y-Axis: [Label Low] → [Label High]

Coordinates:
- Client: (X%, Y%) - "[Positioning description]"
- Comp 1: (X%, Y%) - "[Positioning description]"
- Comp 2: (X%, Y%) - "[Positioning description]"
- Comp 3: (X%, Y%) - "[Positioning description]"
- Comp 4: (X%, Y%) - "[Positioning description]"
- Comp 5: (X%, Y%) - "[Positioning description]"

White Space Opportunity: (X%, Y%) to (X%, Y%) - "[Description of opportunity]"
```

---

### Step 3: Emotional Landscape Analysis (NEW)

**Extract emotional triggers from each competitor's XML:**

| Competitor | Primary Emotion | Secondary Emotion | Emotional Tone |
|------------|-----------------|-------------------|----------------|
| Client | [From emotional_triggers] | | [From tone] |
| Comp 1 | | | |
| ... | | | |

**Common emotions to track:**
- Fear (of breakdown, safety, being cheated)
- Trust (honesty, reliability, expertise)
- Convenience (speed, ease, availability)
- Status (premium, exclusive, best)
- Belonging (community, family, local)
- Aspiration (transformation, success, growth)

**Create Emotional Positioning Map:**
- X-Axis: Rational ← → Emotional
- Y-Axis: Fear-based ← → Aspiration-based

---

### Step 4: Strategic Gap Analysis (From v1)

**Compare strategic scores across all competitors to identify:**

#### 4.1 Table Stakes (What Everyone Does)
- Attributes where ALL competitors score 2-3 points
- These are "must-haves" to compete
- Not differentiators, but necessary baselines

#### 4.2 Strategic Gaps (What NO ONE Does)
- Attributes where ALL competitors score 0-1 points
- These are whitespace opportunities
- High-value differentiation potential

#### 4.3 Positioning Whitespace (What Only One Does)
- Attributes where ONE competitor scores high (3 pts) but others score low (0-1)
- Indicates a positioning niche
- Opportunity to compete head-to-head OR differentiate further

#### 4.4 Weak Execution Across the Board
- Attributes where competitors score 1-2 (present but weak)
- Opportunity to execute better on the same positioning
- Quick wins through superior execution

---

### Step 5: Tactical Gap Analysis (From v1)

**Compare tactical flags across all competitors:**

#### 5.1 Universal Weaknesses (Everyone Flagged ❌)
- Attributes where ALL competitors are ❌ Missing
- Easy wins - adding these elements creates instant differentiation

#### 5.2 Weak Execution Across the Board (Everyone Flagged ⚠️)
- Attributes where ALL competitors are ⚠️ Weak
- Opportunity to execute better on same element

#### 5.3 Rare Strengths (Only One Flagged ✅)
- Attributes where ONE competitor is ✅ Present but others are ❌/⚠️
- Indicates competitive advantage - must match or differentiate

---

### Step 6: Cross-Layer Opportunities

**Identify mismatches:**

| Pattern | Meaning | Opportunity |
|---------|---------|-------------|
| Strong position + weak execution | Great story, poor mechanics | Execute their strategy better |
| Strong execution + weak position | Converts well, unclear why | Add strategic depth |
| Middle-of-pack both | Functional but unremarkable | Differentiate on either dimension |

---

## Output Format

```markdown
## Gap Identification Report

**Market:** [Industry, location, keywords]
**Competitors Analyzed:** [Count]
**Data Sources:** Website extraction + [Ad analysis if available]

---

### Messaging Matrix

| Competitor | Headline | Main Claim | USP | CTA | Proof | Pricing |
|------------|----------|------------|-----|-----|-------|---------|
| [Client] | | | | | | |
| [Comp 1] | | | | | | |
| [Comp 2] | | | | | | |
| [Comp 3] | | | | | | |
| [Comp 4] | | | | | | |
| [Comp 5] | | | | | | |

**Table Stakes (3+ claim this):**
- [Claim 1]
- [Claim 2]

**Potential Differentiators (only 1 claims):**
- [Claim] - Owned by [Competitor]

**Opportunities (no one claims):**
- [Unclaimed positioning 1]
- [Unclaimed positioning 2]

---

### Positioning Map

**Axes:** [X-Axis Label] vs [Y-Axis Label]

**Coordinates:**
- [Client]: ([X]%, [Y]%) - "[Description]"
- [Comp 1]: ([X]%, [Y]%) - "[Description]"
- [Comp 2]: ([X]%, [Y]%) - "[Description]"
- [Comp 3]: ([X]%, [Y]%) - "[Description]"
- [Comp 4]: ([X]%, [Y]%) - "[Description]"
- [Comp 5]: ([X]%, [Y]%) - "[Description]"

**White Space Opportunity:**
Position ([X]%, [Y]%) is unclaimed.
This represents: [Description of the opportunity]

---

### Emotional Landscape

| Competitor | Primary Emotion | Secondary | Tone |
|------------|-----------------|-----------|------|
| | | | |

**Emotional White Space:**
- [Emotion] is underused - only [X] competitors lean into it
- [Emotion] is overcrowded - [X] competitors all claim it

---

### Strategic Gaps (If Ads Analyzed)

#### Table Stakes (Must Match)
| Attribute | Avg Score | Implication |
|-----------|-----------|-------------|
| | | |

#### Strategic Whitespace
| Attribute | Avg Score | Opportunity |
|-----------|-----------|-------------|
| | | |

**Gap Priority Ranking:**
1. [Gap] - **HIGH** - [Why valuable]
2. [Gap] - **MEDIUM** - [Why valuable]
3. [Gap] - **LOW** - [Why valuable]

---

### Tactical Gaps (If Ads Analyzed)

#### Universal Weaknesses (Easy Wins)
| Attribute | Competitors Missing | Impact if Added |
|-----------|---------------------|-----------------|
| | | |

#### Weak Execution Opportunities
| Attribute | Current Execution | Better Execution |
|-----------|-------------------|------------------|
| | | |

---

### Cross-Layer Opportunities

| Competitor | Strategic | Tactical | Assessment | Opportunity |
|------------|-----------|----------|------------|-------------|
| | | | | |

---

### Summary: Top 5 Exploitable Gaps

1. **[Gap Type]:** [Specific gap]
   - **Why it matters:** [Impact]
   - **Difficulty:** Easy / Medium / Hard
   - **Expected impact:** High / Medium / Low
   - **Next step:** Verify client can fill this gap (Phase 6)

2. **[Gap Type]:** [Specific gap]
   - [Same structure]

3. **[Gap Type]:** [Specific gap]
   - [Same structure]

4. **[Gap Type]:** [Specific gap]
   - [Same structure]

5. **[Gap Type]:** [Specific gap]
   - [Same structure]

---

### What NOT to Do (Crowded Positioning)

| Area | Why Avoid |
|------|-----------|
| [Crowded claim] | All competitors already own this |

---

### Critical Reminder

**This analysis identifies OPPORTUNITIES, not RECOMMENDATIONS.**

Before recommending specific ad copy:
- ✅ Must verify client can fill identified gaps (Phase 6)
- ✅ Must scrape client website for evidence
- ✅ Must map gaps to verified capabilities
- ❌ Cannot assume client has features just because gap exists
- ❌ Cannot recommend based on industry standards

**Next Step:** Proceed to Phase 6 (Client Verification)
```

---

## Important Rules

1. **Use all data sources** - Combine website XML + ad analysis (if available)
2. **Create visual outputs** - Positioning maps and emotional landscapes are required
3. **Quantify gaps** - Use counts and percentages (e.g., "3 out of 5 competitors lack...")
4. **Prioritize by value** - Not all gaps are equally valuable
5. **Do NOT recommend copy yet** - This phase identifies what's possible, not what to do
6. **Include "What NOT to do"** - Crowded positioning is as important as whitespace
