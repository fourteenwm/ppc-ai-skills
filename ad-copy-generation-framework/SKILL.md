---
name: ad-copy-generation-framework
description: Comprehensive 23-element Google Ads RSA copywriting framework with distribution formulas, sentiment scoring, and the "Four Words to Value" rule. Auto-invoke when user says "generate RSA copy", "write ad copy", "RSA framework", "headlines and descriptions", or asks for ad copywriting principles. Pure protocol skill, no scripts required.
allowed-tools: [Read]
---

# Ad Copy Generation Framework

Comprehensive Google Ads RSA copywriting framework with 23 elements, distribution formulas, and "Four Words to Value" rule for creating high-performing ad copy.

## Auto-Invoke When

- Generating RSA headlines or descriptions
- Writing ad copy for Google Ads
- Optimizing existing ad copy
- Reviewing ad copy quality
- Training on ad copywriting principles

## Key Features

- **3-Tier Element System**: Mandatory, Preferred, and Optional elements
- **Distribution Formula**: 3 keyword + 2 social proof + 4 generic USP + 2 CTA + 1 pun + 3 flexible
- **"Four Words to Value" Rule**: Website headline optimization for cognitive momentum
- **Character Constraints**: 30 char headlines, 90 char descriptions (Google Ads limits)
- **Sentiment Scoring**: Target 0.8-1.0 positive sentiment
- **Type Categorization**: Headlines tagged by strategic type (keyword-focused, benefit-driven, emotional, etc.)

## Framework Components

### 1. The 23 Elements

Organized into three tiers:
- **Tier 1 (Mandatory)**: Always use - keyword placement, funnel matching, title case, CTA, continuity
- **Tier 2 (Preferred)**: Strongly recommended - punctuation, timely language, features+benefits, single focus
- **Tier 3 (Optional)**: Use strategically - FOMO, puns, competitor comparisons, DKI

See `framework.md` for complete list.

### 2. Distribution Formulas

**Headlines (15 total)**:
- 3 keyword-focused
- 2 social proof
- 4 generic USPs
- 2 CTAs
- 1 pun
- 3 flexible

**Descriptions (4 total)**:
- 2 with keyword + product USP + CTA
- 2 with keyword + generic USPs (no CTA)

See `distribution.md` for details.

### 3. Technical Specifications

- Headlines: 30 characters max (hard Google Ads limit)
- Descriptions: 90 characters max (hard Google Ads limit)
- Capitalize Each Word (Title Case)
- Use symbols/numbers where possible (!, ?, $, %)
- Positive sentiment (0.8-1.0 target)

See `technical-specs.md` for validation rules.

### 4. "Four Words to Value" Rule

Website headlines should deliver value in first 4 words:
- Start with verb (action-oriented)
- Subject/predicate structure (cognitive momentum)
- Use most important keyword
- Avoid "we" - use "you" (customer-focused)
- Imply value, not work

Example: "Get Emergency Plumbing Fixed Today"
          ^    ^         ^        ^      ^
          Verb  You      Benefit  Action Timeframe

See `examples.md` for more.

## Integration with Other Skills

- **Ad Copy Verification Standard**: Only recommend extensions/ad copy from EXPLICITLY verified website content
- **Mutation Safety**: Agent outputs to Google Sheet (manual review before import)

## Usage in Agents

Agents should invoke this skill when generating ad copy. The skill provides:
- Complete 23-element framework reference
- Distribution formulas for headline/description balance
- Validation rules for character limits
- Examples of good vs bad ad copy

**Typical agent workflow**:
1. Invoke skill to get framework
2. Gather inputs (keyword, USPs, reviews, business overview)
3. Generate headlines/descriptions following distribution formula
4. Validate against technical specs
5. Output with character counts and types

## Files in This Skill

- `SKILL.md` - This file (auto-invoke description)
- `framework.md` - Complete 23-element framework with principles
- `distribution.md` - Headline/description generation formulas
- `technical-specs.md` - Character limits, formatting, validation rules
- `examples.md` - Good/bad examples, "Four Words to Value" demos
