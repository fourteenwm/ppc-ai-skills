#!/usr/bin/env python3
"""RSA Refresh Generator — Claude Code handoff workflow for RSA ad copy generation.

Generates a fresh, complete set of headlines AND descriptions from the
business website. Feature headlines are identical across all ad groups in
an account; only keyword headlines vary by ad group type (brand / geo /
bedroom). Descriptions are generated once (3 universal descriptions) and
applied to all ad groups. Customizer assets (headlines and descriptions)
are always preserved.

Workflow (three stages):

    Stage 1: Prepare context (script runs mechanical steps, outputs JSON, exits)
        python rsa_refresh_generator.py --cid CID --sheet-id SHEET_ID --prepare-for-claude

    Stage 2: Claude Code reads rsa_context_{cid}.json, generates headlines +
             descriptions, saves to copy_{cid}.json with format:
             {"headlines": {"ad_id": ["h1", ...]}, "descriptions": ["d1", "d2", "d3"]}

    Stage 3: Resume with copy file (script writes to sheet)
        python rsa_refresh_generator.py --cid CID --sheet-id SHEET_ID --copy-file copy_{cid}.json

If website scraping fails, error rows are written instead of unverified
copy (enforces "Empty > Inaccurate" policy).

Prerequisites:
    - google-ads.yaml at project root (Google Ads API credentials)
    - token-sheets.json at project root OR a refresh token in google-ads.yaml
      with the spreadsheets scope
    - FIRECRAWL_API_KEY env var (set in .env or shell) for website scraping
      (get a key at firecrawl.dev)
    - pip install google-ads gspread google-auth pyyaml python-dotenv \
          firecrawl-py requests beautifulsoup4 playwright

Optional environment variables:
    COMPLIANCE_PATH — directory containing compliance/ad_copy_validator.py
                      (enables geographic validation)
    SERP_API_PATH   — directory containing get_gmb_reviews.py and
                      analyze_competitors_for_rsa.py (enables GMB social
                      proof and competitor analysis)
"""

import argparse
import io
import json
import os
import re
import sys
from collections import defaultdict
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv

load_dotenv()  # FIRECRAWL_API_KEY and other env vars from .env

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
import gspread
from google.oauth2.credentials import Credentials
import yaml

# Baseline snapshot module (expected alongside this script)
try:
    from rsa_baseline_snapshot import capture_baseline, write_baseline_to_sheet
    BASELINE_AVAILABLE = True
except ImportError:
    BASELINE_AVAILABLE = False

# Optional: geographic validation module. Set COMPLIANCE_PATH env var to a
# directory containing compliance/ad_copy_validator.py to enable.
COMPLIANCE_PATH = os.environ.get('COMPLIANCE_PATH')
COMPLIANCE_AVAILABLE = False
if COMPLIANCE_PATH and os.path.isdir(COMPLIANCE_PATH):
    try:
        sys.path.insert(0, COMPLIANCE_PATH)
        from compliance.ad_copy_validator import (
            validate_ad_copy,
            load_property_locations,
            print_validation_report,
            ValidationSeverity,
        )
        COMPLIANCE_AVAILABLE = True
    except ImportError as e:
        print(f"Note: Compliance module not loadable from {COMPLIANCE_PATH}: {e}")

# Optional: SERP API modules for GMB reviews and competitor analysis.
# Set SERP_API_PATH env var to a directory containing the modules to enable.
SERP_API_PATH = os.environ.get('SERP_API_PATH')
SERP_API_AVAILABLE = False
if SERP_API_PATH and os.path.isdir(SERP_API_PATH):
    try:
        sys.path.insert(0, SERP_API_PATH)
        from get_gmb_reviews import get_apartment_social_proof
        from analyze_competitors_for_rsa import (
            search_competitors,
            extract_competitor_messaging,
            identify_gaps,
            format_for_rsa_generation,
            load_vertical_config,
        )
        SERP_API_AVAILABLE = True
    except ImportError as e:
        print(f"Note: SERP API modules not loadable from {SERP_API_PATH}: {e}")

# Fix encoding for Windows console
if sys.platform == 'win32' and sys.stdout is not None:
    try:
        if hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass


# Reference files live alongside this script in the installed skill
_SKILL_REFS_DIR = os.path.join(os.path.dirname(__file__), '..', 'references')


def _load_generation_instructions() -> str:
    """Load copy generation instructions from the skill's reference files.

    Reads pm-headline-structure.md and description-voice-lifting.md as the
    single source of truth. Raises FileNotFoundError if either is missing.
    """
    headline_file = os.path.join(_SKILL_REFS_DIR, 'pm-headline-structure.md')
    description_file = os.path.join(_SKILL_REFS_DIR, 'description-voice-lifting.md')

    parts = []

    if not os.path.exists(headline_file):
        raise FileNotFoundError(
            f"Required reference file not found: {headline_file}\n"
            f"Ensure the 'references/' directory is alongside 'scripts/' "
            f"in the installed skill."
        )
    with open(headline_file, 'r', encoding='utf-8') as f:
        parts.append(f.read())

    if not os.path.exists(description_file):
        raise FileNotFoundError(
            f"Required reference file not found: {description_file}\n"
            f"Ensure the 'references/' directory is alongside 'scripts/' "
            f"in the installed skill."
        )
    with open(description_file, 'r', encoding='utf-8') as f:
        parts.append(f.read())

    parts.append("""
SOCIAL PROOF RULES:
- If gmb_social_proof.social_proof_headlines has entries, use the first one verbatim
- If gmb_social_proof is null or empty, use an additional feature headline instead
- Do NOT invent ratings or review quotes - only use what's in gmb_social_proof

COMPETITOR DIFFERENTIATION:
- If competitor_insights is provided, prioritize headlines that match "unique_client_usps"
- Avoid or de-emphasize messaging in "avoid_saturated_usps" (everyone uses these)
- Stand out by emphasizing what competitors don't mention

QUALITY REQUIREMENTS:
1. Every headline must be 30 characters or less
2. Feature headlines must reference SPECIFIC amenities from the property
3. NO generic filler like "Modern Living Awaits" or "Come Home To Better"
4. NO truncated headlines - if it doesn't fit, rewrite shorter
5. NO pricing ($X, "from $", "starting at")
6. NO unverified claims (luxury, resort-style, world-class, award-winning)
7. NO proximity claims with specific times/distances unless from website
8. Geography headlines should use neighborhood names, not highways

Ask yourself for each headline: "Could this apply to ANY apartment, or only THIS one?"
If it could apply to any apartment, reject it and write something specific.

Return descriptions as a flat list under the key "descriptions" in your output JSON.
""")

    return '\n\n'.join(parts)


# GAQL Queries
RSA_ADS_QUERY = """
SELECT
    customer.descriptive_name,
    campaign.id,
    campaign.name,
    ad_group.id,
    ad_group.name,
    ad_group_ad.ad.id,
    ad_group_ad.ad.responsive_search_ad.headlines,
    ad_group_ad.ad.responsive_search_ad.descriptions,
    ad_group_ad.ad.responsive_search_ad.path1,
    ad_group_ad.ad.responsive_search_ad.path2,
    ad_group_ad.ad.final_urls,
    ad_group_ad.status
FROM ad_group_ad
WHERE
    ad_group_ad.ad.type = RESPONSIVE_SEARCH_AD
    AND ad_group_ad.status = ENABLED
    AND campaign.status = ENABLED
"""

RSA_ASSET_PERF_QUERY = """
SELECT
    ad_group_ad_asset_view.ad_group_ad,
    ad_group_ad_asset_view.field_type,
    ad_group_ad_asset_view.performance_label,
    ad_group_ad_asset_view.pinned_field,
    asset.id,
    asset.text_asset.text,
    campaign.name,
    ad_group.name
FROM ad_group_ad_asset_view
WHERE
    campaign.status = ENABLED
    AND ad_group_ad_asset_view.enabled = TRUE
"""


def format_cid(cid: str) -> str:
    """Format CID with dashes."""
    cid = cid.replace('-', '')
    return f"{cid[:3]}-{cid[3:6]}-{cid[6:]}"


def query_rsa_ads(client, cid: str) -> dict:
    """Query all enabled RSA ads."""
    ga_service = client.get_service("GoogleAdsService")
    ads = {}

    response = ga_service.search(customer_id=cid, query=RSA_ADS_QUERY)

    for row in response:
        ad = row.ad_group_ad.ad
        rsa = ad.responsive_search_ad
        ad_id = ad.id

        ads[ad_id] = {
            'account_name': row.customer.descriptive_name,
            'cid': cid,
            'campaign_id': row.campaign.id,
            'campaign_name': row.campaign.name,
            'ad_group_id': row.ad_group.id,
            'ad_group_name': row.ad_group.name,
            'ad_id': ad_id,
            'headlines': [{'text': h.text, 'pinned': h.pinned_field.name if h.pinned_field else None}
                         for h in rsa.headlines],
            'descriptions': [{'text': d.text, 'pinned': d.pinned_field.name if d.pinned_field else None}
                            for d in rsa.descriptions],
            'path1': rsa.path1 if rsa.path1 else '',
            'path2': rsa.path2 if rsa.path2 else '',
            'final_url': ad.final_urls[0] if ad.final_urls else '',
        }

    return ads


def query_asset_performance(client, cid: str) -> dict:
    """Query asset performance labels."""
    ga_service = client.get_service("GoogleAdsService")
    performance_data = defaultdict(list)

    try:
        response = ga_service.search(customer_id=cid, query=RSA_ASSET_PERF_QUERY)

        for row in response:
            ad_resource = row.ad_group_ad_asset_view.ad_group_ad
            parts = ad_resource.split('~')
            if len(parts) >= 2:
                ad_id = int(parts[-1])
            else:
                continue

            asset_data = {
                'asset_id': row.asset.id,
                'text': row.asset.text_asset.text if row.asset.text_asset.text else '',
                'field_type': row.ad_group_ad_asset_view.field_type.name,
                'performance_label': row.ad_group_ad_asset_view.performance_label.name,
            }
            performance_data[ad_id].append(asset_data)

    except GoogleAdsException as e:
        print(f"Warning: Could not query asset performance: {e}")

    return performance_data


def merge_performance_data(ads: dict, performance_data: dict) -> dict:
    """Merge asset performance labels into ad data."""
    for ad_id, ad in ads.items():
        if ad_id in performance_data:
            headline_perf = {}
            description_perf = {}

            for asset in performance_data[ad_id]:
                if 'HEADLINE' in asset['field_type']:
                    headline_perf[asset['text']] = asset['performance_label']
                elif 'DESCRIPTION' in asset['field_type']:
                    description_perf[asset['text']] = asset['performance_label']

            for h in ad['headlines']:
                h['performance'] = headline_perf.get(h['text'], 'UNKNOWN')

            for d in ad['descriptions']:
                d['performance'] = description_perf.get(d['text'], 'UNKNOWN')
        else:
            for h in ad['headlines']:
                h['performance'] = 'NO_DATA'
            for d in ad['descriptions']:
                d['performance'] = 'NO_DATA'

    return ads


def scrape_with_playwright(url: str, max_retries: int = 3, retry_delay: int = 5) -> str:
    """Scrape website using Playwright for Cloudflare/403-blocked sites.

    Returns the text content of the page, or empty string on failure.
    """
    try:
        import asyncio
        import time
        from playwright.async_api import async_playwright

        async def fetch_page(wait_until: str = 'networkidle', timeout: int = 30000):
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080}
                )
                page = await context.new_page()

                try:
                    await page.goto(url, wait_until=wait_until, timeout=timeout)
                    await page.wait_for_timeout(2000)

                    text_content = await page.evaluate('''() => {
                        const toRemove = document.querySelectorAll('script, style, nav, footer, header, noscript');
                        toRemove.forEach(el => el.remove());
                        return document.body.innerText;
                    }''')

                    await browser.close()
                    return text_content
                except Exception as e:
                    await browser.close()
                    raise e

        strategies = [
            {'wait_until': 'networkidle', 'timeout': 30000},
            {'wait_until': 'domcontentloaded', 'timeout': 45000},
            {'wait_until': 'load', 'timeout': 60000},
        ]

        for attempt in range(max_retries):
            strategy = strategies[min(attempt, len(strategies) - 1)]
            try:
                if attempt > 0:
                    print(f"  Playwright retry {attempt + 1}/{max_retries} (waiting {retry_delay}s, using {strategy['wait_until']})...")
                    time.sleep(retry_delay)

                content = asyncio.run(fetch_page(**strategy))
                if content:
                    print(f"Playwright scraped {len(content)} characters")
                    return content[:15000]

            except Exception as e:
                print(f"  Playwright attempt {attempt + 1} failed: {str(e)[:100]}")
                if attempt == max_retries - 1:
                    print(f"  All {max_retries} Playwright attempts failed for {url}")

        return ''

    except ImportError:
        print("Playwright not installed. Run: pip install playwright && playwright install chromium")
        return ''
    except Exception as e:
        print(f"Playwright error: {e}")
        return ''


def scrape_property_website(url: str) -> Dict[str, Any]:
    """Scrape property website using Firecrawl (preferred) with requests/Playwright fallback."""

    api_key = os.getenv('FIRECRAWL_API_KEY')
    if api_key:
        try:
            from firecrawl import Firecrawl

            app = Firecrawl(api_key=api_key)

            print(f"Scraping property website with Firecrawl: {url}")
            scrape_result = app.scrape(url, formats=['markdown'])

            markdown = getattr(scrape_result, 'markdown', None) or (scrape_result.get('markdown') if isinstance(scrape_result, dict) else None)
            if not markdown:
                raise ValueError("Firecrawl returned empty content")

            content = markdown
            print(f"Firecrawl scraped {len(content)} characters")

            # Try to find floor plans or amenities page
            try:
                map_result = app.map(url=url)
                site_urls = []
                links = getattr(map_result, 'links', None) or (map_result.get('links') if isinstance(map_result, dict) else None) or (map_result if isinstance(map_result, list) else [])
                for link in links:
                    if isinstance(link, str):
                        site_urls.append(link)
                    elif hasattr(link, 'url'):
                        site_urls.append(link.url)
                    elif isinstance(link, dict):
                        site_urls.append(link.get('url', ''))

                print(f"Firecrawl mapped {len(site_urls)} URLs on site")

                for site_url in site_urls[:20]:
                    url_lower = site_url.lower()
                    if any(kw in url_lower for kw in ['amenities', 'features', 'floor-plan', 'floorplan']):
                        try:
                            extra_result = app.scrape(site_url, formats=['markdown'])
                            extra_md = getattr(extra_result, 'markdown', None) or (extra_result.get('markdown') if isinstance(extra_result, dict) else None)
                            if extra_md:
                                content += "\n\n=== ADDITIONAL PAGE ===\n" + extra_md
                                print(f"Also scraped: {site_url}")
                                break
                        except Exception:
                            pass
            except Exception:
                pass

            return {'content': content, 'url': url}

        except ImportError:
            print("Firecrawl not installed, falling back to requests...")
        except Exception as e:
            print(f"Firecrawl error: {e}, falling back to requests...")

    # Fallback: use requests + beautifulsoup
    print(f"Scraping property website with requests fallback: {url}")
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        text = soup.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        content = '\n'.join(lines)

        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            content = f"META DESCRIPTION: {meta_desc['content']}\n\n{content}"

        print(f"Scraped {len(content)} characters")
        return {'content': content[:15000], 'url': url}

    except Exception as e:
        print(f"Requests fallback error: {e}")
        print(f"Trying Playwright fallback for: {url}")
        playwright_content = scrape_with_playwright(url)
        if playwright_content:
            return {'content': playwright_content, 'url': url}

        print(f"WARNING: All scraping methods failed for {url} - headlines will be generic only")
        return {
            'content': '',
            'url': url,
            'scrape_failed': True
        }


def extract_basic_property_info(website_data: Dict[str, Any], cid: str) -> Dict[str, Any]:
    """Extract basic property info without LLM calls.

    If the COMPLIANCE module is loaded, looks up property metadata from
    property_locations.json. Otherwise, falls back to URL-based extraction.
    Full feature extraction is left to Claude Code when it reads the
    context JSON.
    """
    features = {
        "property_name": "",
        "city": "",
        "state": "",
        "amenities": [],
        "unit_features": [],
        "lifestyle": [],
        "unique_points": [],
    }

    if website_data.get('scrape_failed') or not website_data.get('content', '').strip():
        features['scrape_failed'] = True
        print("WARNING: No website content available")

    if COMPLIANCE_AVAILABLE:
        try:
            property_locations = load_property_locations()
            prop_data = property_locations.get('properties', {}).get(cid, {})
            if prop_data:
                features['property_name'] = prop_data.get('property_name', '')
                features['city'] = prop_data.get('city', '')
                features['state'] = prop_data.get('state', '')
                print(f"Property info from locations file: {features['property_name']} in {features['city']}, {features['state']}")
        except Exception as e:
            print(f"Warning: Could not load property_locations: {e}")

    # Fallback: extract property name from URL
    if not features['property_name']:
        url = website_data.get('url', '')
        if url:
            match = re.search(r'https?://(?:www\.)?([^./]+)', url)
            if match:
                features['property_name'] = match.group(1).replace('-', ' ').title()
                print(f"Property name from URL: {features['property_name']}")

    return features


# Common hallucinated terms that Claude often generates but can't be verified.
# These are stripped from generated copy unless they appear in the property name.
HALLUCINATION_PATTERNS = [
    # Property type hallucinations (apartments only unless verified)
    'townhome', 'townhomes', 'townhouse', 'townhouses',
    'condo', 'condos', 'condominium', 'condominiums',
    'single family', 'single-family', 'detached',
    ' homes',  # "Bedroom Homes" etc. - these are apartments, not homes
    # Proximity claims (cannot verify distance)
    'near the strip', 'minutes from', 'steps from', 'close to downtown',
    'walking distance', 'near everything',
    # Unverified luxury terms (unless explicitly on website)
    'upscale', 'high-end', 'exclusive', 'elite', 'premier',
    'world-class', 'best in class', 'top-rated',
    # Unverified newness claims
    'brand new', 'newly built', 'new community', 'just opened',
    'grand opening', 'now open', 'new construction',
    # Unverified amenity claims
    'pet park', 'dog park', 'bark park',
    'rooftop', 'sky lounge', 'infinity pool',
    # Unverified superlatives
    'best apartments', 'top apartments', '#1', 'number one',
    'most affordable', 'lowest prices', 'cheapest',
    # Pricing — NEVER include as it changes frequently
    'from $', 'starting at $', 'starting from', 'prices from',
    '/mo', '/month', 'per month', 'a month',
    # Incentive/promotional terms — NEVER include (changes frequently)
    'free', 'weeks free', 'month free', 'months free',
    'special', 'specials', 'deal', 'deals', 'offer', 'limited time',
    'discount', 'save', 'savings', 'reduced', 'waived', 'waive',
    'no deposit', 'zero deposit', 'move-in special', 'move in special',
    'application fee', 'admin fee', 'look and lease',
]

# Regex pattern for dollar amounts (e.g., $1500, $1,500, $999)
PRICE_PATTERN = re.compile(r'\$[\d,]+', re.IGNORECASE)


def has_duplicate_words(text: str) -> str:
    """Check for duplicate consecutive words like 'Apartments Apartments'.

    Returns the duplicated word if found, None otherwise.
    """
    words = text.split()
    for i in range(len(words) - 1):
        if words[i].lower() == words[i + 1].lower():
            return words[i]
    return None


def is_unverified_copy(text: str, property_name: str = "") -> tuple:
    """Check if text contains unverified/hallucinated patterns.

    Used to verify EXISTING ad copy (headlines and descriptions).

    Args:
        text: The ad copy text to check.
        property_name: Exact property name — patterns that appear in the
            property name are exempt (e.g. a property literally named
            "Harbor Homes" should not be flagged for containing "homes").

    Returns: (is_unverified: bool, reason: str or None)
    """
    if not text or not text.strip():
        return (False, None)

    # Skip customizers — they are always valid
    if re.search(r'\{CUSTOMIZER\.[^}]+\}', text):
        return (False, None)

    text_lower = text.lower()
    property_name_lower = property_name.lower().strip() if property_name else ""

    duplicate = has_duplicate_words(text)
    if duplicate:
        return (True, f"duplicate pattern: '{duplicate} {duplicate}'")

    if PRICE_PATTERN.search(text):
        return (True, "contains pricing")

    for pattern in HALLUCINATION_PATTERNS:
        if pattern in text_lower:
            if property_name_lower and pattern in property_name_lower:
                continue  # pattern is part of property name, allow it
            return (True, f"matched: '{pattern}'")

    return (False, None)


def filter_hallucinated_headlines(headlines: List[str], property_name: str = "") -> List[str]:
    """Filter out headlines containing common hallucinated terms.

    Args:
        headlines: List of headline strings to filter.
        property_name: Exact property name — exempt from pattern matching
            so names like "Harbor Homes" aren't falsely filtered.

    Returns filtered list with hallucinated headlines removed.
    """
    property_name_lower = property_name.lower().strip() if property_name else ""

    filtered = []
    for headline in headlines:
        headline_lower = headline.lower()
        is_hallucination = False

        duplicate = has_duplicate_words(headline)
        if duplicate:
            print(f"  [FILTER] Removed duplicate pattern: '{headline}' ('{duplicate} {duplicate}')")
            is_hallucination = True

        if not is_hallucination and PRICE_PATTERN.search(headline):
            print(f"  [FILTER] Removed pricing: '{headline}' (contains dollar amount)")
            is_hallucination = True

        if not is_hallucination:
            for pattern in HALLUCINATION_PATTERNS:
                if pattern in headline_lower:
                    if property_name_lower and pattern in property_name_lower:
                        continue
                    print(f"  [FILTER] Removed hallucination: '{headline}' (matched: '{pattern}')")
                    is_hallucination = True
                    break

        if not is_hallucination:
            filtered.append(headline)

    return filtered


def is_customizer(text: str) -> bool:
    """Check if text contains ad customizer code."""
    return bool(re.search(r'\{CUSTOMIZER\.[^}]+\}', text))


# ============================================================================
# PM HEADLINE HELPERS
# ============================================================================
# This script is optimized for property management accounts. The headline
# structure (14 AI-generated + 1 customizer) is defined in
# references/pm-headline-structure.md. These helpers generate the mechanical
# parts (keyword, brand, CTA) used by both the script and Claude Code
# during the handoff workflow.
#
# To adapt for another vertical, replace the reference files and update
# generate_keyword_headlines() / generate_brand_headline() below.
# ============================================================================

REQUIRED_CTAS = [
    "Schedule A Tour",
    "Call Us Now"
]


def generate_keyword_headlines(ad_group_name: str, property_name: str, property_address: str = "") -> List[str]:
    """Generate 2 keyword-driven headlines based on ad group type."""
    ad_group_lower = ad_group_name.lower()
    keywords = []

    if any(x in ad_group_lower for x in ['1 bed', '2 bed', '3 bed', 'studio', 'bedroom']):
        # Bedroom ad group — extract bedroom count
        match = re.search(r'(\d+|studio)\s*bed', ad_group_lower)
        if match:
            bdrm = match.group(1).title()
            if bdrm.lower() == 'studio':
                keywords = ["Studio Apartments", "Studio Apts For Rent"]
            else:
                keywords = [f"{bdrm} Bedroom Apartments", f"{bdrm} Bedroom Apts For Rent"]
        else:
            keywords = ["Apartments For Rent", "Luxury Apts For Rent"]

    elif any(x in ad_group_lower for x in ['brand', property_name.lower().split()[0] if property_name else '']):
        # Brand ad group
        short_name = property_name.split()[0] if property_name else "Property"
        keywords = [f"{short_name} Apartments", f"{short_name} Apts For Rent"]

    else:
        # Geo ad group — use the ad group name as the geography
        geo = ad_group_name.replace('-', ' ').replace('_', ' ').strip()
        address_lower = property_address.lower() if property_address else ""
        geo_lower = geo.lower()

        if 'apartment' in geo_lower or 'apts' in geo_lower:
            keywords = [geo, f"{geo} For Rent"]
        elif geo_lower in address_lower:
            keywords = [f"{geo} Apartments", f"{geo} Apts For Rent"]
        else:
            keywords = [f"Apts Near {geo}", f"{geo} Apts For Rent"]

    # Ensure all are ≤30 chars with abbreviations
    validated = []
    for kw in keywords:
        if len(kw) <= 30:
            validated.append(kw)
        else:
            shortened = kw.replace("Apartments", "Apts").replace("Bedroom", "BR")
            if len(shortened) <= 30:
                validated.append(shortened)
            else:
                validated.append(kw[:30])

    return validated[:2]


def generate_brand_headline(property_name: str) -> str:
    """Generate 1 brand headline."""
    if 'apartment' in property_name.lower():
        headline = property_name
    else:
        headline = f"{property_name} Apartments"
    if len(headline) <= 30:
        return headline
    headline = f"{property_name} Apts"
    if len(headline) <= 30:
        return headline
    return property_name[:30]


def has_cta(headlines: List[dict], cta: str) -> bool:
    """Check if a CTA (or similar variation) exists in headlines."""
    cta_lower = cta.lower()
    for h in headlines:
        text_lower = h['text'].lower()
        if cta_lower in text_lower or text_lower in cta_lower:
            return True
        if 'schedule' in cta_lower and 'schedule' in text_lower and 'tour' in text_lower:
            return True
        if 'call' in cta_lower and 'call' in text_lower and ('today' in text_lower or 'now' in text_lower):
            return True
    return False


def normalize_headline(text: str) -> str:
    """Normalize headline text for deduplication comparison."""
    return text.strip().lower()


def add_headline_if_unique(headlines_list: List[dict], seen_normalized: set, headline_dict: dict, changes_list: List[str], change_msg: str = None) -> bool:
    """Add headline to list only if unique. Returns True if added."""
    normalized = normalize_headline(headline_dict['text'])
    if normalized in seen_normalized:
        return False
    seen_normalized.add(normalized)
    headlines_list.append(headline_dict)
    if change_msg:
        changes_list.append(change_msg)
    return True


def refresh_rsas_with_claude_copy(ads: dict, features: Dict[str, Any], claude_headlines: dict, claude_descriptions: list = None) -> dict:
    """Refresh RSAs using Claude Code-generated headlines and descriptions.

    Args:
        ads: Original ads data
        features: Extracted property features
        claude_headlines: Dict with ad_id -> list of headlines from Claude Code
        claude_descriptions: List of 3 account-wide descriptions from Claude Code

    Returns:
        Refreshed ads with Claude Code headlines and descriptions
    """
    refreshed_ads = {}
    property_name = features.get('property_name', 'Property')

    for ad_id, ad in ads.items():
        refreshed_ad = ad.copy()
        refreshed_ad['headlines'] = []
        refreshed_ad['changes'] = []
        seen_headlines = set()

        ad_headlines = claude_headlines.get(str(ad_id), claude_headlines.get(ad_id, []))

        # Categorize existing headlines
        customizer_headlines = []
        for i, h in enumerate(ad['headlines']):
            if is_customizer(h['text']):
                customizer_headlines.append(h)
                refreshed_ad['changes'].append(f"Kept H{i+1} (customizer): {h['text']}")

        for h in customizer_headlines:
            add_headline_if_unique(
                refreshed_ad['headlines'], seen_headlines,
                {'text': h['text'], 'pinned': h.get('pinned'), 'status': 'KEPT (customizer)', 'original_performance': h.get('performance', 'UNKNOWN')},
                refreshed_ad['changes']
            )

        for headline in ad_headlines:
            if len(refreshed_ad['headlines']) >= 15:
                break
            if len(headline) > 30:
                refreshed_ad['changes'].append(f"Skipped (>30 chars): {headline}")
                continue
            add_headline_if_unique(
                refreshed_ad['headlines'], seen_headlines,
                {'text': headline, 'pinned': None, 'status': 'CLAUDE CODE', 'original_performance': 'NEW'},
                refreshed_ad['changes'], f"Added Claude Code headline: {headline}"
            )

        # Minimum headline threshold: 10. Below that, skip the ad group.
        if len(refreshed_ad['headlines']) < 10:
            headline_count = len(refreshed_ad['headlines'])
            print(f"  [SKIP] Ad group '{ad['ad_group_name']}' has only {headline_count}/15 headlines (below minimum 10). Skipping.")
            refreshed_ad['_skipped'] = True
            refreshed_ad['_skip_reason'] = f"Only {headline_count}/15 headlines (minimum 10 required)"

        # Description refresh: preserve customizers, fill with Claude Code descriptions
        new_descriptions = []

        for i, d in enumerate(ad['descriptions']):
            desc_text = d['text'] if isinstance(d, dict) else d
            if is_customizer(desc_text):
                new_descriptions.append(d if isinstance(d, dict) else {'text': d, 'pinned': None})
                refreshed_ad['changes'].append(f"Kept customizer description D{i+1}: {desc_text[:50]}")

        customizer_desc_count = len(new_descriptions)
        if claude_descriptions:
            for desc in claude_descriptions:
                if len(new_descriptions) >= 4:
                    break
                if len(desc) > 90:
                    refreshed_ad['changes'].append(f"Skipped description (>90 chars): {desc[:50]}...")
                    continue
                new_descriptions.append({'text': desc, 'pinned': None})
                refreshed_ad['changes'].append(f"Added description: {desc[:50]}...")
        else:
            # No descriptions provided — copy originals (backward compat)
            for d in ad['descriptions']:
                desc_text = d['text'] if isinstance(d, dict) else d
                if not is_customizer(desc_text):
                    new_descriptions.append(d if isinstance(d, dict) else {'text': d, 'pinned': None})

        refreshed_ad['changes'].append(
            f"Descriptions: {customizer_desc_count} customizers preserved, "
            f"{len(new_descriptions) - customizer_desc_count} {'generated' if claude_descriptions else 'original'}, "
            f"{len(new_descriptions)} total"
        )

        refreshed_ad['descriptions'] = new_descriptions[:4]

        refreshed_ads[ad_id] = refreshed_ad

    return refreshed_ads


def _get_sheets_client(
    sheets_token_path: str = "token-sheets.json",
    ads_config_path: str = "google-ads.yaml",
) -> gspread.Client:
    """Create gspread client.

    Prefers a dedicated token-sheets.json (OAuth with spreadsheets scope).
    Falls back to the refresh token in google-ads.yaml if present with
    the spreadsheets scope.
    """
    token_data = None
    if sheets_token_path and os.path.exists(sheets_token_path):
        with open(sheets_token_path, 'r') as f:
            token_data = json.load(f)

    if not token_data:
        if not os.path.exists(ads_config_path):
            raise FileNotFoundError(
                f"Could not find OAuth credentials.\n"
                f"  Looked for: {sheets_token_path}\n"
                f"  Fell back to: {ads_config_path} (also not found)\n"
                f"Provide --sheets-token or --config with a refresh token "
                f"that has the spreadsheets scope."
            )
        with open(ads_config_path, 'r', encoding='utf-8') as f:
            ads_config = yaml.safe_load(f)

        credentials = Credentials(
            token=None,
            refresh_token=ads_config.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=ads_config.get("client_id"),
            client_secret=ads_config.get("client_secret"),
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.readonly",
            ],
        )
        return gspread.authorize(credentials)

    client_id = token_data.get('client_id')
    client_secret = token_data.get('client_secret')

    if (not client_id or not client_secret) and os.path.exists(ads_config_path):
        with open(ads_config_path, 'r') as f:
            ads_config = yaml.safe_load(f)
            client_id = client_id or ads_config.get('client_id')
            client_secret = client_secret or ads_config.get('client_secret')

    credentials = Credentials(
        token=token_data.get('token') or token_data.get('access_token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri=token_data.get('token_uri', "https://oauth2.googleapis.com/token"),
        client_id=client_id,
        client_secret=client_secret,
        scopes=token_data.get('scopes', ["https://www.googleapis.com/auth/spreadsheets"]),
    )
    return gspread.authorize(credentials)


def write_to_sheet(original_ads: dict, refreshed_ads: dict, sheet_id: str, cid: str,
                   clear: bool = False,
                   sheets_token_path: str = "token-sheets.json",
                   ads_config_path: str = "google-ads.yaml") -> str:
    """Write to Google Sheet with two tabs: Original RSAs and Refreshed RSAs."""

    gc = _get_sheets_client(sheets_token_path, ads_config_path)
    spreadsheet = gc.open_by_key(sheet_id)

    # Tab 1: Original RSAs
    print("Writing Original RSAs tab...")
    try:
        ws_original = spreadsheet.worksheet("Original RSAs")
        if clear:
            ws_original.clear()
    except gspread.exceptions.WorksheetNotFound:
        ws_original = spreadsheet.add_worksheet(title="Original RSAs", rows=500, cols=35)

    orig_headers = ['Account Name', 'Customer ID', 'Campaign', 'Ad Group', 'Ad ID']
    for i in range(1, 16):
        orig_headers.append(f'Headline {i}')
        orig_headers.append(f'H{i} Performance')
    for i in range(1, 5):
        orig_headers.append(f'Description {i}')
    orig_headers.extend(['Path 1', 'Path 2', 'Final URL'])

    if not clear:
        orig_rows = []
        existing_rows = len(ws_original.get_all_values())
        if existing_rows == 0:
            orig_rows = [orig_headers]
            existing_rows = 1
    else:
        orig_rows = [orig_headers]
        existing_rows = 1
    for ad_id, ad in original_ads.items():
        if ad_id in refreshed_ads and refreshed_ads[ad_id].get('_skipped'):
            continue
        row = [
            ad['account_name'],
            format_cid(ad['cid']),
            ad['campaign_name'],
            ad['ad_group_name'],
            str(ad_id)
        ]
        for i in range(15):
            if i < len(ad['headlines']):
                row.append(ad['headlines'][i]['text'])
                row.append(ad['headlines'][i].get('performance', 'UNKNOWN'))
            else:
                row.append('')
                row.append('')
        for i in range(4):
            if i < len(ad['descriptions']):
                row.append(ad['descriptions'][i]['text'])
            else:
                row.append('')
        row.extend([ad['path1'], ad['path2'], ad['final_url']])
        orig_rows.append(row)

    if not clear and existing_rows > 1:
        ws_original.update(f'A{existing_rows + 1}', orig_rows)
        print(f"Appended {len(orig_rows)} rows to Original RSAs tab (total: {existing_rows + len(orig_rows)})")
    else:
        ws_original.update('A1', orig_rows)
        print(f"Wrote {len(orig_rows)-1} rows to Original RSAs tab")

    # Tab 2: Refreshed RSAs (Google Ads Editor format)
    print("Writing Refreshed RSAs tab...")
    try:
        ws_refreshed = spreadsheet.worksheet("Refreshed RSAs")
        if clear:
            ws_refreshed.clear()
    except gspread.exceptions.WorksheetNotFound:
        ws_refreshed = spreadsheet.add_worksheet(title="Refreshed RSAs", rows=500, cols=30)

    ref_headers = ['Account Name', 'Customer ID', 'Campaign', 'Ad Group']
    for i in range(1, 16):
        ref_headers.append(f'Headline {i}')
    for i in range(1, 5):
        ref_headers.append(f'Description {i}')
    ref_headers.extend(['Path 1', 'Path 2', 'Final URL', 'Ad ID', 'Validation Status', 'Validation Errors', 'Changes Made'])

    if not clear:
        ref_rows = []
        ref_existing_rows = len(ws_refreshed.get_all_values())
        if ref_existing_rows == 0:
            ref_rows = [ref_headers]
            ref_existing_rows = 1
    else:
        ref_rows = [ref_headers]
        ref_existing_rows = 1
    for ad_id, ad in refreshed_ads.items():
        if ad.get('_skipped'):
            continue
        row = [
            ad['account_name'],
            format_cid(ad['cid']),
            ad['campaign_name'],
            ad['ad_group_name']
        ]
        for i in range(15):
            if i < len(ad['headlines']):
                row.append(ad['headlines'][i]['text'])
            else:
                row.append('')
        for i in range(4):
            if i < len(ad['descriptions']):
                row.append(ad['descriptions'][i]['text'])
            else:
                row.append('')
        row.extend([
            ad['path1'],
            ad['path2'],
            ad['final_url'],
            str(ad_id),
            ad.get('validation_status', 'N/A'),
            '; '.join(ad.get('validation_errors', [])) or 'None',
            '; '.join(ad.get('changes', ['No changes']))
        ])
        ref_rows.append(row)

    if not clear and ref_existing_rows > 1:
        ws_refreshed.update(f'A{ref_existing_rows + 1}', ref_rows)
        print(f"Appended {len(ref_rows)} rows to Refreshed RSAs tab (total: {ref_existing_rows + len(ref_rows)})")
    else:
        ws_refreshed.update('A1', ref_rows)
        print(f"Wrote {len(ref_rows)-1} rows to Refreshed RSAs tab")

    return f"https://docs.google.com/spreadsheets/d/{sheet_id}"


def main():
    parser = argparse.ArgumentParser(description="RSA Refresh Generator")
    parser.add_argument('--cid', required=True, help='Customer ID (no dashes)')
    parser.add_argument('--sheet-id', required=True, help='Google Sheet ID for output')
    parser.add_argument('--config', default='google-ads.yaml',
                        help='Path to google-ads.yaml (default: ./google-ads.yaml)')
    parser.add_argument('--sheets-token', default='token-sheets.json',
                        help='Path to OAuth token with sheets scope (default: ./token-sheets.json)')
    parser.add_argument('--dry-run', action='store_true', help='Preview only, no sheet write')
    parser.add_argument('--strict', action='store_true',
                        help='Block output on geographic validation errors (default: flag only)')
    parser.add_argument('--skip-validation', action='store_true',
                        help='Skip geographic validation entirely')
    parser.add_argument('--prepare-for-claude', action='store_true',
                        help='Stage 1: prepare context JSON for Claude Code and exit')
    parser.add_argument('--copy-file', type=str,
                        help='Stage 3: Path to JSON file with Claude Code-generated headlines + descriptions')
    parser.add_argument('--headlines-file', type=str,
                        help='(Deprecated, use --copy-file) Path to JSON file with Claude Code-generated headlines')
    parser.add_argument('--clear', action='store_true',
                        help='Clear existing sheet data before writing (default: append)')
    parser.add_argument('--baseline-sheet-id',
                        help='Optional: capture pre-refresh baseline metrics to this sheet. '
                             'Omit to skip baseline capture.')
    parser.add_argument('--skip-baseline', action='store_true',
                        help='Skip baseline performance capture (default if --baseline-sheet-id not provided)')

    args = parser.parse_args()
    cid = args.cid.replace('-', '')

    print("=" * 70)
    print("RSA REFRESH GENERATOR")
    print("=" * 70)
    print(f"Account CID: {format_cid(cid)}")
    print(f"Output Sheet: {args.sheet_id}")
    print("=" * 70)

    # Step 1: Query existing RSAs
    print("\n[1/5] Loading Google Ads client...")
    client = GoogleAdsClient.load_from_storage(args.config)

    print("\n[2/5] Querying existing RSAs...")
    ads = query_rsa_ads(client, cid)
    print(f"Found {len(ads)} enabled RSA ads")

    if not ads:
        print("No RSAs found. Exiting.")
        return

    print("Querying asset performance labels...")
    performance_data = query_asset_performance(client, cid)
    ads = merge_performance_data(ads, performance_data)

    # Baseline performance capture (before any ad copy work)
    # Skip on --copy-file resume (baseline was already captured in the prepare step)
    skip_baseline = (
        args.skip_baseline
        or args.copy_file
        or args.headlines_file
        or not args.baseline_sheet_id  # opt-in via flag
    )
    if not skip_baseline and BASELINE_AVAILABLE:
        first_ad_for_name = list(ads.values())[0]
        baseline_account_name = first_ad_for_name['account_name']
        try:
            baseline = capture_baseline(client, cid, performance_data, baseline_account_name)
            if not args.dry_run:
                write_baseline_to_sheet(baseline, args.baseline_sheet_id, args.sheets_token, args.config)
            else:
                print("  [Baseline] DRY RUN - skipping sheet write")
        except Exception as e:
            print(f"\n  WARNING: Baseline capture failed: {e}")
            print("  Continuing with RSA refresh...\n")
    elif args.skip_baseline or not args.baseline_sheet_id:
        print("\n  [Baseline] Skipped (no --baseline-sheet-id provided or --skip-baseline set)")
    elif not BASELINE_AVAILABLE:
        print("\n  [Baseline] rsa_baseline_snapshot module not available — skipping")

    # Get property URL
    first_ad = list(ads.values())[0]
    property_url = first_ad['final_url']
    account_name = first_ad['account_name']

    # Step 2: Scrape website
    print(f"\n[3/5] Scraping property website: {property_url}")
    website_data = scrape_property_website(property_url)

    # Step 3: Extract basic property info
    print("\n[4/5] Extracting basic property info...")
    features = extract_basic_property_info(website_data, cid)

    # Early exit on scrape failure (non-Claude-Code mode)
    if features.get('scrape_failed') and not args.prepare_for_claude:
        print("\n" + "=" * 70)
        print("ERROR: Website scraping failed for all methods (Firecrawl, requests, Playwright)")
        print(f"URL: {property_url}")
        print("Policy: Empty > Inaccurate - no ad copy will be generated.")
        print("=" * 70)

        if not args.dry_run:
            error_msg = "SCRAPE FAILED - NO COPY GENERATED"
            error_change = "ERROR: Website scraping failed. No ad copy generated. Verify URL and retry."
            error_ads = {}
            for ad_id, ad in ads.items():
                error_ad = ad.copy()
                error_ad['headlines'] = [
                    {'text': error_msg, 'pinned': None, 'status': 'ERROR', 'original_performance': 'N/A'}
                    for _ in range(15)
                ]
                error_ad['descriptions'] = [
                    {'text': error_msg, 'pinned': None}
                    for _ in range(4)
                ]
                error_ad['changes'] = [error_change]
                error_ad['validation_status'] = 'N/A'
                error_ad['validation_errors'] = []
                error_ads[ad_id] = error_ad

            print("\nWriting error rows to Google Sheet...")
            sheet_url = write_to_sheet(
                ads, error_ads, args.sheet_id, cid,
                clear=args.clear,
                sheets_token_path=args.sheets_token,
                ads_config_path=args.config,
            )
            print(f"Error rows written. Sheet URL: {sheet_url}")
        else:
            print("\n[DRY RUN] Would write error rows to sheet")

        return

    # Claude Code workflow: prepare context and exit
    if args.prepare_for_claude:
        context_file = f"rsa_context_{cid}.json"

        # Get GMB social proof data (if SERP API modules loaded)
        gmb_data = None
        if SERP_API_AVAILABLE and features.get('property_name') and features.get('city') and features.get('state'):
            print(f"\n[GMB] Looking up reviews for: {features['property_name']} in {features['city']}, {features['state']}")
            try:
                gmb_data = get_apartment_social_proof(
                    features['property_name'],
                    features['city'],
                    features['state']
                )
                if gmb_data and gmb_data.get('reviews_available'):
                    print(f"[GMB] Found: {gmb_data.get('rating')}★ ({gmb_data.get('reviews_count')} reviews)")
                    if gmb_data.get('rating_meets_threshold'):
                        print(f"[GMB] Rating meets 4.5 threshold - will use rating headline")
                    else:
                        print(f"[GMB] Rating below 4.5 - will use review quote instead")
                    for hl in gmb_data.get('social_proof_headlines', []):
                        print(f"[GMB] Generated: \"{hl['text']}\" ({len(hl['text'])} chars)")
                elif gmb_data and gmb_data.get('lookup_failed'):
                    print(f"[GMB] Lookup failed - will skip social proof headline")
                else:
                    print(f"[GMB] No usable social proof found")
            except Exception as e:
                print(f"[GMB] Error: {e}")
                gmb_data = None
        else:
            if not SERP_API_AVAILABLE:
                print("[GMB] SERP API not available - skipping GMB lookup")
            else:
                print("[GMB] Missing property name/city/state - skipping GMB lookup")

        # Get competitor analysis data (if SERP API modules loaded)
        competitor_data = None
        if SERP_API_AVAILABLE and features.get('city') and features.get('state'):
            print(f"\n[COMPETITOR] Analyzing apartment ads in {features['city']}, {features['state']}")
            try:
                pm_vertical_config = load_vertical_config('property_management')

                search_results = search_competitors(
                    "apartments",
                    f"{features['city']} {features['state']}",
                    vertical='property_management'
                )
                if search_results:
                    competitor_analysis = extract_competitor_messaging(search_results, pm_vertical_config)
                    client_usps = features.get('amenities', []) + features.get('unique_points', [])
                    gap_analysis = identify_gaps(client_usps, competitor_analysis)
                    competitor_data = format_for_rsa_generation(competitor_analysis, gap_analysis)

                    print(f"[COMPETITOR] Found {competitor_analysis.get('competitors_found', 0)} competitors")
                    print(f"[COMPETITOR] Matched {len(competitor_analysis.get('common_usps', []))} USP categories")
                    if competitor_data.get('differentiation_opportunities', {}).get('unique_client_usps'):
                        print(f"[COMPETITOR] Unique angles: {competitor_data['differentiation_opportunities']['unique_client_usps'][:3]}")
                    if competitor_data.get('differentiation_opportunities', {}).get('avoid_saturated_usps'):
                        print(f"[COMPETITOR] Avoid (saturated): {competitor_data['differentiation_opportunities']['avoid_saturated_usps'][:3]}")
                else:
                    print("[COMPETITOR] No search results found")
            except Exception as e:
                print(f"[COMPETITOR] Error: {e}")
                import traceback
                traceback.print_exc()
                competitor_data = None
        else:
            if not SERP_API_AVAILABLE:
                print("[COMPETITOR] SERP API not available - skipping competitor analysis")
            else:
                print("[COMPETITOR] Missing city/state - skipping competitor analysis")

        context_data = {
            'cid': cid,
            'account_name': account_name,
            'property_url': property_url,
            'features': features,
            'website_text': website_data.get('content', '')[:15000],
            'gmb_social_proof': gmb_data,
            'competitor_insights': competitor_data,
            'ads': {
                ad_id: {
                    'ad_group_name': ad['ad_group_name'],
                    'campaign_name': ad['campaign_name'],
                    'existing_headlines': [h['text'] for h in ad['headlines']],
                    'headlines_needed': 15 - len([h for h in ad['headlines'] if h.get('performance') != 'LOW']),
                    'existing_descriptions': [d['text'] for d in ad['descriptions']],
                    'customizer_descriptions': [d['text'] for d in ad['descriptions'] if is_customizer(d['text'])],
                }
                for ad_id, ad in ads.items()
            },
            'instructions': _load_generation_instructions(),
        }

        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(context_data, f, indent=2, ensure_ascii=False)

        print(f"\n[CLAUDE CODE MODE] Context saved to: {context_file}")
        print(f"\nContext includes:")
        print(f"  - Property features: {len(features.get('amenities', [])) + len(features.get('unit_features', []))} items")
        print(f"  - GMB social proof: {'Yes' if gmb_data and gmb_data.get('reviews_available') else 'No'}")
        print(f"  - Competitor insights: {'Yes' if competitor_data else 'No'}")
        print(f"\nNext steps:")
        print(f"1. Claude Code reads {context_file}")
        print(f"2. Claude Code generates headlines + descriptions and saves to: copy_{cid}.json")
        print(f"   Format: {{\"headlines\": {{\"ad_id\": [\"h1\", ...]}}, \"descriptions\": [\"d1\", \"d2\", \"d3\"]}}")
        print(f"3. Resume with: --cid {cid} --sheet-id {args.sheet_id} --copy-file copy_{cid}.json")
        return

    # Step 4: Refresh RSAs
    print("\n[5/5] Generating refreshed RSAs...")

    copy_file = args.copy_file or args.headlines_file
    if copy_file:
        if args.headlines_file and not args.copy_file:
            print(f"[DEPRECATION] --headlines-file is deprecated, use --copy-file instead")
        print(f"[CLAUDE CODE MODE] Loading copy from: {copy_file}")
        with open(copy_file, 'r', encoding='utf-8') as f:
            claude_copy = json.load(f)
        if 'headlines' in claude_copy and isinstance(claude_copy['headlines'], dict):
            claude_headlines = claude_copy['headlines']
            claude_descriptions = claude_copy.get('descriptions', None)
        else:
            # Legacy format: flat dict of ad_id -> headlines
            claude_headlines = claude_copy
            claude_descriptions = None
        if claude_descriptions:
            print(f"  Headlines: {len(claude_headlines)} ad groups")
            print(f"  Descriptions: {len(claude_descriptions)} account-wide")
        else:
            print(f"  Headlines: {len(claude_headlines)} ad groups")
            print(f"  Descriptions: not provided (will copy originals)")
        refreshed_ads = refresh_rsas_with_claude_copy(ads, features, claude_headlines, claude_descriptions)
    else:
        raise ValueError(
            "Direct automated mode is not supported. "
            "Use the Claude Code handoff workflow:\n"
            "  Stage 1: --prepare-for-claude  (outputs context JSON)\n"
            "  Stage 2: Claude Code generates copy → saves to copy_{cid}.json\n"
            "  Stage 3: --copy-file copy_{cid}.json  (writes to sheet)\n\n"
            "All ad copy must be generated by Claude Code for quality and compliance."
        )

    skipped_ads = {ad_id: ad for ad_id, ad in refreshed_ads.items() if ad.get('_skipped')}
    if skipped_ads:
        print(f"\n[SKIP] {len(skipped_ads)} ad group(s) below minimum 10 headlines - excluded from output:")
        for ad_id, ad in skipped_ads.items():
            print(f"  - {ad['ad_group_name']}: {ad.get('_skip_reason', 'unknown')}")

    total_customizers = 0
    total_features = 0
    total_desc_customizers = 0
    total_desc_generated = 0
    has_errors = False
    for ad in refreshed_ads.values():
        if ad.get('_skipped'):
            continue
        for h in ad.get('headlines', []):
            if h.get('status') == 'KEPT (customizer)':
                total_customizers += 1
            elif h.get('status') == 'FEATURE':
                total_features += 1
            elif h.get('status') == 'ERROR':
                has_errors = True
        for d in ad.get('descriptions', []):
            desc_text = d['text'] if isinstance(d, dict) else d
            if is_customizer(desc_text):
                total_desc_customizers += 1
            else:
                total_desc_generated += 1

    print(f"\nRefresh Summary:")
    if has_errors:
        print(f"  ERROR: Scrape failed - error rows generated")
    else:
        print(f"  Customizers preserved: {total_customizers} headlines, {total_desc_customizers} descriptions")
        print(f"  Feature headlines applied: {total_features}")
        print(f"  Generated descriptions applied: {total_desc_generated}")
        print(f"  Total RSAs: {len(refreshed_ads) - len(skipped_ads)}{f' ({len(skipped_ads)} skipped)' if skipped_ads else ''}")
        print(f"  Cross-ad-group consistency: YES (features + descriptions identical across all ads)")

    # Geographic validation (optional; requires COMPLIANCE module)
    validation_reports = {}
    validation_blocked = False

    if COMPLIANCE_AVAILABLE and not args.skip_validation:
        print("\n[VALIDATION] Running geographic validation...")

        property_locations = load_property_locations()
        total_errors = 0
        total_warnings = 0

        for ad_id, ad in refreshed_ads.items():
            if ad.get('_skipped'):
                continue
            headlines = [h['text'] for h in ad['headlines']]

            report = validate_ad_copy(
                headlines=headlines,
                cid=cid,
                property_name=account_name,
                property_locations=property_locations
            )

            validation_reports[ad_id] = report
            total_errors += report.errors
            total_warnings += report.warnings

            ad['validation_status'] = 'VALID' if report.is_valid else f'{report.errors} ERRORS'
            ad['validation_errors'] = [
                f"{r.headline}: {r.message}"
                for r in report.results
                if r.severity == ValidationSeverity.ERROR
            ]

            if report.errors > 0:
                print(f"  [ERROR] Ad {ad_id} ({ad['ad_group_name']}): {report.errors} geographic errors")
                for err in ad['validation_errors']:
                    print(f"    - {err[:70]}...")

        print(f"\nValidation Summary:")
        print(f"  Total errors: {total_errors}")
        print(f"  Total warnings: {total_warnings}")

        if total_errors > 0 and args.strict:
            print(f"\n[BLOCKED] --strict mode: {total_errors} geographic errors detected")
            print("Fix headlines or run without --strict to flag only")
            validation_blocked = True
    elif args.skip_validation:
        print("\n[VALIDATION] Skipped (--skip-validation flag)")
        for ad_id, ad in refreshed_ads.items():
            ad['validation_status'] = 'SKIPPED'
            ad['validation_errors'] = []
    else:
        print("\n[VALIDATION] Skipped (compliance module not available)")
        for ad_id, ad in refreshed_ads.items():
            ad['validation_status'] = 'N/A'
            ad['validation_errors'] = []

    # Step 5: Write to sheet
    if validation_blocked:
        print("\n[BLOCKED] Output not written due to geographic validation errors")
        print("Run without --strict to output with flagged errors, or fix the headlines")
        return

    if args.dry_run:
        print("\n[DRY RUN] Skipping sheet write")
        print("\nSample refreshed RSA:")
        sample = list(refreshed_ads.values())[0]
        print(f"  Campaign: {sample['campaign_name']}")
        print(f"  Ad Group: {sample['ad_group_name']}")
        print(f"  Validation: {sample.get('validation_status', 'N/A')}")
        print(f"  Headlines ({len(sample['headlines'])}):")
        for h in sample['headlines'][:5]:
            print(f"    - [{h['status']}] {h['text']}")
        print(f"  Changes: {sample.get('changes', ['None'])}")
        if sample.get('validation_errors'):
            print(f"  Validation Errors:")
            for err in sample['validation_errors']:
                print(f"    - {err}")
    else:
        print("\nWriting to Google Sheet...")
        sheet_url = write_to_sheet(
            ads, refreshed_ads, args.sheet_id, cid,
            clear=args.clear,
            sheets_token_path=args.sheets_token,
            ads_config_path=args.config,
        )
        print(f"\nDone! Sheet URL: {sheet_url}")

    print("\n" + "=" * 70)
    print("RSA REFRESH COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
