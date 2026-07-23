---
name: rsa-single-account
description: Generate a full Responsive Search Ad set for ONE account — 15 headlines + 4 descriptions per active ad group — from website-verified content plus live SERP competitive analysis and a website→Google-Business-Profile review fallback. Ships all seven workflow scripts. Auto-invoke when user says "create RSAs for [account]", "generate RSAs for [account]", or "build RSA copy for [account]". Outputs an import-ready Google Sheet. Read-only on Google Ads (no mutations).
allowed-tools: [Read, Bash, Grep, Glob]
---

# RSA Single-Account Generator

**Purpose:** Produce a complete, import-ready RSA set for a single account — find its active Search ad groups, scrape its website for verified claims, analyze competitors for differentiation, pull reviews, and generate 15 headlines + 4 descriptions per ad group. Output lands in a Google Sheet ready to copy/paste into Google Ads Editor.

**Type:** Read-only generation skill. It does not mutate Google Ads — it writes ad copy to a review Sheet; you import via Editor.

**Which RSA skill?** This one builds a **full set from scratch**. If the
account already has RSAs with performance labels and the job is replacing
the LOW slots while keeping proven copy, load
[`rsa-refresh`](../rsa-refresh/) instead. If the job is a uniform literal
text swap across existing ads (rebrand, spelling, customizer retirement) —
no new copy at all — load [`rsa-bulk-edit`](../rsa-bulk-edit/).

---

## What This Skill Wraps

The skill is a procedural wrapper around seven small scripts, all shipped in [`scripts/`](scripts/). The scripts gather and verify inputs (Steps 1–6) and land output (Step 8) — **no script writes a headline**. Generation itself (Step 7) is yours, governed by two companion skills (both in this repo; the README install block fetches them):

- **`ad-copy-verification-standard`** — every claim must come from the website (or a verified review). No "Free" copy. *Empty > Inaccurate.*
- **`ad-copy-generation-framework`** — the 23-element framework + the headline/description distribution.

**Do not invent business facts.** All USPs, services, hours, credentials, and social proof must be verified from the scrape or reviews. If the scrape fails, STOP — do not fall back to generic copy.

The scripts are generic and self-contained — Google Ads credentials from `google-ads.yaml`, API keys from environment variables, output Sheet via `--sheet-id`. Every script's exact selection filters, thresholds, and output contract live in [`references/pipeline-contract.md`](references/pipeline-contract.md), so you can swap any script for your own implementation (different SERP provider, different scraper) as long as the contract holds.

---

## What This Skill Deliberately Does NOT Do

- **No Google Ads mutations** — it writes a review Sheet; a human imports via Google Ads Editor. There is no approval flow or rollback here because nothing is ever pushed.
- **No editing of existing ads** — replacing LOW-labeled assets in live RSAs is [`rsa-refresh`](../rsa-refresh/); uniform literal text swaps are [`rsa-bulk-edit`](../rsa-bulk-edit/).
- **No invented facts, ever** — no generic fallback on scrape failure, no assumed reviews, no industry-template copy.
- **No multi-account batching** — one account per run, by design. Run it once per account.
- **No copy validation by script** — the 30/90 limits, counts, Title Case, and verification rules are enforced by you at Step 7; the sheet writer checks JSON key presence only.
- **No keyword or structure strategy** — the ad group name is taken as the primary keyword; restructuring campaigns is out of scope.

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

## Workflow

The numbered path is the default, not a ritual — [`rules.md`](rules.md) § "Step sequencing" says which steps are skippable when (CID already known → skip 1; URL provided → skip 2; ≥ 2 site testimonials → skip 6) and how cached artifacts let a re-run resume at Step 7.

### Step 1 — Find the account
`python scripts/check_active_accounts.py [--name "<query>"]` → lists accounts with spend this month (accounts.json registry if present, MCC walk otherwise); resolve the account name to a Customer ID (CID) from the list. Multiple matches → ask the user. No match → list candidates.

### Step 2 — Get the website URL
`get_account_website_url.py` reads the CID from **stdin**, so pipe it:
```bash
echo "<CID>" | python scripts/get_account_website_url.py
```
→ business website (from ad final URLs) + business name. No ads found → ask the user for the URL.

### Step 3 — Competitive analysis (the differentiator)
`python scripts/analyze_competitors_for_rsa.py "<service>" "<location>" [--vertical <vertical>]` (needs `SERP_API_KEY`) → SERP-based competitor messaging analysis: common USPs (with saturation counts), services, CTAs, cached to `competitive_insights.json` for Step 7. Verticals are defined in `scripts/vertical_configs.json` — three example sets ship (auto_repair, plumbing, property_management); add your own.
- Derive **service** from the first active campaign/ad group name; **location** from the account/ad-group names (fallback: ask).
- The script's own gap printout runs against **built-in example client USPs** (real client USPs don't exist until the Step-5 scrape) — the saturation counts are the real half. At Step 7 you apply the gap logic to the client's *actual* USPs: emphasize what competitors *don't* mention; de-emphasize/skip USPs 3+ competitors use; differentiate through specificity. Mechanics + misread traps: [`references/pipeline-contract.md`](references/pipeline-contract.md) and [`rules.md`](rules.md).

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
- **GBP fallback** (if <2): `python scripts/get_gmb_reviews.py "<business_name>" "<location>"` (needs `SERP_API_KEY`) → rating, review count, recent snippets. A rating+count headline only exists at **rating ≥ 4.5** (the script's gate); verify the returned panel is actually the client, and read any snippet's `original_rating` before using it — details in [`rules.md`](rules.md) § "Review usability".
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
Serialize your generated copy (you author `rsa_data.json` — no script produces it), then:
```bash
python scripts/write_rsa_to_sheet.py --sheet-id "<YOUR_RSA_SHEET_ID>" rsa_data.json
```
JSON per ad group: `{account_name, campaign_name, ad_group_name, headlines:[15], descriptions:[4]}`. The script clears the Sheet, writes a header row + data, and handles Sheets auth (a `token-sheets.json` if present, otherwise the OAuth credentials in your `google-ads.yaml`). It validates key presence only — your Step-7 validation is the sole guard on counts and lengths.

### Step 9 — Summary
Report ad groups processed (by campaign), the Sheet URL, validation results (within/over limits, flagged), competitive insights applied, and warnings (limited website content, GBP fallback used, no reviews found).

---

## Output Configuration

| Setting | Value |
|---|---|
| Sheet ID | `--sheet-id <YOUR_RSA_SHEET_ID>` (bare ID or full URL; **dedicated sheet** — first tab A:Z is cleared each run) |
| Columns | A Account · B Campaign · C Ad Group · D–R Headlines 1–15 · S–V Descriptions 1–4 |
| Auth | `token-sheets.json` if present, else OAuth reuse from `google-ads.yaml` |

Exact write semantics (clear range, padding behavior, validation scope): [`references/pipeline-contract.md`](references/pipeline-contract.md) § Step 8.

---

## After a Run

No script writes a timestamp — the working directory is the run record: `competitive_insights.json` (Step 3), the Step-5 cache (e.g. `website_data.json`), and `rsa_data.json` (authored by you at Step 7) mark how far a run got; the Sheet's first tab holds only the latest successful write. The cold-read table is in [`references/pipeline-contract.md`](references/pipeline-contract.md) § "Reading run state cold".

Anything that looks wrong — an account missing from Step 1, a `[ERROR]` at Step 4, everything flagged "unique," misaligned Sheet columns — check [`rules.md`](rules.md) § "False alarms and misreads" **before** re-running or escalating; most of these are reads, not failures. After the human imports via Editor, [`change-history-checker`](../change-history-checker/) confirms what actually landed in the account.

Worked end-to-end runs (a clean set, a thin-review business, and a `[ERROR]`-that-isn't): [`examples.md`](examples.md).

---

## Files in This Skill

| File | Role |
|---|---|
| `SKILL.md` | This workflow — entry point and routing |
| `rules.md` | Judgment layer: invariants, step sequencing, JSON/review reading, false alarms, escalation |
| `examples.md` | Three worked runs, two edge-shaped |
| `references/pipeline-contract.md` | Exact per-script mechanics — selection filters, thresholds, output contracts (scripts win) |
| `scripts/check_active_accounts.py` | Step 1 — name → CID over registry or MCC walk |
| `scripts/get_account_website_url.py` | Step 2 — website + business name from ad final URLs |
| `scripts/analyze_competitors_for_rsa.py` | Step 3 — SERP saturation analysis |
| `scripts/vertical_configs.json` | Step 3 — per-vertical keyword maps (the operative lever) |
| `scripts/get_search_campaign_structure.py` | Step 4 — ENABLED "Search"-named campaigns + ad groups |
| `scripts/scrape_website_firecrawl.py` | Step 5 — Firecrawl scrape + LLM extraction (the verification source) |
| `scripts/get_gmb_reviews.py` | Step 6 — GBP review fallback (4.5 gate) |
| `scripts/write_rsa_to_sheet.py` | Step 8 — clear-then-write Sheet output |

Runtime artifacts (`competitive_insights.json`, the Step-5 cache, `rsa_data.json`) land in your working directory, never in this folder.

---

## When to Load Sibling Skills

| Load | When |
|---|---|
| [`ad-copy-verification-standard`](../ad-copy-verification-standard/) | Always, at Step 7 — the verification law every claim passes through |
| [`ad-copy-generation-framework`](../ad-copy-generation-framework/) | Always, at Step 7 — the 23-element framework behind the distribution |
| [`rsa-refresh`](../rsa-refresh/) | The account already has RSAs with performance labels and the job is replacing LOW slots |
| [`rsa-bulk-edit`](../rsa-bulk-edit/) | The job is a uniform literal text swap across existing ads — no new copy |
| [`competitor-analysis-v2`](../competitor-analysis-v2/) | Step 3's ad-text saturation counts aren't enough — you need a full strategic teardown of named competitors |
| [`change-history-checker`](../change-history-checker/) | After the Editor import — confirm what actually changed in the account |
| [`google-ads-api-setup`](../google-ads-api-setup/) | First run — creating `google-ads.yaml` (and the Sheets-scoped token this skill reuses) |

---

## License

MIT — use freely in your own brain / repo / agency.
