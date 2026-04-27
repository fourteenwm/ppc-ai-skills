# Lead Quality Pattern Analysis

Five red-flag detection frameworks for diagnosing bad leads, bot traffic, form spam, and placement garbage from GA4 behavioral data.

**The pain point:** Your conversion count looks fine. Your CPA looks fine. But the client says every lead is a no-show, a bot, or a wrong-number form fill. Where do you even start looking? This skill gives you a structured way to find the pattern — instead of guessing.

---

## What It Solves

"Low quality leads" is vague. This skill breaks it into 5 specific frameworks, each with red-flag thresholds and severity classifications. Count the red flags, classify the severity, find the root cause.

---

## The 5 Frameworks

### 1. Landing Page Distribution
Are conversions coming from high-intent pages (pricing, services, contact) or low-intent pages (blog posts, informational content)? If >50% of conversions come from blog content, you're collecting researchers — not buyers.

### 2. Geographic Distribution
Are conversions from your target market — or from cities 1,000 miles away? Cross-reference GA4 city data against campaign location targeting to separate targeting misconfiguration from IP geolocation noise.

### 3. Device & Browser Patterns
Android WebView dominance. Headless browsers. Unnatural browser version consistency. The five signatures that scream "this is bot traffic or in-app ad garbage."

### 4. Time Patterns
1-4 AM conversion peaks. Exact-interval timing. Single-hour dominance. Natural human behavior has a specific shape. When conversions don't match it, something is wrong.

### 5. User Behavior
New vs returning users, session duration, pages per session. The severity combinations that identify form spam (100% new + <10 sec + 1 page) vs engaged prospects (75-85% new + 2-5 min + 3-5 pages).

---

## Severity Classification

| Red Flags Detected | Classification | Action Timeline |
|---|---|---|
| 0 flags, poor performance | Configuration issues | Review targeting, bidding, budgets |
| 1 red flag | Moderate concerns | Investigate this week |
| 2 red flags | Moderate concerns | Prioritize by impact |
| 3 red flags | Severe quality issues | Same-day action required |
| 4+ red flags | Severe quality issues | Consider pausing until fixed |

---

## What's Inside

- **5 detailed analysis frameworks** with thresholds, example tables, and red flag statements
- **Cross-referencing rules** — how to combine framework findings to identify root causes (e.g., blog pages + Android WebView + 1-4 AM peak = in-app ad garbage)
- **Severity summary table** — quick classification by red flag count
- **Real-world example** — a PMax analysis walkthrough with 5 red flags detected and specific recommendations
- **Service business benchmarks** — what normal engagement looks like

---

## Installation

```bash
mkdir -p .claude/skills/lead-quality-pattern-analysis
curl -o .claude/skills/lead-quality-pattern-analysis/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/lead-quality-pattern-analysis/SKILL.md
```

---

## When It Activates

Auto-invokes when Claude sees:
- "Low quality leads", "bot traffic", "form spam"
- "Why are we getting no-shows?"
- GA4 conversion pattern analysis
- Lead quality audit requests
- Wrong-number or missing-contact-info investigations

---

## Prerequisites

- **GA4 data access** — to pull landing page, geo, device, time, and behavior metrics
- No external dependencies — this is a diagnostic framework, not an executable tool
- Works best paired with Google Ads campaign settings data for cross-referencing

---

## Pairs With

- **[investigation-methodology](../investigation-methodology/)** — Hypothesis-driven framework that this skill plugs into
- **[mutation-safety](../mutation-safety/)** — Two-step approval before applying URL/placement exclusions based on findings

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage 118 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
