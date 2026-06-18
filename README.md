# PPC AI Skills

Free, open-source AI skills for Google Ads practitioners. Drop them into [Claude Code](https://claude.ai/code) and they work immediately.

Each skill is a structured set of rules, frameworks, or workflows that make AI smarter about PPC. Some are executable tools with Python scripts. Others are pure knowledge — diagnostic frameworks, safety protocols, reporting standards — that work with any AI setup.

---

## ⚠ Use at Your Own Risk

Several skills in this repo include code that mutates live Google Ads
accounts (e.g., uploading negative keywords, disabling automation,
editing RSAs). Test any mutation script against a sandbox or
non-production account before running it against live data. The author
assumes no liability for ad spend impact, account changes, or business
consequences resulting from use of these skills. See LICENSE for the
full warranty disclaimer.

---

## Start Here

New to this? These five skills give you the most value with the least setup. Install them first.

| # | Skill | Why Start Here |
|---|-------|---------------|
| 1 | [Mutation Safety](mutation-safety/) | **Install this before anything else.** Prevents AI from making changes to live accounts without your explicit approval. Two-step dry-run → approve → execute. |
| 2 | [Ad Copy Verification Standard](ad-copy-verification-standard/) | Stops AI from hallucinating ad copy. Forces every claim to be sourced from the actual business website. Core principle: *Empty > Inaccurate*. |
| 3 | [Investigation Methodology](investigation-methodology/) | Hypothesis-driven framework for diagnosing performance issues. Teaches AI to think like a senior PPC analyst instead of guessing. |
| 4 | [Non-Serving Keyword Scanner](non-serving-keyword-scanner/) | Quick win — finds keywords with zero impressions over 180 days. Run it once, clean up the dead weight. |
| 5 | [Portfolio Health Prioritization](portfolio-health-prioritization/) | If you manage more than 10 accounts, this answers the daily question: *which account do I look at first?* |

```bash
# Install all five
for skill in mutation-safety ad-copy-verification-standard investigation-methodology non-serving-keyword-scanner portfolio-health-prioritization; do
  mkdir -p .claude/skills/$skill
  curl -sO --output-dir .claude/skills/$skill \
    https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/$skill/SKILL.md
done
```

---

## All Skills

### Safety & Guardrails
| Skill | What It Does |
|-------|-------------|
| [Mutation Safety](mutation-safety/) | Two-step approval system that prevents accidental changes to live Google Ads accounts |
| [Ad Copy Verification Standard](ad-copy-verification-standard/) | Forces AI to source every ad claim from the business website — no hallucinated copy |
| [Fair Housing Compliance](fair-housing-compliance/) | Blocks discriminatory targeting (age, income, zip codes) for property management advertising — Fair Housing Act compliance |
| [MCC Hack Audit](mcc-hack-audit/) | Portfolio-wide scan of every manager (MCC) with access to any account in your tree — built after a real-world MCC link-fraud incident |
| [Budget Guardian](budget-guardian/) | 2-hour spend tripwire — alerts on 100%/120% monthly budget overruns to catch hijacked accounts, runaway PMax, and fat-fingered budget formulas. Alert-only, never pauses |

### Diagnostics & Investigation
| Skill | What It Does |
|-------|-------------|
| [Investigation Methodology](investigation-methodology/) | Hypothesis-driven framework for diagnosing Google Ads performance issues |
| [Impression Share Diagnostics](impression-share-diagnostics/) | Decision tree for interpreting Search IS, Budget Lost IS, and Rank Lost IS under smart bidding |
| [Underspending Investigation](underspending-investigation/) | Six-framework root-cause diagnosis for accounts pacing under tolerance — distinguishes budget-too-low from quality issues, low demand, and smart-bidding ramp-up. Read-only; produces conservative budget recommendations capped at +10% per change |
| [Change History Checker](change-history-checker/) | GAQL templates for answering "what changed?" — not limited to the UI's 30-day window |
| [Conversion Tracking Health](conversion-tracking-health/) | Audit conversion tracking across portfolios — catches stale or misconfigured conversion actions |
| [Lead Quality Pattern Analysis](lead-quality-pattern-analysis/) | 5 red-flag detection frameworks for diagnosing bot traffic, form spam, and low-intent leads |
| [Lead Quality Recommendation Prioritization](lead-quality-recommendation-prioritization/) | 3-tier action framework for turning lead quality findings into prioritized fixes |
| [GA4 Campaign Cross-Reference](ga4-campaign-cross-reference/) | Cross-analyze GA4 behavioral data with Google Ads campaign settings to find gaps |
| [GA4 Cross-Analysis](ga4-cross-analysis/) | GA4 data collection framework for diagnosing lead quality and conversion path issues |
| [GA4 Lead Quality Investigation](ga4-lead-quality-investigation/) | Cross-analyze GA4 behavioral data with Google Ads settings to diagnose low-quality leads (no-shows, bot traffic, geo mismatches) — 5 red-flag frameworks, hypothesis-driven verification, 3-tier prioritized fixes |
| [Account Audit](account-audit/) | Comprehensive single-account health audit — generates structured HTML reports |
| [Ads Checker](ads-checker/) | Creative-compliance audit — 10 checks (DKI, ad disapprovals, broken URLs, auto-applied recommendations, Fair-Housing-risk content, spelling, irrelevance, more) with run-over-run issue-history comparison and chronic-issue detection (3+ occurrences / 90 days). Read-only; severity-ranked Google Sheet output |

### Search Query & Negative Keyword Management
| Skill | What It Does |
|-------|-------------|
| [SQR Classifier](sqr-classifier/) | Paste search terms, get intent classification (high-intent, low-intent, informational, off-brand) |
| [Offbrand Analyzer](offbrand-analyzer/) | GPT-powered query intent classification at scale with competitor keyword matching |
| [Geo Conflict Analyzer](geo-conflict-analyzer/) | GPT-powered check on whether a query conflicts with your active geo targets before you negative it |
| [SQR Pipeline](sqr-pipeline/) | End-to-end negative-keyword pipeline — pull search terms, classify with 3-run consensus, optional geo conflict check, human review, then two-step upload of approved negatives (supersedes the old SQR 3-Run + SQR Upload skills) |
| [Neg Conflict Finder](neg-conflict-finder/) | Google Ads Script that finds every place a negative is silently blocking a positive — across the whole MCC, at every level (ad group, campaign, shared list, MCC shared list) |
| [Account-Level Negative Keywords](add-account-negative-keywords/) | Bulk-add account-level negatives (Admin → Account Settings) using the 3-step SharedSet pattern most guides miss — idempotent across portfolios, with state categorization (NO_SET / PARTIAL / COMPLIANT) |

### Ad Copy & RSAs
| Skill | What It Does |
|-------|-------------|
| [Ad Copy Generation Framework](ad-copy-generation-framework/) | 23-element RSA copywriting framework with distribution formulas and verification checkpoints |
| [RSA Refresh](rsa-refresh/) | Replace LOW-performing RSA assets with website-verified headlines and descriptions |
| [RSA Bulk Edit](rsa-bulk-edit/) | Find-and-replace text across RSA ads with preview, approval, and rollback safety |
| [RSA Single-Account Generator](rsa-single-account/) | Generate a full RSA set (15 headlines + 4 descriptions per ad group) for one account from website-verified copy + live SERP competitive analysis + GBP review fallback |

### Portfolio Management
| Skill | What It Does |
|-------|-------------|
| [Portfolio Health Prioritization](portfolio-health-prioritization/) | 5-tier triage framework — answers "which account do I look at first?" |
| [Portfolio Pacing Rules](portfolio-pacing-rules/) | Budget pacing thresholds and tolerance rules for multi-portfolio management |
| [Budget Recommendation Calculator](budget-recommendation-calculator/) | Conservative budget change framework with 5-10% increase caps and performance guardrails |

### Campaign Building
| Skill | What It Does |
|-------|-------------|
| [PMax Builder](pmax-builder/) | Generate Performance Max campaign CSV files for Google Ads Editor import |
| [PMax Asset Automation](pmax-asset-automation/) | Audit and opt out of Google's auto-generated PMax headlines, descriptions, videos, and images |
| [DGen Automation Disable](dgen-automation-disable/) | Bulk-disable Demand Gen ad-level asset automation with safety protocol |

### Queries & API
| Skill | What It Does |
|-------|-------------|
| [Google Ads API Setup](google-ads-api-setup/) | Step-by-step guide to get your Google Ads API connection working |
| [GAQL Query Patterns](gaql-query-patterns/) | Ready-to-use query templates for campaign analysis, search terms, and more |
| [Google Ads Query](google-ads-query/) | Natural language to GAQL query tool with Python runner script |
| [Google Ads Samples](google-ads-samples/) | Reference library of official Google Ads API code samples |

### Reporting & Communication
| Skill | What It Does |
|-------|-------------|
| [Client Communication Standards](client-communication-standards/) | Background → Analysis → Conclusions reporting framework with data source attribution |
| [Markdown to Sheets Presenter](markdown-to-sheets-presenter/) | Transform markdown reports into formatted Google Sheets for client presentation |

### Competitive & Brand Safety
| Skill | What It Does |
|-------|-------------|
| [Competitor Analysis v2](competitor-analysis-v2/) | Structured competitive intelligence — auction insights, ad copy teardown, positioning gaps |
| [YouTube Placement Audit](youtube-placement-audit/) | Scan MCC for bad YouTube placements and aggregate by channel for bulk negation |
| [Non-Serving Keyword Scanner](non-serving-keyword-scanner/) | Find keywords with zero impressions over 180 days across accounts |

---

## Quick Start

### 1. Install Claude Code
```bash
# macOS/Linux
curl -fsSL https://claude.ai/install.sh | sh

# Windows (PowerShell)
irm https://claude.ai/install.ps1 | iex
```

### 2. Install a skill
```bash
mkdir -p .claude/skills/mutation-safety
curl -sO --output-dir .claude/skills/mutation-safety \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/mutation-safety/SKILL.md
```

### 3. Use it
Start Claude Code in your project directory. The skill loads automatically when relevant.

---

## About

I'm Kurt Henninger. I manage Google Ads portfolios across property management and local services — over 110 accounts total.

I built these skills because AI is fast but not careful. It hallucinates phone numbers, overwrites live campaigns, generates ad copy from assumptions instead of facts. Every skill in this repo exists because something went wrong and I wanted to make sure it didn't happen again.

The philosophy is simple: **engineered AI with guardrails beats raw prompting every time.**

These 42 public skills are a subset of what I run in production. I use a larger production system of 85+ specialized skills to manage accounts daily. If you're curious about how the full system works or want to build something similar for your agency, I write about it here:

**Website:** [fourteenwebmedia.com](https://fourteenwebmedia.com)
**X:** [@KurtHenninger](https://x.com/KurtHenninger)

---

## Contributing

Found a bug? Have a suggestion? Open an issue or submit a PR.

If you build something useful with these skills, I'd genuinely like to hear about it — drop me a note on X or open a discussion.

---

## License

MIT License. Use these however you want.
