# RSA Single-Account Generator

Generate a complete, import-ready Responsive Search Ad set for **one** account — 15 headlines + 4 descriptions per active ad group — built entirely from website-verified content, sharpened with live SERP competitive analysis, and backed by a website→Google-Business-Profile review fallback for social proof.

**The pain point:** Writing RSAs by hand is slow, and writing them *well* means doing three jobs at once — pulling real claims off the client's site (not guessing), checking what competitors already say so you don't blend in, and balancing the 15-headline mix so you're not shipping ten variations of the same idea. Most AI ad-copy tools skip straight to generation and hallucinate phone numbers, fake "5-star" ratings, and services the shop doesn't offer. This skill front-loads verification and competitive positioning, then generates to a disciplined distribution — so every headline traces to a fact and the set is differentiated, not generic.

---

## What's Inside

- **Per-ad-group RSAs** — 15 headlines + 4 descriptions, one set per active Search ad group, with the ad group name as the primary keyword
- **Website-verified copy** — claims sourced from a Firecrawl scrape + structured extraction; *Empty > Inaccurate*
- **Live SERP competitive analysis** — finds what competitors over-use (saturated) vs. what the client uniquely offers (emphasize), so the copy differentiates instead of echoing
- **Review-backed social proof** — website testimonials first, Google Business Profile fallback via SERP; never fabricated ratings/counts
- **Disciplined distribution** — 3 keyword · 2 social proof · 4 USP · 2 CTA · 1 pun · 3 flexible (auto-falls back to 5 flexible when no reviews exist)
- **Premium-avatar filter** — excludes all "Free" copy even when verified on the site
- **Import-ready Google Sheet** — Account · Campaign · Ad Group · 15 headlines · 4 descriptions, ready to paste into Google Ads Editor
- Read-only on Google Ads — never mutates accounts

---

## Installation

```bash
mkdir -p .claude/skills/rsa-single-account
curl -o .claude/skills/rsa-single-account/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/rsa-single-account/SKILL.md
curl -o .claude/skills/rsa-single-account/README.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/rsa-single-account/README.md
```

---

## Script Dependency (You Provide)

This skill is docs-only — it orchestrates small scripts you implement against your own data sources and credentials. The SKILL.md documents the workflow and data contract; adapt the scripts to your stack.

- **`check_active_accounts.py`** — list active accounts (name ↔ CID) so a name resolves to a Customer ID
- **`get_account_website_url.py`** — given a CID, return the business website from ad final URLs (+ business name for the review lookup)
- **`analyze_competitors_for_rsa.py`** — given a service + location (+ optional vertical), query the SERP and summarize competitor USP saturation and gaps
- **`get_search_campaign_structure.py`** — given a CID, return active Search campaigns + ad groups
- **`scrape_website_firecrawl.py`** — scrape the site (Firecrawl) and extract services, credentials, features, hours, and specializations (LLM extraction)
- **`get_gmb_reviews.py`** — Google-Business-Profile review fallback via SERP local results (rating, count, snippets)
- **`write_rsa_to_sheet.py`** — clear + write the RSA rows to a Google Sheet

**Reference implementation hooks:**

- Google Ads API via `google-ads-python` (credentials from `google-ads.yaml`)
- Website scrape via Firecrawl + an LLM for structured extraction (keys via environment variables)
- SERP competitive analysis + GBP reviews via a SERP API (key in a config you provide)
- Google Sheets write via an OAuth credential you provide

A working reference implementation lives in the private brain this skill was extracted from; if you'd like a starter template to adapt, open an issue.

---

## Usage

**Inline (one account):**

> "Create RSAs for Example Auto"
> "Generate RSAs for Customer ID 1234567890"

The skill will:

1. Resolve the account → CID and pull the website URL
2. Run the SERP competitive analysis and scrape the site for verified claims
3. Pull reviews (website → GBP fallback)
4. Generate 15 headlines + 4 descriptions per active ad group to the distribution, applying competitive insights and the verification rules
5. Write an import-ready Google Sheet and summarize

---

## Output Example (Truncated)

Console summary:

```
RSAs generated for Example Auto (3 campaigns, 8 ad groups)
Website: scraped ✓ (7 services, 4 credentials, 6 features)
Reviews: none found on site or GBP → 5-flexible fallback
Competitive: 0–7 competitors analyzed; emphasized 3 unique USPs
Validation: 120/120 headlines ≤30 chars · 32/32 descriptions ≤90 chars · 0 "Free" · all verified
Sheet updated → ready for Google Ads Editor import
```

Ad group **"Auto Repair [City]"** (illustrative):

```
H: Auto Repair In [City] | ASE Certified Technicians | AAA Approved Auto Repair |
   NAPA AutoCare Center | Book Your Service Today! | All Makes & Models Serviced | ...
D: Auto Repair In [City] By ASE Certified Techs. AAA Approved. Book Online Today!
```

Every line traces to a verified website claim — nothing fabricated, no "Free" copy.

---

## License

MIT — use freely in your own brain / repo / agency.
