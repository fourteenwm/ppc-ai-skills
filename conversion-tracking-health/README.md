# Conversion Tracking Health

Audits conversion tracking health across an entire Google Ads portfolio, identifying conversion actions that haven't fired or have gone stale — but only for accounts that are actively spending.

**The pain point:** A portfolio of 80+ accounts means hundreds of conversion actions. Some silently stop firing — the tag breaks, the page changes, or the tracking just goes stale. You won't notice until someone asks "why did conversions drop?" This skill scans every active account in one run and surfaces the problems sorted by severity.

---

## What's Inside

- Portfolio-wide scan with automatic spend filter (only audits accounts with spend in last 7 days)
- Filters out noise: ignores store visits, Google-hosted actions, mobile app conversions, and observation-only actions
- Activity categorization: Healthy (14 days or less), Warning (15-30 days), Stale (30+ days), No Data (90+ days or never fired)
- Severity-based output: No Recent Data first, then Stale, then Warning
- Supports custom lookback periods and single-account deep dives
- Complements existing Google Ads Script-based monitoring

---

## Installation

```bash
mkdir -p .claude/skills/conversion-tracking-health/scripts
curl -o .claude/skills/conversion-tracking-health/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/conversion-tracking-health/SKILL.md
curl -o .claude/skills/conversion-tracking-health/scripts/portfolio_conversion_audit.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/conversion-tracking-health/scripts/portfolio_conversion_audit.py
curl -o .claude/skills/conversion-tracking-health/scripts/last_conversion_dates_by_action.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/conversion-tracking-health/scripts/last_conversion_dates_by_action.py
```

---

## Prerequisites

- Google Ads API credentials (`google-ads.yaml` at project root, or `--config <path>`) — see [google-ads-api-setup](../google-ads-api-setup/) if you don't have one
- Python with the `google-ads` package
- Optional: a CSV portfolio file (`cid,name` per row, no header) for named portfolio runs — single `--cid` and `--cids` runs need no extra files

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
