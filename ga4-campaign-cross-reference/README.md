# GA4 Campaign Cross-Reference

A hypothesis-driven framework for comparing GA4 behavioral data with Google Ads campaign settings to identify real configuration gaps versus misleading data anomalies.

**The pain point:** GA4 shows conversions from Phoenix but your campaign targets NYC. Is your targeting broken? Probably not — it's likely mobile IP geolocation inaccuracy. Without a verification framework, you waste time "fixing" things that aren't broken and miss the actual configuration gaps. This skill provides the methodology to tell the difference.

---

## What's Inside

- Hypothesis, Verification, Finding methodology for every discrepancy
- 5 cross-reference checks: Geographic, Landing Page, Device/Browser, Time Pattern, Audience/Targeting
- Pattern library of common discrepancies with verified root causes
- Templates for documenting confirmed gaps, ruled-out hypotheses, and strategic issues
- "What Was Ruled Out" framework that prevents recommending fixes for non-existent problems
- Real-world examples showing how GA4 data can be misleading (VPNs, carrier IPs, WebView browsers)
- Pre-flight checklist for systematic investigation

---

## Installation

```bash
mkdir -p .claude/skills/ga4-campaign-cross-reference
curl -o .claude/skills/ga4-campaign-cross-reference/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/ga4-campaign-cross-reference/SKILL.md
```

---

## Prerequisites

None. This is a protocol skill — it works with just Claude Code installed. No API keys or external dependencies required. The framework applies to any GA4 + Google Ads investigation regardless of tooling.

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
