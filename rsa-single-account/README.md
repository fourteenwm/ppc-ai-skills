# RSA Single-Account Generator

Generate a complete, import-ready Responsive Search Ad set for **one** account — 15 headlines + 4 descriptions per active ad group — built entirely from website-verified content, sharpened with live SERP competitive analysis, and backed by a website→Google-Business-Profile review fallback for social proof.

**The pain point:** Writing RSAs by hand is slow, and writing them *well* means doing three jobs at once — pulling real claims off the client's site (not guessing), checking what competitors already say so you don't blend in, and balancing the 15-headline mix so you're not shipping ten variations of the same idea. Most AI ad-copy tools skip straight to generation and hallucinate phone numbers, fake "5-star" ratings, and services the shop doesn't offer. This skill front-loads verification and competitive positioning, then generates to a disciplined distribution — so every headline traces to a fact and the set is differentiated, not generic.

---

## What's Inside

- **Per-ad-group RSAs** — 15 headlines + 4 descriptions, one set per active Search ad group, with the ad group name as the primary keyword
- **Website-verified copy** — claims sourced from a Firecrawl scrape + structured extraction; *Empty > Inaccurate*
- **Live SERP competitive analysis** — finds what competitors over-use (saturated) vs. what the client uniquely offers (emphasize), so the copy differentiates instead of echoing
- **Review-backed social proof** — website testimonials first, Google Business Profile fallback via SERP; never fabricated ratings/counts
- **Disciplined distribution** — 3 keyword · 2 social proof · 4 USP · 2 CTA · 1 pun · 3 flexible (falls back to 5 flexible when no reviews exist — a workflow rule, enforced at generation)
- **Premium-avatar filter** — excludes all "Free" copy even when verified on the site
- **Import-ready Google Sheet** — Account · Campaign · Ad Group · 15 headlines · 4 descriptions, ready to paste into Google Ads Editor
- **Operator docs** — [`rules.md`](rules.md) (step sequencing, false-alarm table, escalation), [`examples.md`](examples.md) (three worked runs), and [`references/pipeline-contract.md`](references/pipeline-contract.md) (exact per-script mechanics)
- Read-only on Google Ads — never mutates accounts

---

## Installation

```bash
mkdir -p .claude/skills/rsa-single-account/scripts .claude/skills/rsa-single-account/references
for f in SKILL.md README.md rules.md examples.md; do
  curl -o ".claude/skills/rsa-single-account/$f" \
    "https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/rsa-single-account/$f"
done
curl -o .claude/skills/rsa-single-account/references/pipeline-contract.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/rsa-single-account/references/pipeline-contract.md
for f in check_active_accounts.py get_account_website_url.py \
         analyze_competitors_for_rsa.py get_search_campaign_structure.py \
         scrape_website_firecrawl.py get_gmb_reviews.py write_rsa_to_sheet.py \
         vertical_configs.json; do
  curl -o ".claude/skills/rsa-single-account/scripts/$f" \
    "https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/rsa-single-account/scripts/$f"
done

# Step 7 invokes two companion skills (both in this repo) — install their operative files:
mkdir -p .claude/skills/ad-copy-verification-standard .claude/skills/ad-copy-generation-framework
curl -o .claude/skills/ad-copy-verification-standard/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/ad-copy-verification-standard/SKILL.md
for f in SKILL.md framework.md distribution.md technical-specs.md examples.md; do
  curl -o ".claude/skills/ad-copy-generation-framework/$f" \
    "https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/ad-copy-generation-framework/$f"
done
```

The generation step will not work as documented without both companions — the verification standard is the law every claim passes through, and the generation framework holds the 23-element system the distribution comes from.

---

## The Scripts (Ship With This Skill)

All seven workflow scripts are included in [`scripts/`](scripts/) — generic and self-contained. Google Ads credentials come from your `google-ads.yaml`, API keys from environment variables, and the output Sheet from `--sheet-id`.

- **[`check_active_accounts.py`](scripts/check_active_accounts.py)** — lists accounts with spend this month (name ↔ CID) so a name resolves to a Customer ID; reads an optional `accounts.json` registry, otherwise walks the MCC in your `google-ads.yaml` (`--name` filters, `--exclude` skips CIDs)
- **[`get_account_website_url.py`](scripts/get_account_website_url.py)** — given a CID on stdin, returns the business website from ad final URLs (+ business name for the review lookup)
- **[`analyze_competitors_for_rsa.py`](scripts/analyze_competitors_for_rsa.py)** — given a service + location (+ optional vertical), queries the SERP and summarizes competitor USP saturation and gaps; vertical keyword sets live in [`vertical_configs.json`](scripts/vertical_configs.json)
- **[`get_search_campaign_structure.py`](scripts/get_search_campaign_structure.py)** — given a CID, returns active Search campaigns + ad groups
- **[`scrape_website_firecrawl.py`](scripts/scrape_website_firecrawl.py)** — scrapes the site (Firecrawl) and extracts services, credentials, features, hours, and specializations (LLM extraction)
- **[`get_gmb_reviews.py`](scripts/get_gmb_reviews.py)** — Google-Business-Profile review fallback via SERP local results (rating, count, snippets)
- **[`write_rsa_to_sheet.py`](scripts/write_rsa_to_sheet.py)** — clears + writes the RSA rows to a Google Sheet (`--sheet-id`, bare ID or URL)

**Prerequisites:** `google-ads.yaml` at project root (see [google-ads-api-setup](../google-ads-api-setup/)), `SERP_API_KEY` + `FIRECRAWL_API_KEY` + `ANTHROPIC_API_KEY` environment variables (a `.env` at project root works), and `pip install google-ads google-search-results firecrawl-py anthropic google-api-python-client google-auth pyyaml python-dotenv`.

**Adaptation hooks:**

- `vertical_configs.json` ships three **example** vertical keyword sets (auto_repair, plumbing, property_management) — copy a block and adjust the keywords for your vertical
- The "campaign name contains Search" filter in `get_search_campaign_structure.py` is a production-safety convention — adapt the LIKE clause if you name campaigns differently
- Each step's data contract is documented in the SKILL.md, so any script can be swapped for your own implementation (different SERP provider, different scraper) as long as the contract holds

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
Competitive: 9 competitors found (top 5 ads + 3 LSAs analyzed); emphasized 3 USPs no competitor mentions
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

**Before you import:** the Sheet is a review queue, not an approval. Read the set against
[`rules.md`](rules.md) — the false-alarm table covers the misreads (the `[ERROR]` that's
really a naming-convention miss, the "everything unique" thin-SERP artifact, sub-4.5-star
review traps) — then import via Google Ads Editor and confirm with the
[change-history-checker](../change-history-checker/) skill.

---

## License

MIT — use freely in your own brain / repo / agency.

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
