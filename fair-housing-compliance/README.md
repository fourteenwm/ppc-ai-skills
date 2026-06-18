# Fair Housing Compliance

A legal compliance skill that auto-invokes whenever Claude is about to discuss targeting, audiences, or geographic settings for property management advertising. It enforces Fair Housing Act requirements as hard rules — not suggestions.

**The pain point:** The Fair Housing Act restricts discriminatory targeting in housing ads, but AI tools happily recommend age ranges, income brackets, and zip code targeting because they optimize for conversions, not legal risk. One bad recommendation can expose a client to federal lawsuits and substantial fines. This skill blocks the recommendation before it happens.

---

## What It Prevents

Real mistakes this skill catches:

- Recommending age targeting (e.g., "25-34") for property management campaigns
- Adding household income signals to audiences
- Targeting specific zip codes (income proxy)
- Using affinity audiences like "Young Urban Professionals" (age proxy)
- Adding parental/familial status filters
- Suggesting "College Graduates" audience (could imply age range)

---

## What It Enforces

### Prohibited
- Age, income, parental status, familial status, gender-as-discriminator
- Zip code or sub-city geographic targeting
- Any demographic audience signal that could proxy for a protected class

### Compliant
- Behavioral signals only: in-market audiences, search themes, website remarketing
- Metro or city-level geographic targeting
- Radius targeting from a property address
- Conversion-based optimization without demographic filters

### Guiding Principle
**Target the product (apartments), not the people (demographics).**

---

## Installation

```bash
mkdir -p .claude/skills/fair-housing-compliance
curl -o .claude/skills/fair-housing-compliance/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/fair-housing-compliance/SKILL.md
```

---

## When It Activates

Auto-invokes whenever Claude is about to:
- Create or modify a property management campaign
- Recommend audience signals
- Change location/geographic targeting
- Optimize PMax or Demand Gen campaigns
- Discuss any targeting change for a PM account

---

## Prerequisites

None. This is a protocol skill — it works with just Claude Code installed. No API keys or external dependencies required.

---

## Legal Basis

- Fair Housing Act (Title VIII of the Civil Rights Act of 1968)
- U.S. Department of Housing and Urban Development (HUD) regulations
- Google Ads Fair Housing policy

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
