---
name: account-audit
description: Comprehensive single-account health audit combining analytics with business-specific checks. Auto-invoke when user says 'run account audit', 'audit [account]', 'account health check', or 'full audit for [account]'. Generates HTML report with 13 sections covering performance, conversions, keywords, assets, and compliance.
allowed-tools: [Bash, Read]
---

# Account Audit Skill

Comprehensive single-account health audit for Google Ads accounts.

---

## Invocation Triggers

Auto-invoke when user says:
- "Run account audit for [account]"
- "Audit [account]"
- "Account health check for [account]"
- "Full audit for [account]"

---

## What It Does

Runs 13 audit sections and generates a professional HTML report:

| # | Section | What It Checks |
|---|---------|----------------|
| 1 | Account Overview | Spend, conversions, CPA with period comparison |
| 2 | Budget Pacing | Daily average, 30-day forecast, month remaining |
| 3 | Campaign Performance | Top campaigns by spend, ROAS by campaign |
| 4 | Keyword Analysis | Highest CPC, zero-conversion keywords |
| 5 | Search Term Analysis | Wasted spend on zero-conv terms |
| 6 | Conversion Health | Healthy/Warning/Stale/No Data categorization |
| 7 | Business Conversion Standards | Checks for standard business conversions (configurable) |
| 8 | Bid Management | Search IS, Budget Lost IS, Rank Lost IS diagnosis |
| 9 | Asset Performance | BEST/GOOD/LOW asset labels |
| 10 | Creative Compliance | DKI, disapprovals, AI assets (Ads Checker subset) |
| 11 | PMAX Settings | PMAX campaign detection |
| 12 | Quality Score | QS distribution, low QS keywords |
| 13 | Negative Keywords | Total negatives, campaigns with <10 flagged |

---

## How to Run

### Basic Usage

```bash
python scripts/account_audit.py "Account Name"
```

### With CID

```bash
python scripts/account_audit.py --cid [CUSTOMER_ID]
```

### Custom Period (default: 30 days)

```bash
python scripts/account_audit.py "Account Name" --days 60
```

---

## Output

**HTML Report Location:** `./data/audits/[account]-audit-[timestamp].html` (configurable)

**Report Features:**
- Summary cards with period comparison (arrows)
- Daily trend chart (cost + conversions)
- Campaign spend chart
- Color-coded severity (green/yellow/red)
- Actionable insights per section

---

## Account Name Resolution

The script accepts `--cid` for direct CID input. If your setup maintains a
local accounts mapping file, update the script's account-lookup helper to
read from it. Keep your accounts file out of source control (the `.gitignore`
ignores `credentials/` by default).

---

## Relationship to Existing Scripts

This audit **references but does not modify** existing standalone scripts:

| Existing Script | Relationship |
|-----------------|--------------|
| `ads_checker_audit.py` | Section 10 runs subset of checks inline |
| `portfolio_conversion_audit.py` | Section 6 uses similar logic |
| `audit_pmax_asset_automation.py` | Section 11 detects PMAX, recommends standalone for detail |

**Standalone scripts remain available for portfolio-wide execution.**

---

## 13 Sections Explained

### Section 1: Account Overview
- Total spend, conversions, conv value, CPA
- Period comparison (current vs previous N days)
- Delta arrows with percentage change

### Section 2: Budget Pacing
- Daily average spend
- 30-day projection
- Month remaining forecast
- Days left in month

### Section 3: Campaign Performance
- Top campaigns by spend (chart)
- Campaign count
- ROAS by campaign

### Section 4: Keyword Analysis
- Highest CPC keyword
- Zero-conversion keywords count
- Wasted spend on zero-conv keywords

### Section 5: Search Term Analysis
- Zero-conversion search terms
- Top 5 by wasted spend
- Total wasted on zero-conv terms

### Section 6: Conversion Tracking Health
- Total conversion actions
- Categorization: Healthy (<=14d), Warning (15-30d), Stale (30+d), No Data
- Lists problematic conversions

### Section 7: Business Conversion Standards
- Checks for standard business conversions (configure per your vertical):
  - Example: Form Submit, Phone Call, Chat, Quote Request
- Flags missing standards

### Section 8: Bid Management & Impression Share
- Search Impression Share
- Budget Lost IS
- Rank Lost IS
- Diagnosis: Budget constraint / Quality issues / Low demand / Mixed

### Section 9: Asset Performance
- BEST/GOOD/LOW asset counts
- Lists LOW performers (replace these)
- Lists BEST performers (replicate these)

### Section 10: Creative Compliance
- DKI detection
- Disapproved ads
- Google AI auto-created assets
- (Subset of full Ads Checker - run standalone for complete 10-check audit)

### Section 11: PMAX Settings
- PMAX campaign count
- Note to run standalone audit for detailed settings

### Section 12: Quality Score
- Keywords with QS data
- Low QS (<5) count
- Lowest QS keywords list

### Section 13: Negative Keywords
- Total negative keywords
- Average per campaign
- Campaigns with <10 negatives (flagged)

---

## Interpretation Guide

### Period Comparison Arrows
- Up Green = Improvement (more conversions, lower CPA)
- Down Red = Decline (fewer conversions, higher CPA)
- For CPA: lower is better, so down is green

### Severity Colors
- **Green:** Healthy, no action needed
- **Yellow:** Warning, review when possible
- **Red:** Critical, action required

### Impression Share Diagnosis
| Pattern | Diagnosis | Action |
|---------|-----------|--------|
| Budget Lost IS >30% | Budget constraint | Consider budget increase |
| Rank Lost IS >60%, Budget Lost <10% | Quality issues | Improve ad relevance |
| Search IS >80% | Good coverage | Capturing available demand |
| Mixed | Monitor | No immediate action |

---

## Use Cases

### 1. Monthly Account Review
Run for each account during monthly optimization cycle.

### 2. Client Reporting
Generate HTML report to share with stakeholders.

### 3. New Account Onboarding
Run audit to identify setup issues (missing conversions, low QS).

### 4. Performance Investigation
When account performance changes, run audit for comprehensive diagnosis.

### 5. Pre-Meeting Prep
Quick health check before client calls.

---

## Limitations

1. **Single account only** - Not designed for portfolio-wide execution
2. **PMAX detail limited** - Run standalone `audit_pmax_asset_automation.py` for full settings check
3. **Creative compliance subset** - Run standalone `ads_checker_audit.py` for full 10-check audit
4. **No historical trending** - Shows single snapshot, not trend over time
5. **Quality Score may be empty** - Google does not always provide QS data

---

## Dependencies

- `matplotlib` - For chart generation
- `pandas` - For data processing
- `google-ads` - Google Ads API client
- `pyyaml` - Config loading

---

## Related Skills

| Skill | Relationship |
|-------|--------------|
| `conversion-tracking-health` | Section 6 uses similar logic |
| `impression-share-diagnostics` | Section 8 uses IS interpretation framework |
| `google-ads-audit` | Section 10 runs subset of checks |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-02 | Initial release - 13 sections, HTML report |
| 1.1 | 2026-04-23 | Script inlined (`scripts/account_audit.py`). Sanitized, runnable out of the box with `google-ads.yaml` + `accounts.md`. |

---

**Script Location:** `scripts/account_audit.py` (inlined &mdash; runnable)
**Output Location:** `./data/audits/` (configurable)
