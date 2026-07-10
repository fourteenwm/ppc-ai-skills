---
name: rsa-single-account
description: Generate a full Responsive Search Ad set for ONE account — 15 headlines + 4 descriptions per active ad group — from website-verified content plus live SERP competitive analysis and a website→Google-Business-Profile review fallback. Ships all seven workflow scripts. Auto-invoke when user says "create RSAs for [account]", "generate RSAs for [account]", or "build RSA copy for [account]". Outputs an import-ready Google Sheet. Read-only on Google Ads (no mutations).
allowed-tools: [Read, Bash, Grep, Glob]
---

# RSA Single-Account Generator

**Purpose:** Produce a complete, import-ready RSA set for a single account — find its active Search ad groups, scrape its website for verified claims, analyze competitors for differentiation, pull reviews, and generate 15 headlines + 4 descriptions per ad group. Output lands in a Google Sheet ready to copy/paste into Google Ads Editor.

**Type:** Read-only generation skill. It does not mutate Google Ads — it writes ad copy to a review Sheet; you import via Editor.

---

## What This Skill Wraps

The skill is a procedural wrapper around seven small scripts, all shipped in [`scripts/`](scripts/). It determines the account, runs each step, and assembles verified copy via two companion skills:

- **`ad-copy-verification-standard`** — every claim must come from the website (or a verified review). No "Free" copy. *Empty > Inaccurate.*
- **`ad-copy-generation-framework`** — the 23-element framework + the headline/description distribution.

**Do not invent business facts.** All USPs, services, hours, credentials, and social proof must be verified from the scrape or reviews. If the scrape fails, STOP — do not fall back to generic copy.

The scripts are generic and self-contained — Google Ads credentials from `google-ads.yaml`, API keys from environment variables, output Sheet via `--sheet-id`. Each step below documents the script's data contract, so you can also swap any script for your own implementation (different SERP provider, different scraper) as long as the contract holds.

---

## Prerequisites

- **`google-ads.yaml`** at project root (or `--config <path>`) — see the [google-ads-api-setup](../google-ads-api-setup/) skill for creating it. Its OAuth credentials are reused for the Google Sheets write; set `login_customer_id` to your MCC so Step 1 can walk your accounts without a registry.
- **`SERP_API_KEY`** environment variable — for the competitive analysis (Step 3) and the GBP review fallback (Step 6). Get a key at serpapi.com. Each lookup costs an API credit.
- **`FIRECRAWL_API_KEY`** environment variable — for the website scrape (Step 5). Get a key at firecrawl.dev.
- **`ANTHROPIC_API_KEY`** environment variable — for the structured extraction in Step 5. All three keys can live in a `.env` file at project root.
- **Python packages:** `pip install google-ads google-search-results firecrawl-py anthropic google-api-python-client google-auth pyyaml python-dotenv`
- **An output Google Sheet** — create an empty spreadsheet and pass its ID via `--sheet-id` in Step 8.
- **Optional: `accounts.json`** registry for Step 1 name→CID resolution (same schema as the ads-checker skill; documented in the script header). Without it, Step 1 walks the MCC in your `google-ads.yaml`.

---

## Decisions Baked In

| Decision | Choice |
|---|---|
| Competitive analysis | **Live SERP** competitor messaging + saturation/gap analysis (the differentiator) |
| Reviews | Website first → **Google Business Profile fallback** via SERP local results |
| Headline distribution | 3 keyword · 2 social proof · 4 generic USP · 2 CTA · 1 pun · 3 flexible |
| Descriptions | Formula-composed from verified claims (keyword + USP + CTA), not lifted sentences |
| Output | One import-ready Google Sheet, cleared + rewritten each run |

---

## Workflow

### Step 1 — Find the account
`python scripts/check_active_accounts.py [--name "<query>"]` → lists accounts with spend this month (accounts.json registry if present, MCC walk otherwise); resolve the account name to a Customer ID (CID) from the list. Multiple matches → ask the user. No match → list candidates.

### Step 2 — Get the website URL
`get_account_website_url.py` reads the CID from **stdin**, so pipe it:
```bash
echo "<CID>" | python scripts/get_account_website_url.py
```
→ business website (from ad final URLs) + business name. No ads found → ask the user for the URL.

### Step 3 — Competitive analysis (the differentiator)
`python scripts/analyze_competitors_for_rsa.py "<service>" "<location>" [--vertical <vertical>]` (needs `SERP_API_KEY`) → SERP-based competitor messaging analysis: common USPs (with saturation), services, CTAs, and a **gap analysis** of which of the client's USPs are unique vs. saturated. Verticals are defined in `scripts/vertical_configs.json` — three example sets ship (auto_repair, plumbing, property_management); add your own.
- Derive **service** from the first active campaign/ad group name; **location** from the account/ad-group names (fallback: ask).
- **Strategy:** emphasize USPs competitors *don't* mention; de-emphasize/skip USPs 3+ competitors use; differentiate through specificity. Cache for Step 7.

### Step 4 — Query campaign structure
`python scripts/get_search_campaign_structure.py <CID>` → active Search campaigns (name contains "Search", for production safety) + active ad groups. **The ad group name is the primary keyword** for that RSA.

### Step 5 — Scrape the website (once per account)
The scrape uses Firecrawl + an LLM for structured extraction, so it needs `FIRECRAWL_API_KEY` + `ANTHROPIC_API_KEY` in the environment:
```bash
python scripts/scrape_website_firecrawl.py "<website_url>" --output website_data.json
```
→ verified business overview, USPs, services, credentials, hours, specializations. `--output` caches the extraction — reuse it across all ad groups. **If scraping fails → STOP** (no generic fallback).

### Step 6 — Reviews: website → GBP fallback
- **Website first:** parse the scrape for testimonials (need ≥2 for social-proof headlines).
- **GBP fallback** (if <2): `python scripts/get_gmb_reviews.py "<business_name>" "<location>"` (needs `SERP_API_KEY`) → rating, review count, recent snippets.
- Reviews from website or GBP only — never assumed.

### Step 7 — Generate RSAs (per ad group)
Invoke `ad-copy-generation-framework`. Distribution:

**Headlines (15):** 3 keyword · 2 social proof · 4 generic USP · 2 CTA · 1 pun · 3 flexible.
**Descriptions (4):** 2 = keyword + product USP + CTA · 2 = keyword + generic USPs (no CTA). Composed from verified claims.

**Apply competitive insights:** prioritize unique client USPs in the first USP slots; skip claims 3+ competitors use (or only combine them inside descriptions); differentiate through specificity; lead with differentiators.

**Verification rules (MANDATORY):**
- ALL copy website- or review-verified.
- **NO "Free" copy** even if verified on the site (premium-customer avatar filter).
- **NO generic placeholders / unverified ratings** ("Rated 5★ By Happy Customers" with no verified count).
- **Empty > Inaccurate** — leave a slot empty rather than fabricate.
- **No reviews at all (site or GBP):** skip the 2 social-proof headlines, add 2 more **verified** flexible headlines (5 flexible total). Never placeholders.

**Validation:** headlines ≤30 chars · descriptions ≤90 chars · Title Case · all claims verified · no "Free" · flag (don't silently drop) any violations for review.

### Step 8 — Write to the Sheet
Prepare RSA data as JSON, then:
```bash
python scripts/write_rsa_to_sheet.py --sheet-id "<YOUR_RSA_SHEET_ID>" rsa_data.json
```
JSON per ad group: `{account_name, campaign_name, ad_group_name, headlines:[15], descriptions:[4]}`. The script clears the Sheet, writes a header row + data, and handles Sheets auth (a `token-sheets.json` if present, otherwise the OAuth credentials in your `google-ads.yaml`).

### Step 9 — Summary
Report ad groups processed (by campaign), the Sheet URL, validation results (within/over limits, flagged), competitive insights applied, and warnings (limited website content, GBP fallback used, no reviews found).

---

## Output Configuration

| Setting | Value |
|---|---|
| Sheet ID | `--sheet-id <YOUR_RSA_SHEET_ID>` (bare ID or full URL) |
| Columns | A Account · B Campaign · C Ad Group · D–R Headlines 1–15 · S–V Descriptions 1–4 |
| Auth | `token-sheets.json` if present, else OAuth reuse from `google-ads.yaml` |

---

## Error Handling

| Symptom | Cause | Fix |
|---|---|---|
| Account not found | Name mismatch | List candidates, confirm exact name |
| Website scrape fails | Firecrawl/key error or empty site | STOP — no generic fallback; recommend manual review |
| No reviews (site or GBP) | No testimonials / no local match | Omit social proof, add verified flexible headlines |
| Headline >30 / description >90 | Over limit | Flag with location; never auto-truncate |
| No active ad groups | Paused / no Search campaigns | Error (criteria: "Search" in name, campaign + ad group ENABLED) |

---

## Worked Example (illustrative — verify against the real site)

Ad group **"Auto Repair [City]"**, scrape surfaces *ASE Certified, AAA Approved, NAPA AutoCare, all makes & models, online booking, M-F 8AM-5:30PM* (no reviews found → 5-flexible fallback):

- Headlines: `Auto Repair In [City]` · `ASE Certified Technicians` · `AAA Approved Auto Repair` · `NAPA AutoCare Center` · `Book Your Service Today!` · `All Makes & Models Serviced` · `Open Mon-Fri 8AM-5:30PM` · … (15 total)
- Description: `Auto Repair In [City] By ASE Certified Techs. AAA Approved. Book Online Today!`

Every line traces to a verified site claim; nothing fabricated; no "Free".

---

## Important Notes

- **Read-only on Google Ads** — output is a Sheet for review; you import via Editor.
- **Verification is non-negotiable** — see `ad-copy-verification-standard`.
- Each GBP/SERP lookup costs an API credit; scrape once per account and cache.

---

## License

MIT — use freely in your own brain / repo / agency.
