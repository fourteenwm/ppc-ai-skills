# Account Audit

A comprehensive 13-section health audit for individual Google Ads accounts that generates a professional HTML report covering performance, conversions, keywords, assets, and compliance.

**The pain point:** Auditing a Google Ads account means checking a dozen different things across multiple screens — budget pacing, conversion health, keyword quality, asset performance, impression share. This skill runs all 13 checks in one pass and produces a color-coded HTML report with actionable insights.

---

## What's Inside

- 13 audit sections: Account Overview, Budget Pacing, Campaign Performance, Keyword Analysis, Search Term Analysis, Conversion Health, Business Conversion Standards, Bid Management & Impression Share, Asset Performance, Creative Compliance, PMAX Settings, Quality Score, and Negative Keywords
- Period-over-period comparison with delta arrows
- Charts for daily spend trends and campaign breakdown
- Severity-coded findings (green/yellow/red)
- Supports lookup by account name or CID

---

## Installation

```bash
mkdir -p .claude/skills/account-audit
curl -o .claude/skills/account-audit/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/account-audit/SKILL.md
```

---

## Prerequisites

- Google Ads API credentials (YAML config)
- Python with `google-ads`, `matplotlib`, `pandas`, and `pyyaml` packages
- Account list file for name-to-CID resolution

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
