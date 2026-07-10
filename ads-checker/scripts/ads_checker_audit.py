#!/usr/bin/env python3
"""Ads Checker Audit — creative-compliance audit with issue-history intelligence.

Audits Google Ads accounts for creative and compliance issues (10 checks),
compares every run to the account's audit history, detects chronic issues
(3+ occurrences in 90 days), and writes prioritized findings to a Google Sheet.

Read-only on Google Ads: the script never mutates accounts. Its only writes
are to the audit Google Sheet you point it at (``--sheet-id``) and, optionally,
per-account markdown files created after an interactive prompt.

The 10 checks:
    1. DKI Detection — Dynamic Keyword Insertion in copy/assets (trademark risk)
    2. Google AI Assets — AUTOMATICALLY_CREATED assets present
    3. URL Validation — broken/invalid destination URLs (parallel HEAD checks)
    4. Ad Disapprovals — policy violations on ENABLED ads
    5. Seasonal Promotions — outdated seasonal content
    6. Final URL Expansion — enabled without approval
    7. Auto-Applied Recommendations — Google auto-applying changes
    8. Inappropriate Content — profane, discriminatory, or problematic language
    9. Spelling/Grammar — misspelled words in ad copy
    10. Irrelevance — wrong URLs, missing brand names, template placeholders

    (An 11th function reports the auto-created-assets *setting* state —
    TEXT_ASSET_AUTOMATION currently OPTED_IN — alongside the 10 issue checks.
    "10 checks" is the user-facing framing.)

Intelligence features (every non --dry-run run):
    - Issue history comparison — tags each issue type NEW / INCREASED /
      DECREASED / RESOLVED / SAME vs the account's previous audit
    - Account History tab — per-account issue tracking over time
    - Chronic issue detection — 3+ occurrences in 90 days triggers a manual
      review prompt (pipe "no" to stdin for non-interactive runs)
    - Account file management — optionally creates/updates
      accounts/[portfolio]/[account].md with a chronic-issues table

Output: Google Sheet (one row per account)
Tabs: Raw Output, an optional per-portfolio tab, History (aggregate),
      Account History (per-account — the daily-briefing cache)

CACHED-OUTPUT CONTRACT: the companion reader (read_latest_ads_checker.py)
reads the Account History tab and depends on its tab name, the 'Audit Date'
format (%Y-%m-%d %H:%M), and the column headers written here. Never change
one script without the other, or the briefing feed silently goes blank.

Usage:
    # Single account (pipe "no" so the chronic-issue prompt never blocks)
    echo "no" | python ads_checker_audit.py --cid 1234567890 --sheet-id YOUR_SHEET_ID

    # Several accounts
    echo "no" | python ads_checker_audit.py --cids 1234567890,0987654321 --sheet-id YOUR_SHEET_ID

    # A portfolio segment defined in your accounts.json registry
    echo "no" | python ads_checker_audit.py --portfolio north --sheet-id YOUR_SHEET_ID

    # Every account (registry if present, otherwise walks your MCC)
    echo "no" | python ads_checker_audit.py --all --sheet-id YOUR_SHEET_ID

    # Dry run (no sheet write, no comparison, no prompt)
    python ads_checker_audit.py --portfolio north --dry-run

accounts.json format (default ./accounts.json, override with --accounts):
    {
      "accounts": {
        "riverside-flats": {
          "id": "1234567890",
          "name": "Riverside Flats",
          "portfolio": "north"
        },
        "cedar-point-lofts": {
          "id": "0987654321",
          "name": "Cedar Point Lofts",
          "portfolio": "south"
        }
      }
    }
    - "portfolio" is any grouping label you choose; accounts without one
      land in the "default" portfolio. --portfolio all selects everything.
    - Registry names may follow a "Parent Brand - Property Name" convention;
      the part after " - " is treated as the brand for spell-check
      exceptions and the brand-presence check.

Prerequisites:
    - google-ads.yaml at project root (see the google-ads-api-setup skill),
      with login_customer_id set to your MCC for --all runs without a registry
    - pip install google-ads gspread google-auth pyyaml requests pyspellchecker
"""

import argparse
import json
import re
import sys
import io
import time
import requests
import os
from datetime import datetime
from collections import Counter
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
import gspread
from google.oauth2.credentials import Credentials
import yaml
from spellchecker import SpellChecker

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Constants — tab names are part of the cached-output contract with the
# companion reader. Do not rename without updating read_latest_ads_checker.py.
TAB_NAME = "Raw Output"
HISTORY_TAB_NAME = "History"
ACCOUNT_HISTORY_TAB_NAME = "Account History"

# Directory where chronic-issue account files are created (relative to CWD)
ACCOUNTS_FILES_DIR = os.path.join('.', 'accounts')

# Seasonal keywords to detect outdated promotions
SEASONAL_KEYWORDS = [
    # Holidays
    "black friday", "cyber monday", "memorial day", "labor day",
    "presidents day", "veterans day", "independence day", "4th of july",
    "thanksgiving", "christmas", "new year", "easter", "halloween",
    "valentine", "mother's day", "father's day",
    # Seasons
    "spring sale", "spring special", "spring savings",
    "summer sale", "summer special", "summer savings",
    "fall sale", "fall special", "fall savings",
    "winter sale", "winter special", "winter savings",
    # Generic seasonal
    "holiday sale", "holiday special", "holiday savings",
    "end of year", "year-end", "limited time", "this weekend only",
    # Months (risky if specific)
    "january special", "february special", "march special",
    "april special", "may special", "june special",
    "july special", "august special", "september special",
    "october special", "november special", "december special",
]

# DKI pattern (matches {keyword:default}, {KeyWord:default}, etc.)
DKI_PATTERN = re.compile(r'\{(keyword|KeyWord|KEYWORD|Keyword):[^}]*\}', re.IGNORECASE)

# Inappropriate content blocklist
# Categories: profanity, violence, adult content, discriminatory, legally problematic
# This is a STARTER list — extend it for your vertical and market. The
# discriminatory/scam/competitor sections below carry housing-vertical
# examples (Fair Housing Act compliance is a common requirement for housing
# advertisers); swap them for the phrases that matter in your vertical.
INAPPROPRIATE_CONTENT_BLOCKLIST = [
    # Profanity (common misspellings and variations)
    "fuck", "fck", "f*ck", "sh*t", "shit", "damn", "ass", "bitch", "bastard",
    "crap", "piss", "whore", "slut", "dick", "cock", "pussy",
    # Violence
    "kill", "murder", "death", "violent", "weapon", "gun", "shoot",
    "attack", "assault", "bomb", "terror", "dead",
    # Adult/Sexual content
    "xxx", "porn", "sex", "nude", "naked", "erotic", "adult content",
    "hookup", "escort", "stripper",
    # Discriminatory terms (race, religion, orientation)
    "racist", "sexist", "homophobic", "bigot", "hate crime",
    # Legally problematic phrasing — HOUSING EXAMPLE SET (Fair Housing Act);
    # adapt to your vertical's compliance regime
    "no kids", "adults only", "no children", "no families",
    "christians only", "muslim free", "whites only", "no blacks",
    "no hispanics", "no immigrants", "english speakers only",
    "no section 8", "no vouchers", "no welfare",
    # Scam/misleading indicators — housing/rental examples; adapt phrasing
    "guaranteed approval", "no credit check", "free rent forever",
    "100% approved", "no deposit ever", "instant approval guaranteed",
    # Competitor/aggregator mentions — housing-vertical EXAMPLES (listing
    # aggregators that shouldn't appear in an advertiser's own ads);
    # replace with your vertical's competitor names/domains
    "apartments.com", "zillow", "trulia", "rent.com", "apartmentlist",
    # Spam indicators
    "click here now", "act now", "limited spots", "only 1 left",
    "call immediately", "urgent", "don't miss out",
]

# Compile patterns for word boundary matching (avoid false positives)
# Use word boundaries to avoid matching "class" in "classic" etc.
INAPPROPRIATE_PATTERNS = [
    re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
    for word in INAPPROPRIATE_CONTENT_BLOCKLIST
]

# =============================================================================
# SPELLING CHECKER CONFIGURATION
# =============================================================================

# Common ad copy terms that aren't in standard dictionaries.
# This is a STARTER list — extend it for your vertical. The real-estate block
# is an example vertical set; account/brand names are added automatically at
# runtime from your registry (see build_brand_exceptions_from_accounts).
AD_COPY_EXCEPTIONS = [
    # Common abbreviations
    "br", "bd", "ba", "sq", "ft", "sqft", "apt", "apts", "bdrm", "bdrms",
    "mo", "wk", "yr", "hrs", "mins", "w", "d", "brs", "lbs",
    # Real estate / housing terms (example vertical set)
    "floorplan", "floorplans", "townhome", "townhomes", "condo", "condos",
    "walkable", "bikeable", "livable", "rentable", "leasable",
    "pre-lease", "prelease", "pre-leasing", "preleasing",
    "movein", "move-in", "moveins", "move-ins",
    "countertops", "stovetop",
    # Amenities
    "wifi", "ev", "hvac", "ac", "a/c", "washer/dryer", "w/d",
    "clubhouse", "poolside", "rooftop", "courtyard", "dogpark",
    "coworking", "co-working", "gameroom", "fitnesscenter", "carshare",
    # Location terms
    "midtown", "downtown", "uptown", "waterfront", "lakefront",
    "beachfront", "oceanfront", "parkside",
    # Marketing terms
    "luxury", "luxe", "upscale", "boutique", "lifestyle",
    "specials", "incentives", "waived", "discounted",
    # Common metro abbreviations
    "nyc", "atx", "dfw", "la", "sf", "dc", "chi",
    # Other common ad terms
    "onsite", "on-site", "offsite", "pet-friendly", "petfriendly",
    "smokefree", "smoke-free", "contactless", "touchless",
    "virtual", "self-guided", "selfguided", "online",
    "facetime", "zoom", "instagram", "facebook",
    "faqs", "sitemap", "app", "ios", "android",
    # Common marketing words not in dictionary
    "reimagining", "immersive", "instagrammable", "multi", "wfh",
    # Additional common abbreviations
    "addtl", "cds", "dvds", "tvs",
    # Contraction fragments that get flagged incorrectly
    "doesn", "isn", "wasn", "hasn", "couldn", "wouldn", "shouldn",
]

# =============================================================================
# IRRELEVANCE DETECTION CONFIGURATION
# =============================================================================

# Template/placeholder patterns that indicate unfilled content
TEMPLATE_PATTERNS = [
    re.compile(r'\[.*?\]'),  # [Property Name], [City], etc.
    # Match {keyword}, {city}, etc. BUT exclude:
    #   - {CUSTOMIZER.*} (valid ad customizers)
    #   - {KeyWord:*} (valid DKI, caught by DKI check)
    re.compile(r'\{(?!CUSTOMIZER\.)(?!keyword:)(?!KeyWord:)(?!KEYWORD:)[^}]*\}', re.IGNORECASE),
    re.compile(r'<.*?>'),  # <insert here>
    re.compile(r'XXXX+', re.IGNORECASE),  # XXXX placeholders
    re.compile(r'TODO', re.IGNORECASE),  # TODO markers
    re.compile(r'INSERT\s+HERE', re.IGNORECASE),
    re.compile(r'YOUR\s+(PROPERTY|BRAND|NAME|COMPANY)', re.IGNORECASE),
    re.compile(r'PLACEHOLDER', re.IGNORECASE),
    re.compile(r'LOREM\s+IPSUM', re.IGNORECASE),
]

# Domains to ignore (tracking, analytics, etc.)
IGNORED_DOMAINS = [
    'google.com', 'googleadservices.com', 'doubleclick.net',
    'facebook.com', 'fb.com', 'instagram.com',
    'bing.com', 'microsoft.com',
    'analytics.google.com', 'tagmanager.google.com',
]


def build_brand_exceptions_from_accounts(accounts: dict) -> set:
    """Extract brand terms from account names to use as spelling exceptions.

    Registry names may follow a "Parent Brand - Property Name" convention;
    the part after the first " - " is treated as the brand.

    Examples:
        "Northgate Group - Riverside Flats" -> {'riverside', 'flats'}
        "Cedar Point Lofts" -> {'cedar', 'point', 'lofts'}
    """
    brand_terms = set()

    for account_name in accounts.values():
        # Drop a "Parent Brand - " prefix if the name carries one
        name = account_name.split(' - ', 1)[1] if ' - ' in account_name else account_name

        # Split on common separators and extract words
        words = re.split(r'[\s\-_/&]+', name)

        for word in words:
            # Clean the word
            clean_word = re.sub(r'[^a-zA-Z0-9]', '', word).lower()
            if clean_word and len(clean_word) >= 2:
                brand_terms.add(clean_word)

    return brand_terms


# =============================================================================
# ACCOUNT REGISTRY
# =============================================================================

# cid -> {'name': str, 'portfolio': str} — populated in main()
REGISTRY = {}


def load_accounts_registry(accounts_path: str) -> dict:
    """Load account mappings from an accounts.json registry.

    Returns {cid: {'name': str, 'portfolio': str}}; {} if the file is absent.
    Accounts without a "portfolio" field land in the "default" portfolio.
    """
    if not os.path.exists(accounts_path):
        return {}

    with open(accounts_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    registry = {}
    for entry in data.get('accounts', {}).values():
        cid = str(entry['id']).replace('-', '')
        registry[cid] = {
            'name': entry.get('name', f"Account {cid}"),
            'portfolio': entry.get('portfolio', 'default'),
        }
    return registry


def get_accounts_for_portfolio(portfolio: str) -> dict:
    """Return {cid: name} for the specified registry portfolio ('all' = everything)."""
    if portfolio == 'all':
        return {cid: entry['name'] for cid, entry in REGISTRY.items()}

    accounts = {
        cid: entry['name']
        for cid, entry in REGISTRY.items()
        if entry['portfolio'] == portfolio
    }
    if not accounts:
        available = sorted({entry['portfolio'] for entry in REGISTRY.values()})
        raise ValueError(
            f"Unknown portfolio: {portfolio!r}. "
            f"Portfolios in your registry: {available or '(registry empty)'}"
        )
    return accounts


def get_portfolio_name(cid: str) -> str:
    """Determine which portfolio an account belongs to (registry lookup)."""
    entry = REGISTRY.get(cid)
    return entry['portfolio'] if entry else 'unknown'


def get_login_customer_id(config_path: str) -> str:
    """Read login_customer_id (the MCC) from google-ads.yaml, if present."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        value = data.get('login_customer_id', '')
        return str(value).replace('-', '') if value else ''
    except Exception:
        return ''


def get_mcc_accounts(ads_client: GoogleAdsClient, login_customer_id: str) -> list:
    """Walk the MCC's customer_client resource to get all active accounts.

    Returns list of (cid_without_dashes, descriptive_name) tuples.
    """
    query = """
        SELECT
            customer_client.id,
            customer_client.descriptive_name
        FROM customer_client
        WHERE customer_client.status = 'ENABLED'
          AND customer_client.manager = FALSE
    """
    service = ads_client.get_service("GoogleAdsService")
    accounts = []
    response = service.search(customer_id=login_customer_id, query=query)
    for row in response:
        accounts.append((str(row.customer_client.id), row.customer_client.descriptive_name))
    return accounts


# Google Ads service handle — initialized in main() from --config
ga_service = None


def get_sheets_client(config_path: str):
    """Get authenticated Google Sheets client (OAuth reused from google-ads.yaml)."""
    with open(config_path, "r", encoding="utf-8") as f:
        ads_config = yaml.safe_load(f.read())

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


# =============================================================================
# AUDIT FUNCTIONS
# =============================================================================

def check_dki(cid: str) -> dict:
    """Check for Dynamic Keyword Insertion in ad copy and assets."""
    findings = []

    # Query RSA headlines and descriptions (only active campaigns/ad groups/ads)
    query = """
        SELECT
            ad_group_ad.ad.id,
            ad_group_ad.ad.responsive_search_ad.headlines,
            ad_group_ad.ad.responsive_search_ad.descriptions,
            campaign.name,
            ad_group.name
        FROM ad_group_ad
        WHERE campaign.status = 'ENABLED'
          AND ad_group.status = 'ENABLED'
          AND ad_group_ad.status = 'ENABLED'
          AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'
    """

    try:
        response = ga_service.search(customer_id=cid, query=query)
        for row in response:
            ad = row.ad_group_ad.ad

            # Check headlines
            for headline in ad.responsive_search_ad.headlines:
                if DKI_PATTERN.search(headline.text):
                    findings.append({
                        'type': 'Headline',
                        'text': headline.text,
                        'campaign': row.campaign.name,
                        'ad_group': row.ad_group.name
                    })

            # Check descriptions
            for desc in ad.responsive_search_ad.descriptions:
                if DKI_PATTERN.search(desc.text):
                    findings.append({
                        'type': 'Description',
                        'text': desc.text,
                        'campaign': row.campaign.name,
                        'ad_group': row.ad_group.name
                    })
    except GoogleAdsException:
        pass

    # Also check sitelinks and callouts
    asset_query = """
        SELECT
            asset.id,
            asset.type,
            asset.text_asset.text,
            asset.sitelink_asset.link_text,
            asset.sitelink_asset.description1,
            asset.sitelink_asset.description2,
            asset.callout_asset.callout_text
        FROM asset
        WHERE asset.type IN ('TEXT', 'SITELINK', 'CALLOUT')
    """

    try:
        response = ga_service.search(customer_id=cid, query=asset_query)
        for row in response:
            asset = row.asset
            texts_to_check = [
                asset.text_asset.text,
                asset.sitelink_asset.link_text,
                asset.sitelink_asset.description1,
                asset.sitelink_asset.description2,
                asset.callout_asset.callout_text
            ]
            for text in texts_to_check:
                if text and DKI_PATTERN.search(text):
                    findings.append({
                        'type': f'Asset ({asset.type.name})',
                        'text': text,
                        'campaign': 'Account-level',
                        'ad_group': ''
                    })
    except GoogleAdsException:
        pass

    return {
        'count': len(findings),
        'details': findings[:5],  # Limit details to first 5
        'severity': 'HIGH' if findings else 'OK'
    }


def check_google_ai_assets(cid: str) -> dict:
    """Check for automatically created (Google AI) assets."""
    findings = []

    # Direct asset query
    query = """
        SELECT
            asset.id,
            asset.type,
            asset.source,
            asset.text_asset.text,
            asset.sitelink_asset.link_text,
            asset.callout_asset.callout_text
        FROM asset
        WHERE asset.source = 'AUTOMATICALLY_CREATED'
    """

    try:
        response = ga_service.search(customer_id=cid, query=query)
        for row in response:
            asset = row.asset
            text = (asset.text_asset.text or
                    asset.sitelink_asset.link_text or
                    asset.callout_asset.callout_text or
                    f"[{asset.type.name}]")
            findings.append({
                'type': asset.type.name,
                'text': text[:50],
                'source': 'Account'
            })
    except GoogleAdsException:
        pass

    # RSA auto-created assets via ad_group_ad_asset_view
    rsa_query = """
        SELECT
            asset.id,
            asset.type,
            asset.text_asset.text,
            ad_group_ad_asset_view.field_type,
            campaign.name
        FROM ad_group_ad_asset_view
        WHERE ad_group_ad_asset_view.source = 'AUTOMATICALLY_CREATED'
    """

    try:
        response = ga_service.search(customer_id=cid, query=rsa_query)
        for row in response:
            findings.append({
                'type': row.ad_group_ad_asset_view.field_type.name if row.ad_group_ad_asset_view.field_type else row.asset.type.name,
                'text': (row.asset.text_asset.text or '')[:50],
                'source': row.campaign.name
            })
    except GoogleAdsException:
        pass

    # Deduplicate by asset ID (tracked via text for simplicity)
    seen = set()
    unique_findings = []
    for f in findings:
        key = f"{f['type']}:{f['text']}"
        if key not in seen:
            seen.add(key)
            unique_findings.append(f)

    return {
        'count': len(unique_findings),
        'details': unique_findings[:5],
        'severity': 'MEDIUM' if unique_findings else 'OK'
    }


def check_url_validation(cid: str) -> dict:
    """Check for broken or invalid destination URLs.

    Checks two sources:
    1. Ad URLs - Only from ENABLED campaigns/ad groups/ads
    2. Sitelink URLs - All account-level sitelinks (even unused), except REMOVED
    """
    findings = []
    urls_checked = set()

    # Get final URLs from ads (only in active campaigns/ad groups)
    query = """
        SELECT
            ad_group_ad.ad.id,
            ad_group_ad.ad.final_urls,
            campaign.name,
            campaign.status,
            ad_group.name,
            ad_group.status
        FROM ad_group_ad
        WHERE ad_group_ad.status = 'ENABLED'
          AND campaign.status = 'ENABLED'
          AND ad_group.status = 'ENABLED'
    """

    try:
        response = ga_service.search(customer_id=cid, query=query)
        for row in response:
            for url in row.ad_group_ad.ad.final_urls:
                if url and url not in urls_checked:
                    urls_checked.add(url)
    except GoogleAdsException:
        pass

    # Get final URLs from sitelinks (all non-removed sitelinks, even unused)
    sitelink_query = """
        SELECT
            asset.id,
            asset.final_urls
        FROM asset
        WHERE asset.type = 'SITELINK'
    """

    try:
        response = ga_service.search(customer_id=cid, query=sitelink_query)
        for row in response:
            for url in row.asset.final_urls:
                if url and url not in urls_checked:
                    urls_checked.add(url)
    except GoogleAdsException:
        pass

    # Check URLs (limit to first 20 to avoid timeout)
    urls_to_check = list(urls_checked)[:20]

    def check_url(url):
        try:
            resp = requests.head(url, timeout=5, allow_redirects=True)
            if resp.status_code >= 400:
                return {'url': url, 'status': resp.status_code, 'error': 'HTTP Error'}
        except requests.exceptions.Timeout:
            return {'url': url, 'status': 0, 'error': 'Timeout'}
        except requests.exceptions.ConnectionError:
            return {'url': url, 'status': 0, 'error': 'Connection Error'}
        except Exception as e:
            return {'url': url, 'status': 0, 'error': str(e)[:30]}
        return None

    # Parallel URL checking
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(check_url, url): url for url in urls_to_check}
        for future in as_completed(futures):
            result = future.result()
            if result:
                findings.append(result)

    return {
        'count': len(findings),
        'urls_checked': len(urls_to_check),
        'details': findings[:5],
        'severity': 'CRITICAL' if findings else 'OK'
    }


def check_ad_disapprovals(cid: str) -> dict:
    """Check for disapproved ads in active campaigns/ad groups only.

    Only flags disapprovals in ads that are:
    - Ad status = ENABLED
    - Ad group status = ENABLED
    - Campaign status = ENABLED

    This excludes archived/paused campaigns with old disapprovals.
    """
    findings = []

    # Query all ads and filter in Python (API doesn't support all enum values in WHERE)
    query = """
        SELECT
            ad_group_ad.ad.id,
            ad_group_ad.policy_summary.approval_status,
            ad_group_ad.policy_summary.policy_topic_entries,
            campaign.name,
            campaign.status,
            ad_group.name,
            ad_group.status
        FROM ad_group_ad
        WHERE ad_group_ad.status = 'ENABLED'
          AND campaign.status = 'ENABLED'
          AND ad_group.status = 'ENABLED'
    """

    try:
        response = ga_service.search(customer_id=cid, query=query)
        for row in response:
            policy = row.ad_group_ad.policy_summary
            status = policy.approval_status.name if policy.approval_status else 'UNKNOWN'

            # Only include non-approved statuses
            if status not in ('APPROVED', 'APPROVED_LIMITED', 'UNKNOWN'):
                topics = [entry.topic for entry in policy.policy_topic_entries] if policy.policy_topic_entries else []
                findings.append({
                    'ad_id': row.ad_group_ad.ad.id,
                    'status': status,
                    'topics': ', '.join(topics)[:50],
                    'campaign': row.campaign.name,
                    'ad_group': row.ad_group.name
                })
    except GoogleAdsException:
        pass

    # Count by severity
    disapproved = [f for f in findings if f['status'] == 'DISAPPROVED']
    limited = [f for f in findings if f['status'] in ('LIMITED', 'AREA_OF_INTEREST_ONLY', 'APPROVED_LIMITED')]

    severity = 'OK'
    if disapproved:
        severity = 'CRITICAL'
    elif limited:
        severity = 'MEDIUM'

    return {
        'count': len(findings),
        'disapproved': len(disapproved),
        'limited': len(limited),
        'details': findings[:5],
        'severity': severity
    }


def check_seasonal_promotions(cid: str) -> dict:
    """Check for outdated seasonal promotions in ad copy."""
    findings = []

    # Query RSA headlines and descriptions
    query = """
        SELECT
            ad_group_ad.ad.id,
            ad_group_ad.ad.responsive_search_ad.headlines,
            ad_group_ad.ad.responsive_search_ad.descriptions,
            campaign.name,
            ad_group.name
        FROM ad_group_ad
        WHERE ad_group_ad.status = 'ENABLED'
          AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'
    """

    try:
        response = ga_service.search(customer_id=cid, query=query)
        for row in response:
            ad = row.ad_group_ad.ad

            # Check headlines
            for headline in ad.responsive_search_ad.headlines:
                text_lower = headline.text.lower()
                for keyword in SEASONAL_KEYWORDS:
                    if keyword in text_lower:
                        findings.append({
                            'type': 'Headline',
                            'text': headline.text,
                            'keyword': keyword,
                            'campaign': row.campaign.name
                        })
                        break

            # Check descriptions
            for desc in ad.responsive_search_ad.descriptions:
                text_lower = desc.text.lower()
                for keyword in SEASONAL_KEYWORDS:
                    if keyword in text_lower:
                        findings.append({
                            'type': 'Description',
                            'text': desc.text,
                            'keyword': keyword,
                            'campaign': row.campaign.name
                        })
                        break
    except GoogleAdsException:
        pass

    # Also check callouts and sitelinks
    asset_query = """
        SELECT
            asset.id,
            asset.type,
            asset.sitelink_asset.link_text,
            asset.callout_asset.callout_text
        FROM asset
        WHERE asset.type IN ('SITELINK', 'CALLOUT')
    """

    try:
        response = ga_service.search(customer_id=cid, query=asset_query)
        for row in response:
            asset = row.asset
            text = asset.sitelink_asset.link_text or asset.callout_asset.callout_text or ''
            text_lower = text.lower()
            for keyword in SEASONAL_KEYWORDS:
                if keyword in text_lower:
                    findings.append({
                        'type': f'Asset ({asset.type.name})',
                        'text': text,
                        'keyword': keyword,
                        'campaign': 'Account-level'
                    })
                    break
    except GoogleAdsException:
        pass

    return {
        'count': len(findings),
        'details': findings[:5],
        'severity': 'HIGH' if findings else 'OK'
    }


def check_auto_created_assets_setting(cid: str) -> dict:
    """Check if Automatically Created Assets setting is currently ENABLED on campaigns.

    This checks the actual setting state, not just whether AI assets exist.
    Looks for TEXT_ASSET_AUTOMATION being OPTED_IN.
    """
    enabled_campaigns = []
    disabled_campaigns = []
    total_campaigns = 0

    query = """
        SELECT
            campaign.id,
            campaign.name,
            campaign.advertising_channel_type,
            campaign.asset_automation_settings
        FROM campaign
        WHERE campaign.status = 'ENABLED'
    """

    try:
        response = ga_service.search(customer_id=cid, query=query)
        for row in response:
            campaign = row.campaign
            total_campaigns += 1

            # Check for TEXT_ASSET_AUTOMATION setting
            text_automation_status = None
            for setting in campaign.asset_automation_settings:
                if setting.asset_automation_type.name == 'TEXT_ASSET_AUTOMATION':
                    text_automation_status = setting.asset_automation_status.name
                    break

            if text_automation_status == 'OPTED_IN':
                enabled_campaigns.append({
                    'campaign': campaign.name,
                    'type': campaign.advertising_channel_type.name,
                    'status': 'ENABLED'
                })
            elif text_automation_status == 'OPTED_OUT':
                disabled_campaigns.append({
                    'campaign': campaign.name,
                    'type': campaign.advertising_channel_type.name,
                    'status': 'DISABLED'
                })
            # If not explicitly set, Google defaults vary by campaign type
    except GoogleAdsException:
        pass

    return {
        'enabled_count': len(enabled_campaigns),
        'disabled_count': len(disabled_campaigns),
        'total_campaigns': total_campaigns,
        'details': enabled_campaigns[:5],
        'severity': 'HIGH' if enabled_campaigns else 'OK'
    }


def check_final_url_expansion(cid: str) -> dict:
    """Check for Final URL Expansion enabled on campaigns.

    Checks asset_automation_settings for FINAL_URL_EXPANSION_TEXT_ASSET_AUTOMATION
    being OPTED_IN, which means Google can expand to different URLs.
    """
    findings = []

    query = """
        SELECT
            campaign.id,
            campaign.name,
            campaign.advertising_channel_type,
            campaign.asset_automation_settings
        FROM campaign
        WHERE campaign.status = 'ENABLED'
    """

    try:
        response = ga_service.search(customer_id=cid, query=query)
        for row in response:
            campaign = row.campaign
            for setting in campaign.asset_automation_settings:
                # Check specifically for Final URL Expansion
                if (setting.asset_automation_type.name == 'FINAL_URL_EXPANSION_TEXT_ASSET_AUTOMATION'
                        and setting.asset_automation_status.name == 'OPTED_IN'):
                    findings.append({
                        'campaign': campaign.name,
                        'type': campaign.advertising_channel_type.name,
                        'setting': 'FINAL_URL_EXPANSION'
                    })
    except GoogleAdsException:
        pass

    return {
        'count': len(findings),
        'details': findings[:5],
        'severity': 'MEDIUM' if findings else 'OK'
    }


# Approved/safe auto-apply recommendation types (whitelist - don't flag these)
APPROVED_RECOMMENDATION_TYPES = [
    'OPTIMIZE_AD_ROTATION',  # Safe optimization setting
]

# High-risk auto-apply recommendation types that can break account strategy
HIGH_RISK_RECOMMENDATION_TYPES = [
    'KEYWORD',
    'RAISE_TARGET_CPA_BID_TOO_LOW',
    'LOWER_TARGET_ROAS',
    'RESPONSIVE_SEARCH_AD',
    'USE_BROAD_MATCH_KEYWORD',
    'RAISE_TARGET_CPA',
    'FORECASTING_SET_TARGET_CPA',
    'FORECASTING_SET_TARGET_ROAS',
]


def check_auto_applied_recommendations(cid: str) -> dict:
    """Check for auto-applied recommendations enabled.

    Ignores approved types (e.g., OPTIMIZE_AD_ROTATION).
    Flags concerning types as MEDIUM (bidding opt-ins, UNKNOWN).
    Flags high-risk types as HIGH (keyword additions, CPA/ROAS changes).
    """
    findings = []

    query = """
        SELECT
            recommendation_subscription.resource_name,
            recommendation_subscription.type,
            recommendation_subscription.status
        FROM recommendation_subscription
    """

    try:
        response = ga_service.search(customer_id=cid, query=query)
        for row in response:
            sub = row.recommendation_subscription
            rec_type = sub.type.name if sub.type else 'UNKNOWN'
            status = sub.status.name if sub.status else 'UNKNOWN'

            # Skip approved types (whitelist)
            if rec_type in APPROVED_RECOMMENDATION_TYPES:
                continue

            # Flag if enabled (especially high-risk types)
            if status == 'ENABLED':
                is_high_risk = rec_type in HIGH_RISK_RECOMMENDATION_TYPES
                findings.append({
                    'type': rec_type,
                    'status': status,
                    'high_risk': is_high_risk
                })
    except GoogleAdsException:
        pass

    # Determine severity based on high-risk types
    high_risk_count = sum(1 for f in findings if f.get('high_risk'))

    if high_risk_count > 0:
        severity = 'HIGH'
    elif findings:
        severity = 'MEDIUM'
    else:
        severity = 'OK'

    return {
        'count': len(findings),
        'high_risk_count': high_risk_count,
        'details': findings[:5],
        'severity': severity
    }


def check_inappropriate_content(cid: str) -> dict:
    """Check for inappropriate, offensive, or problematic content in ad copy.

    Scans all text assets for:
    - Profanity and offensive language
    - Violence-related terms
    - Adult/sexual content
    - Discriminatory language (e.g., Fair Housing violations for housing advertisers)
    - Spam/scam indicators
    - Competitor mentions
    """
    findings = []

    def check_text_for_issues(text: str, location: str, campaign: str = '', ad_group: str = '') -> None:
        """Check a text string against all inappropriate patterns."""
        if not text:
            return
        for i, pattern in enumerate(INAPPROPRIATE_PATTERNS):
            if pattern.search(text):
                matched_term = INAPPROPRIATE_CONTENT_BLOCKLIST[i]
                findings.append({
                    'text': text[:60],
                    'matched_term': matched_term,
                    'location': location,
                    'campaign': campaign,
                    'ad_group': ad_group
                })
                break  # Only report first match per text

    # Query RSA headlines and descriptions
    rsa_query = """
        SELECT
            ad_group_ad.ad.id,
            ad_group_ad.ad.responsive_search_ad.headlines,
            ad_group_ad.ad.responsive_search_ad.descriptions,
            campaign.name,
            ad_group.name
        FROM ad_group_ad
        WHERE ad_group_ad.status = 'ENABLED'
          AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'
    """

    try:
        response = ga_service.search(customer_id=cid, query=rsa_query)
        for row in response:
            ad = row.ad_group_ad.ad
            campaign = row.campaign.name
            ad_group = row.ad_group.name

            # Check headlines
            for headline in ad.responsive_search_ad.headlines:
                check_text_for_issues(headline.text, 'RSA Headline', campaign, ad_group)

            # Check descriptions
            for desc in ad.responsive_search_ad.descriptions:
                check_text_for_issues(desc.text, 'RSA Description', campaign, ad_group)
    except GoogleAdsException:
        pass

    # Check sitelinks, callouts, and other text assets
    asset_query = """
        SELECT
            asset.id,
            asset.type,
            asset.text_asset.text,
            asset.sitelink_asset.link_text,
            asset.sitelink_asset.description1,
            asset.sitelink_asset.description2,
            asset.callout_asset.callout_text,
            asset.structured_snippet_asset.header,
            asset.structured_snippet_asset.values
        FROM asset
        WHERE asset.type IN ('TEXT', 'SITELINK', 'CALLOUT', 'STRUCTURED_SNIPPET')
    """

    try:
        response = ga_service.search(customer_id=cid, query=asset_query)
        for row in response:
            asset = row.asset
            asset_type = asset.type.name

            # Check various asset text fields
            texts_to_check = [
                (asset.text_asset.text, 'Text Asset'),
                (asset.sitelink_asset.link_text, 'Sitelink'),
                (asset.sitelink_asset.description1, 'Sitelink Desc1'),
                (asset.sitelink_asset.description2, 'Sitelink Desc2'),
                (asset.callout_asset.callout_text, 'Callout'),
                (asset.structured_snippet_asset.header, 'Snippet Header'),
            ]

            for text, location in texts_to_check:
                if text:
                    check_text_for_issues(text, location, 'Account-level', '')

            # Check structured snippet values
            for value in asset.structured_snippet_asset.values:
                if value:
                    check_text_for_issues(value, 'Snippet Value', 'Account-level', '')
    except GoogleAdsException:
        pass

    # Determine severity based on category of matched terms
    critical_terms = ['fuck', 'fck', 'f*ck', 'shit', 'sh*t', 'porn', 'xxx', 'nude', 'naked',
                      'no kids', 'adults only', 'no children', 'whites only', 'no blacks',
                      'no hispanics', 'christians only', 'muslim free']
    high_terms = ['damn', 'ass', 'bitch', 'kill', 'murder', 'death', 'gun', 'weapon',
                  'no section 8', 'no vouchers', 'no welfare', 'sex', 'escort']

    severity = 'OK'
    for finding in findings:
        term = finding['matched_term'].lower()
        if term in critical_terms:
            severity = 'CRITICAL'
            break
        elif term in high_terms:
            severity = 'HIGH'

    return {
        'count': len(findings),
        'details': findings[:5],
        'severity': severity
    }


def check_spelling(cid: str, brand_exceptions: set = None) -> dict:
    """Check for spelling errors in ad copy using pyspellchecker.

    Args:
        cid: Customer ID
        brand_exceptions: Set of brand terms to exclude from spell checking

    Returns:
        Dict with count, details, and severity
    """
    findings = []
    brand_exceptions = brand_exceptions or set()

    # Create a local spell checker instance with brand exceptions
    local_spell = SpellChecker(language='en', distance=1)  # distance=1 for performance
    local_spell.word_frequency.load_words(AD_COPY_EXCEPTIONS)
    local_spell.word_frequency.load_words(list(brand_exceptions))

    def extract_words(text: str) -> list:
        """Extract words from text, handling ad copy patterns."""
        if not text:
            return []
        # Remove common ad patterns that aren't words
        text = re.sub(r'\{[^}]+\}', '', text)  # Remove DKI patterns
        text = re.sub(r'https?://\S+', '', text)  # Remove URLs
        text = re.sub(r'\d+', '', text)  # Remove numbers
        # Replace hyphens with spaces to split compound words
        text = text.replace('-', ' ')
        text = re.sub(r'[^\w\s\']', ' ', text)  # Keep letters and apostrophes only
        # Split and filter
        words = text.lower().split()
        # Filter out very short words and words with apostrophes (contractions)
        return [w.strip("'") for w in words if len(w.strip("'")) >= 3 and "'" not in w]

    def check_text_for_spelling(text: str, location: str, campaign: str = '', ad_group: str = '') -> None:
        """Check a text string for spelling errors."""
        if not text:
            return

        words = extract_words(text)
        if not words:
            return

        # Find misspelled words
        misspelled = local_spell.unknown(words)

        for word in misspelled:
            # Skip if it looks like an acronym (all caps in original)
            if word.upper() in text:
                continue
            # Skip if it's a number-letter combo (like "1br", "2bd")
            if any(c.isdigit() for c in word):
                continue
            # Skip very short words that slipped through
            if len(word) < 3:
                continue
            # Skip if word appears capitalized in original (likely proper noun)
            # Check for Title Case (e.g., "Bourdain", "Magnus")
            if word.capitalize() in text:
                continue

            suggestion = local_spell.correction(word)
            findings.append({
                'word': word,
                'suggestion': suggestion if suggestion != word else '(no suggestion)',
                'text': text[:50],
                'location': location,
                'campaign': campaign,
                'ad_group': ad_group
            })

    # Query RSA headlines and descriptions
    rsa_query = """
        SELECT
            ad_group_ad.ad.id,
            ad_group_ad.ad.responsive_search_ad.headlines,
            ad_group_ad.ad.responsive_search_ad.descriptions,
            campaign.name,
            ad_group.name
        FROM ad_group_ad
        WHERE ad_group_ad.status = 'ENABLED'
          AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'
    """

    try:
        response = ga_service.search(customer_id=cid, query=rsa_query)
        for row in response:
            ad = row.ad_group_ad.ad
            campaign = row.campaign.name
            ad_group = row.ad_group.name

            # Check headlines
            for headline in ad.responsive_search_ad.headlines:
                check_text_for_spelling(headline.text, 'RSA Headline', campaign, ad_group)

            # Check descriptions
            for desc in ad.responsive_search_ad.descriptions:
                check_text_for_spelling(desc.text, 'RSA Description', campaign, ad_group)
    except GoogleAdsException:
        pass

    # Check sitelinks and callouts
    asset_query = """
        SELECT
            asset.id,
            asset.type,
            asset.text_asset.text,
            asset.sitelink_asset.link_text,
            asset.sitelink_asset.description1,
            asset.sitelink_asset.description2,
            asset.callout_asset.callout_text
        FROM asset
        WHERE asset.type IN ('TEXT', 'SITELINK', 'CALLOUT')
    """

    try:
        response = ga_service.search(customer_id=cid, query=asset_query)
        for row in response:
            asset = row.asset

            texts_to_check = [
                (asset.text_asset.text, 'Text Asset'),
                (asset.sitelink_asset.link_text, 'Sitelink'),
                (asset.sitelink_asset.description1, 'Sitelink Desc1'),
                (asset.sitelink_asset.description2, 'Sitelink Desc2'),
                (asset.callout_asset.callout_text, 'Callout'),
            ]

            for text, location in texts_to_check:
                if text:
                    check_text_for_spelling(text, location, 'Account-level', '')
    except GoogleAdsException:
        pass

    # Deduplicate findings by word (same misspelling might appear multiple times)
    seen_words = set()
    unique_findings = []
    for finding in findings:
        if finding['word'] not in seen_words:
            seen_words.add(finding['word'])
            unique_findings.append(finding)

    # Determine severity
    # HIGH if 5+ unique misspellings, MEDIUM if 1-4, OK if none
    if len(unique_findings) >= 5:
        severity = 'HIGH'
    elif len(unique_findings) >= 1:
        severity = 'MEDIUM'
    else:
        severity = 'OK'

    return {
        'count': len(unique_findings),
        'details': unique_findings[:5],
        'severity': severity
    }


def check_irrelevance(cid: str, account_name: str) -> dict:
    """Check for irrelevant content: wrong URLs, missing brand names, template placeholders.

    Args:
        cid: Customer ID
        account_name: Account display name (used to extract expected brand terms)

    Returns:
        Dict with findings categorized by type
    """
    findings = []

    # Extract brand terms from account name (dropping any "Parent Brand - " prefix)
    # e.g., "Northgate Group - Riverside Flats" -> ['riverside', 'flats']
    # e.g., "Cedar Point Lofts" -> ['cedar', 'point', 'lofts']
    clean_name = account_name.split(' - ', 1)[1] if ' - ' in account_name else account_name

    brand_terms = set()
    words = re.split(r'[\s\-_/&]+', clean_name)
    for word in words:
        clean_word = re.sub(r'[^a-zA-Z0-9]', '', word).lower()
        # Skip common filler words and short words
        if clean_word and len(clean_word) >= 3 and clean_word not in ['the', 'and', 'apartments', 'at']:
            brand_terms.add(clean_word)

    # ==========================================================================
    # 1. URL Domain Check - Find expected domain and flag mismatches
    # ==========================================================================
    url_domains = Counter()
    all_urls = []

    # Query ad URLs
    url_query = """
        SELECT
            ad_group_ad.ad.final_urls,
            campaign.name
        FROM ad_group_ad
        WHERE ad_group_ad.status = 'ENABLED'
    """

    try:
        response = ga_service.search(customer_id=cid, query=url_query)
        for row in response:
            for url in row.ad_group_ad.ad.final_urls:
                if url:
                    all_urls.append((url, row.campaign.name))
                    try:
                        domain = urlparse(url).netloc.lower()
                        # Remove www. prefix for consistency
                        domain = domain.replace('www.', '')
                        if domain and domain not in IGNORED_DOMAINS:
                            url_domains[domain] += 1
                    except Exception:
                        pass
    except GoogleAdsException:
        pass

    # Query sitelink URLs
    sitelink_query = """
        SELECT
            asset.final_urls
        FROM asset
        WHERE asset.type = 'SITELINK'
    """

    try:
        response = ga_service.search(customer_id=cid, query=sitelink_query)
        for row in response:
            for url in row.asset.final_urls:
                if url:
                    all_urls.append((url, 'Sitelink'))
                    try:
                        domain = urlparse(url).netloc.lower().replace('www.', '')
                        if domain and domain not in IGNORED_DOMAINS:
                            url_domains[domain] += 1
                    except Exception:
                        pass
    except GoogleAdsException:
        pass

    # Determine expected domain (most common)
    expected_domain = None
    mismatched_urls = []
    if url_domains:
        expected_domain = url_domains.most_common(1)[0][0]

        # Find URLs with different domains
        for url, source in all_urls:
            try:
                domain = urlparse(url).netloc.lower().replace('www.', '')
                if domain and domain not in IGNORED_DOMAINS and domain != expected_domain:
                    mismatched_urls.append({
                        'type': 'URL_MISMATCH',
                        'url': url[:60],
                        'expected_domain': expected_domain,
                        'actual_domain': domain,
                        'source': source
                    })
            except Exception:
                pass

    findings.extend(mismatched_urls[:3])  # Limit URL findings

    # ==========================================================================
    # 2. Template/Placeholder Check
    # ==========================================================================
    template_findings = []

    def check_for_templates(text: str, location: str) -> None:
        if not text:
            return
        for pattern in TEMPLATE_PATTERNS:
            match = pattern.search(text)
            if match:
                template_findings.append({
                    'type': 'TEMPLATE',
                    'text': text[:50],
                    'matched': match.group()[:20],
                    'location': location
                })
                return  # Only report one match per text

    # Query ad copy for templates
    rsa_query = """
        SELECT
            ad_group_ad.ad.responsive_search_ad.headlines,
            ad_group_ad.ad.responsive_search_ad.descriptions,
            campaign.name
        FROM ad_group_ad
        WHERE ad_group_ad.status = 'ENABLED'
          AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'
    """

    try:
        response = ga_service.search(customer_id=cid, query=rsa_query)
        for row in response:
            ad = row.ad_group_ad.ad
            for headline in ad.responsive_search_ad.headlines:
                check_for_templates(headline.text, f'RSA Headline ({row.campaign.name})')
            for desc in ad.responsive_search_ad.descriptions:
                check_for_templates(desc.text, f'RSA Description ({row.campaign.name})')
    except GoogleAdsException:
        pass

    findings.extend(template_findings[:3])  # Limit template findings

    # ==========================================================================
    # 3. Brand Name Presence Check (only if we have brand terms to check)
    # ==========================================================================
    brand_missing_findings = []

    if brand_terms and len(brand_terms) <= 5:  # Only check if we have specific brand terms
        # Check if any brand term appears in ad copy
        all_ad_text = []

        try:
            response = ga_service.search(customer_id=cid, query=rsa_query)
            for row in response:
                ad = row.ad_group_ad.ad
                for headline in ad.responsive_search_ad.headlines:
                    if headline.text:
                        all_ad_text.append(headline.text.lower())
                for desc in ad.responsive_search_ad.descriptions:
                    if desc.text:
                        all_ad_text.append(desc.text.lower())
        except GoogleAdsException:
            pass

        # Check which brand terms are missing from ALL ad copy
        combined_text = ' '.join(all_ad_text)
        missing_terms = []
        for term in brand_terms:
            if term not in combined_text:
                missing_terms.append(term)

        # Only flag if ALL brand terms are missing (suggests wrong account copy)
        if missing_terms and len(missing_terms) == len(brand_terms) and all_ad_text:
            brand_missing_findings.append({
                'type': 'BRAND_MISSING',
                'missing_terms': ', '.join(list(brand_terms)[:3]),
                'sample_text': all_ad_text[0][:40] if all_ad_text else '',
                'location': 'All RSA copy'
            })

    findings.extend(brand_missing_findings)

    # ==========================================================================
    # Determine severity
    # ==========================================================================
    url_mismatch_count = len([f for f in findings if f['type'] == 'URL_MISMATCH'])
    template_count = len([f for f in findings if f['type'] == 'TEMPLATE'])
    brand_missing_count = len([f for f in findings if f['type'] == 'BRAND_MISSING'])

    if template_count > 0 or brand_missing_count > 0:
        severity = 'HIGH'  # Templates and missing brand are serious
    elif url_mismatch_count > 2:
        severity = 'HIGH'
    elif url_mismatch_count > 0:
        severity = 'MEDIUM'
    else:
        severity = 'OK'

    return {
        'count': len(findings),
        'url_mismatches': url_mismatch_count,
        'templates': template_count,
        'brand_missing': brand_missing_count,
        'expected_domain': expected_domain,
        'details': findings[:5],
        'severity': severity
    }


# =============================================================================
# MAIN AUDIT RUNNER
# =============================================================================

def run_audit(cid: str, account_name: str, brand_exceptions: set = None) -> dict:
    """Run all audits for a single account.

    Args:
        cid: Customer ID
        account_name: Account display name
        brand_exceptions: Set of brand terms to exclude from spell checking
    """
    result = {
        'cid': cid,
        'account_name': account_name,
        'portfolio': get_portfolio_name(cid),
        'audit_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        # Core checks
        'dki': None,
        'google_ai_assets': None,
        'url_validation': None,
        'ad_disapprovals': None,
        'seasonal_promotions': None,
        # Extended checks
        'auto_created_assets_setting': None,
        'final_url_expansion': None,
        'auto_applied_recommendations': None,
        'inappropriate_content': None,
        'spelling': None,
        'irrelevance': None,
        'overall_severity': 'OK',
        'error': None
    }

    try:
        # Run core audits
        result['dki'] = check_dki(cid)
        result['google_ai_assets'] = check_google_ai_assets(cid)
        result['url_validation'] = check_url_validation(cid)
        result['ad_disapprovals'] = check_ad_disapprovals(cid)
        result['seasonal_promotions'] = check_seasonal_promotions(cid)

        # Run extended audits
        result['auto_created_assets_setting'] = check_auto_created_assets_setting(cid)
        result['final_url_expansion'] = check_final_url_expansion(cid)
        result['auto_applied_recommendations'] = check_auto_applied_recommendations(cid)
        result['inappropriate_content'] = check_inappropriate_content(cid)
        result['spelling'] = check_spelling(cid, brand_exceptions)
        result['irrelevance'] = check_irrelevance(cid, account_name)

        # Calculate overall severity
        severities = [
            result['dki']['severity'],
            result['google_ai_assets']['severity'],
            result['url_validation']['severity'],
            result['ad_disapprovals']['severity'],
            result['seasonal_promotions']['severity'],
            result['auto_created_assets_setting']['severity'],
            result['final_url_expansion']['severity'],
            result['auto_applied_recommendations']['severity'],
            result['inappropriate_content']['severity'],
            result['spelling']['severity'],
            result['irrelevance']['severity'],
        ]

        if 'CRITICAL' in severities:
            result['overall_severity'] = 'CRITICAL'
        elif 'HIGH' in severities:
            result['overall_severity'] = 'HIGH'
        elif 'MEDIUM' in severities:
            result['overall_severity'] = 'MEDIUM'
        else:
            result['overall_severity'] = 'OK'

    except Exception as e:
        result['error'] = str(e)[:100]
        result['overall_severity'] = 'ERROR'

    return result


def format_row_for_sheet(result: dict) -> list:
    """Format audit result as a row for Google Sheet."""
    def summarize(audit_result, key='count'):
        if audit_result is None:
            return 'Error'
        return f"{audit_result.get(key, 0)} ({audit_result.get('severity', 'N/A')})"

    def get_details(audit_result, detail_key='text'):
        if audit_result is None or not audit_result.get('details'):
            return ''
        details = audit_result['details'][:3]
        return '; '.join([str(d.get(detail_key, d.get('text', d.get('url', d.get('campaign', d.get('type', ''))))))[:40] for d in details])

    return [
        result['audit_date'],
        result['portfolio'],
        result['account_name'],
        result['cid'],
        result['overall_severity'],
        # DKI
        result['dki']['count'] if result['dki'] else 'Error',
        result['dki']['severity'] if result['dki'] else 'Error',
        get_details(result['dki']),
        # Google AI Assets
        result['google_ai_assets']['count'] if result['google_ai_assets'] else 'Error',
        result['google_ai_assets']['severity'] if result['google_ai_assets'] else 'Error',
        get_details(result['google_ai_assets']),
        # URL Validation
        result['url_validation']['count'] if result['url_validation'] else 'Error',
        result['url_validation']['severity'] if result['url_validation'] else 'Error',
        get_details(result['url_validation']),
        # Ad Disapprovals
        result['ad_disapprovals']['count'] if result['ad_disapprovals'] else 'Error',
        result['ad_disapprovals']['severity'] if result['ad_disapprovals'] else 'Error',
        get_details(result['ad_disapprovals']),
        # Seasonal Promotions
        result['seasonal_promotions']['count'] if result['seasonal_promotions'] else 'Error',
        result['seasonal_promotions']['severity'] if result['seasonal_promotions'] else 'Error',
        get_details(result['seasonal_promotions']),
        # Auto-Created Assets Setting - checks if setting is currently ENABLED
        result['auto_created_assets_setting']['enabled_count'] if result['auto_created_assets_setting'] else 'Error',
        result['auto_created_assets_setting']['severity'] if result['auto_created_assets_setting'] else 'Error',
        get_details(result['auto_created_assets_setting'], 'campaign'),
        # Final URL Expansion
        result['final_url_expansion']['count'] if result['final_url_expansion'] else 'Error',
        result['final_url_expansion']['severity'] if result['final_url_expansion'] else 'Error',
        get_details(result['final_url_expansion'], 'campaign'),
        # Auto-Applied Recommendations
        result['auto_applied_recommendations']['count'] if result['auto_applied_recommendations'] else 'Error',
        result['auto_applied_recommendations']['severity'] if result['auto_applied_recommendations'] else 'Error',
        get_details(result['auto_applied_recommendations'], 'type'),
        # Inappropriate Content
        result['inappropriate_content']['count'] if result['inappropriate_content'] else 'Error',
        result['inappropriate_content']['severity'] if result['inappropriate_content'] else 'Error',
        get_details(result['inappropriate_content'], 'matched_term'),
        # Spelling
        result['spelling']['count'] if result['spelling'] else 'Error',
        result['spelling']['severity'] if result['spelling'] else 'Error',
        get_details(result['spelling'], 'word'),
        # Irrelevance
        result['irrelevance']['count'] if result['irrelevance'] else 'Error',
        result['irrelevance']['severity'] if result['irrelevance'] else 'Error',
        get_details(result['irrelevance'], 'type'),
        # Error
        result.get('error', '')
    ]


def portfolio_tab_display_name(portfolio: str) -> str:
    """Sheet tab name for a portfolio scope ('all' gets a combined tab)."""
    return 'All Portfolios' if portfolio == 'all' else portfolio.title()


def write_to_sheet(results: list, sheet_id: str, config_path: str,
                   dry_run: bool = False, portfolio: str = None):
    """Write audit results to Google Sheet."""
    headers = [
        'Audit Date', 'Portfolio', 'Account Name', 'CID', 'Overall Severity',
        'DKI Count', 'DKI Severity', 'DKI Details',
        'AI Assets Count', 'AI Assets Severity', 'AI Assets Details',
        'Broken URLs Count', 'Broken URLs Severity', 'Broken URLs Details',
        'Disapprovals Count', 'Disapprovals Severity', 'Disapprovals Details',
        'Seasonal Count', 'Seasonal Severity', 'Seasonal Details',
        'Auto-Created Setting Enabled', 'Auto-Created Setting Severity', 'Auto-Created Setting Details',
        'URL Expansion Count', 'URL Expansion Severity', 'URL Expansion Details',
        'Auto-Apply Count', 'Auto-Apply Severity', 'Auto-Apply Details',
        'Inappropriate Count', 'Inappropriate Severity', 'Inappropriate Details',
        'Spelling Count', 'Spelling Severity', 'Spelling Details',
        'Irrelevance Count', 'Irrelevance Severity', 'Irrelevance Details',
        'Error'
    ]

    rows = [format_row_for_sheet(r) for r in results]

    if dry_run:
        print("\n[DRY RUN] Would write to Google Sheet:")
        print(f"  Sheet: {sheet_id or '(no --sheet-id provided — required for a live run)'}")
        print(f"  Tab: {TAB_NAME}")
        print(f"  Rows: {len(rows)}")
        print(f"  Headers: {headers}")
        return

    print(f"\nWriting {len(rows)} rows to Google Sheet...")

    sheets_client = get_sheets_client(config_path)
    spreadsheet = sheets_client.open_by_key(sheet_id)

    try:
        worksheet = spreadsheet.worksheet(TAB_NAME)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=TAB_NAME, rows=1000, cols=40)

    # Clear existing data and write new
    worksheet.clear()
    worksheet.append_row(headers)
    worksheet.append_rows(rows)

    print(f"Successfully wrote {len(rows)} rows to '{TAB_NAME}' tab")

    # Also write to portfolio-specific tab if applicable
    if portfolio:
        portfolio_tab_name = portfolio_tab_display_name(portfolio)
        try:
            portfolio_ws = spreadsheet.worksheet(portfolio_tab_name)
        except gspread.exceptions.WorksheetNotFound:
            portfolio_ws = spreadsheet.add_worksheet(title=portfolio_tab_name, rows=1000, cols=40)

        portfolio_ws.clear()
        portfolio_ws.append_row(headers)
        portfolio_ws.append_rows(rows)
        print(f"Successfully wrote {len(rows)} rows to '{portfolio_tab_name}' tab")

    # Also append summary to History tab for trend tracking
    write_to_history(results, spreadsheet, portfolio)

    # Write per-account data to Account History tab
    write_to_account_history(results, spreadsheet, portfolio)


def compare_issue_count(current: int, previous: int) -> str:
    """Compare current issue count to previous, return status tag."""
    if previous == 0 and current > 0:
        return 'NEW'
    elif previous > 0 and current == 0:
        return 'RESOLVED'
    elif current > previous:
        return 'INCREASED'
    elif current < previous:
        return 'DECREASED'
    else:
        return 'SAME'


def get_previous_account_data(spreadsheet, cid: str, portfolio: str = None):
    """Retrieve previous audit data for a specific account from Account History tab.

    Returns dict with previous issue counts, or None if no previous data exists.
    """
    try:
        account_history_ws = spreadsheet.worksheet(ACCOUNT_HISTORY_TAB_NAME)
        all_data = account_history_ws.get_all_values()

        if len(all_data) < 2:  # No data rows (only header or empty)
            return None

        headers = all_data[0]

        # Find the most recent row for this CID (search backwards)
        for row in reversed(all_data[1:]):
            row_dict = dict(zip(headers, row))

            # Match by CID (and optionally portfolio)
            if row_dict.get('CID') == cid:
                if portfolio and row_dict.get('Portfolio') != portfolio:
                    continue  # Skip if portfolio doesn't match

                # Parse previous counts
                return {
                    'audit_date': row_dict.get('Audit Date', ''),
                    'dki': int(row_dict.get('DKI Count', 0) or 0),
                    'ai_assets': int(row_dict.get('AI Assets Count', 0) or 0),
                    'broken_urls': int(row_dict.get('Broken URLs Count', 0) or 0),
                    'disapprovals': int(row_dict.get('Disapprovals Count', 0) or 0),
                    'seasonal': int(row_dict.get('Seasonal Count', 0) or 0),
                    'url_expansion': int(row_dict.get('URL Expansion Count', 0) or 0),
                    'auto_apply': int(row_dict.get('Auto-Apply Count', 0) or 0),
                    'inappropriate': int(row_dict.get('Inappropriate Count', 0) or 0),
                    'spelling': int(row_dict.get('Spelling Count', 0) or 0),
                    'irrelevance': int(row_dict.get('Irrelevance Count', 0) or 0),
                }

        return None  # No previous data found for this CID

    except gspread.exceptions.WorksheetNotFound:
        return None  # Account History tab doesn't exist yet


def compare_to_previous_run(results: list, spreadsheet, portfolio: str = None):
    """Compare current audit results to previous run, add comparison metadata.

    Modifies results in-place by adding 'comparison' dict to each account.
    """
    for result in results:
        cid = result['cid']

        # Get previous data for this account
        prev_data = get_previous_account_data(spreadsheet, cid, portfolio)

        if not prev_data:
            # First run for this account
            result['comparison'] = {
                'status': 'FIRST_RUN',
                'previous_audit_date': None,
                'deltas': {}
            }
            continue

        # Calculate deltas for each issue type
        deltas = {}

        issue_mappings = {
            'dki': result['dki']['count'],
            'ai_assets': result['google_ai_assets']['count'],
            'broken_urls': result['url_validation']['count'],
            'disapprovals': result['ad_disapprovals']['count'],
            'seasonal': result['seasonal_promotions']['count'],
            'url_expansion': result['final_url_expansion']['count'],
            'auto_apply': result['auto_applied_recommendations']['count'],
            'inappropriate': result['inappropriate_content']['count'],
            'spelling': result['spelling']['count'],
            'irrelevance': result['irrelevance']['count'],
        }

        for issue_type, current_count in issue_mappings.items():
            previous_count = prev_data.get(issue_type, 0)
            delta = current_count - previous_count
            status = compare_issue_count(current_count, previous_count)

            deltas[issue_type] = {
                'current': current_count,
                'previous': previous_count,
                'delta': delta,
                'status': status
            }

        result['comparison'] = {
            'status': 'COMPARED',
            'previous_audit_date': prev_data['audit_date'],
            'deltas': deltas
        }

    return results


def write_to_history(results: list, spreadsheet, portfolio: str = None):
    """Append summary row to History tab for trend tracking over time."""
    history_headers = [
        'Audit Date', 'Portfolio', 'Accounts Audited',
        'CRITICAL', 'HIGH', 'MEDIUM', 'OK', 'ERROR',
        'Total DKI', 'Total AI Assets', 'Total Broken URLs',
        'Total Disapprovals', 'Total Seasonal', 'Total URL Expansion',
        'Total Auto-Apply', 'Total Inappropriate', 'Total Spelling', 'Total Irrelevance'
    ]

    # Calculate totals
    severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'OK': 0, 'ERROR': 0}
    totals = {
        'dki': 0, 'ai_assets': 0, 'broken_urls': 0, 'disapprovals': 0,
        'seasonal': 0, 'url_expansion': 0, 'auto_apply': 0,
        'inappropriate': 0, 'spelling': 0, 'irrelevance': 0
    }

    for r in results:
        severity_counts[r['overall_severity']] = severity_counts.get(r['overall_severity'], 0) + 1
        if r['dki']:
            totals['dki'] += r['dki']['count']
        if r['google_ai_assets']:
            totals['ai_assets'] += r['google_ai_assets']['count']
        if r['url_validation']:
            totals['broken_urls'] += r['url_validation']['count']
        if r['ad_disapprovals']:
            totals['disapprovals'] += r['ad_disapprovals']['count']
        if r['seasonal_promotions']:
            totals['seasonal'] += r['seasonal_promotions']['count']
        if r['final_url_expansion']:
            totals['url_expansion'] += r['final_url_expansion']['count']
        if r['auto_applied_recommendations']:
            totals['auto_apply'] += r['auto_applied_recommendations']['count']
        if r['inappropriate_content']:
            totals['inappropriate'] += r['inappropriate_content']['count']
        if r['spelling']:
            totals['spelling'] += r['spelling']['count']
        if r['irrelevance']:
            totals['irrelevance'] += r['irrelevance']['count']

    # Build summary row
    summary_row = [
        datetime.now().strftime('%Y-%m-%d %H:%M'),
        portfolio or 'custom',
        len(results),
        severity_counts['CRITICAL'],
        severity_counts['HIGH'],
        severity_counts['MEDIUM'],
        severity_counts['OK'],
        severity_counts['ERROR'],
        totals['dki'],
        totals['ai_assets'],
        totals['broken_urls'],
        totals['disapprovals'],
        totals['seasonal'],
        totals['url_expansion'],
        totals['auto_apply'],
        totals['inappropriate'],
        totals['spelling'],
        totals['irrelevance'],
    ]

    try:
        history_ws = spreadsheet.worksheet(HISTORY_TAB_NAME)
    except gspread.exceptions.WorksheetNotFound:
        history_ws = spreadsheet.add_worksheet(title=HISTORY_TAB_NAME, rows=1000, cols=20)
        history_ws.append_row(history_headers)

    # Check if headers exist (first row)
    existing = history_ws.row_values(1)
    if not existing or existing[0] != 'Audit Date':
        history_ws.insert_row(history_headers, 1)

    # Append the summary row
    history_ws.append_row(summary_row)
    print(f"Appended summary to '{HISTORY_TAB_NAME}' tab for trend tracking")


def count_issue_occurrences_in_history(history_data: list, cid: str, issue_type: str, days_back: int = 90) -> dict:
    """Count how many times an issue appeared for an account in the last N days.

    Returns dict with:
    - count: Number of occurrences
    - first_seen: Date of first occurrence
    - last_seen: Date of last occurrence
    - dates: List of all audit dates where issue was present
    """
    from datetime import datetime, timedelta

    if len(history_data) < 2:  # No data (header only or empty)
        return {'count': 0, 'first_seen': None, 'last_seen': None, 'dates': []}

    headers = history_data[0]
    cutoff_date = datetime.now() - timedelta(days=days_back)

    # Map issue_type to column name
    issue_column_map = {
        'dki': 'DKI Count',
        'ai_assets': 'AI Assets Count',
        'broken_urls': 'Broken URLs Count',
        'disapprovals': 'Disapprovals Count',
        'seasonal': 'Seasonal Count',
        'url_expansion': 'URL Expansion Count',
        'auto_apply': 'Auto-Apply Count',
        'inappropriate': 'Inappropriate Count',
        'spelling': 'Spelling Count',
        'irrelevance': 'Irrelevance Count',
    }

    column_name = issue_column_map.get(issue_type)
    if not column_name:
        return {'count': 0, 'first_seen': None, 'last_seen': None, 'dates': []}

    occurrences = []

    for row in history_data[1:]:
        row_dict = dict(zip(headers, row))

        # Match by CID
        if row_dict.get('CID') != cid:
            continue

        # Parse audit date
        audit_date_str = row_dict.get('Audit Date', '')
        try:
            audit_date = datetime.strptime(audit_date_str, '%Y-%m-%d %H:%M')
        except ValueError:
            continue

        # Check if within date range
        if audit_date < cutoff_date:
            continue

        # Check if issue was present (count > 0)
        issue_count = int(row_dict.get(column_name, 0) or 0)
        if issue_count > 0:
            occurrences.append(audit_date_str)

    if not occurrences:
        return {'count': 0, 'first_seen': None, 'last_seen': None, 'dates': []}

    # Sort by date
    sorted_dates = sorted(occurrences)

    return {
        'count': len(occurrences),
        'first_seen': sorted_dates[0],
        'last_seen': sorted_dates[-1],
        'dates': sorted_dates
    }


def slugify_account_name(account_name: str) -> str:
    """Convert account name to filename-safe slug."""
    # Remove a "Parent Brand - " prefix (e.g., "Northgate Group - Riverside Flats" -> "Riverside Flats")
    if ' - ' in account_name:
        account_name = account_name.split(' - ', 1)[1]

    # Convert to lowercase, replace spaces and special chars with dashes
    slug = account_name.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)  # Remove non-alphanumeric except spaces and dashes
    slug = re.sub(r'[-\s]+', '-', slug)   # Replace spaces and multiple dashes with single dash
    slug = slug.strip('-')                # Remove leading/trailing dashes

    return slug


def account_file_path(account_name: str, portfolio: str) -> str:
    """Path for a chronic-issue account file: ./accounts/<portfolio>/<slug>.md"""
    portfolio_folder = portfolio.lower().replace(' ', '-')
    slug = slugify_account_name(account_name)
    return os.path.join(ACCOUNTS_FILES_DIR, portfolio_folder, f'{slug}.md')


def create_account_file(cid: str, account_name: str, portfolio: str, chronic_issues: list):
    """Create account file from template with chronic issues table pre-populated.

    Args:
        cid: Customer ID (no dashes)
        account_name: Full account name
        portfolio: Portfolio name (as defined in your registry)
        chronic_issues: List of chronic issue dicts for this account
    """
    account_file = account_file_path(account_name, portfolio)

    # Create folder if doesn't exist
    os.makedirs(os.path.dirname(account_file), exist_ok=True)

    # Build chronic issues table
    chronic_table_rows = []
    for issue in chronic_issues:
        issue_type_display = issue['issue_type'].replace('_', ' ').title()
        chronic_table_rows.append(
            f"| creative_{issue['issue_type']} | {issue['first_seen'][:10]} | {issue['occurrences']} | active |"
        )

    chronic_table = '\n'.join(chronic_table_rows)

    # Create file content from template
    content = f"""---
Account: {account_name}
Portfolio: {portfolio}
CID: {cid}
Created: {datetime.now().strftime('%Y-%m-%d')}
Last Updated: {datetime.now().strftime('%Y-%m-%d')}
Status: active
---

## Account Overview

(Auto-generated account file due to chronic creative issues. Add description as needed.)

## Chronic Issues

| Issue Type | First Seen | Occurrences | Status |
|------------|------------|-------------|--------|
{chronic_table}

## Account Quirks

(Add any unique constraints or client-specific requirements here.)

## Historical Context

### What's Been Tried

(Document actions taken and their outcomes.)

### What Works

(Proven approaches for this account.)

### What Doesn't Work

(Failed approaches and why.)

## Related Investigations

(Link to investigation files if any exist.)

---

**Auto-created:** {datetime.now().strftime('%Y-%m-%d %H:%M')} by ads_checker_audit.py (chronic issue detection)
"""

    # Write file
    with open(account_file, 'w', encoding='utf-8') as f:
        f.write(content)

    return account_file


def update_chronic_issues_in_account_file(account_file: str, chronic_issues: list):
    """Update chronic issues table in existing account file.

    Args:
        account_file: Path to account file
        chronic_issues: List of chronic issue dicts for this account
    """
    # Read existing file
    with open(account_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find chronic issues table
    table_start = content.find('| Issue Type | First Seen | Occurrences | Status |')
    if table_start == -1:
        print(f"  Warning: Could not find chronic issues table in {account_file}")
        return

    # Find end of table (next ## heading or end of file)
    table_end = content.find('\n##', table_start)
    if table_end == -1:
        table_end = len(content)

    # Build updated table rows
    existing_issues = {}

    # Parse existing rows
    table_section = content[table_start:table_end]
    for line in table_section.split('\n')[2:]:  # Skip header and separator
        if line.strip().startswith('|'):
            parts = [p.strip() for p in line.split('|')[1:-1]]  # Remove outer pipes
            if len(parts) >= 4:
                issue_type = parts[0]
                existing_issues[issue_type] = {
                    'first_seen': parts[1],
                    'occurrences': parts[2],
                    'status': parts[3]
                }

    # Update with new chronic issues
    for issue in chronic_issues:
        issue_key = f"creative_{issue['issue_type']}"

        if issue_key in existing_issues:
            # Update occurrence count
            existing_issues[issue_key]['occurrences'] = str(issue['occurrences'])
            existing_issues[issue_key]['status'] = 'active'
        else:
            # Add new issue
            existing_issues[issue_key] = {
                'first_seen': issue['first_seen'][:10],
                'occurrences': str(issue['occurrences']),
                'status': 'active'
            }

    # Rebuild table
    new_table_rows = []
    for issue_type, data in sorted(existing_issues.items()):
        new_table_rows.append(
            f"| {issue_type} | {data['first_seen']} | {data['occurrences']} | {data['status']} |"
        )

    new_table = "| Issue Type | First Seen | Occurrences | Status |\n"
    new_table += "|------------|------------|-------------|--------|\n"
    new_table += '\n'.join(new_table_rows)

    # Replace table in content
    updated_content = content[:table_start] + new_table + content[table_end:]

    # Update "Last Updated" in frontmatter
    updated_content = re.sub(
        r'Last Updated: \d{4}-\d{2}-\d{2}',
        f"Last Updated: {datetime.now().strftime('%Y-%m-%d')}",
        updated_content
    )

    # Write back
    with open(account_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)


def prompt_account_file_creation(chronic_issues: list):
    """Prompt user to create account files for chronic issues (manual review required).

    This is the interactive prompt the skill's `echo "no" |` pattern answers —
    piping "no" skips file creation and lets the sheet write proceed.

    Returns dict mapping CID -> user decision (True = create, False = skip).
    """
    if not chronic_issues:
        return {}

    print("\n" + "=" * 80)
    print("CHRONIC ISSUES DETECTED - MANUAL REVIEW REQUIRED")
    print("=" * 80)
    print()
    print(f"The following accounts have chronic creative issues (3+ occurrences in 90 days):")
    print()

    # Group by account
    by_account = {}
    for issue in chronic_issues:
        cid = issue['cid']
        if cid not in by_account:
            by_account[cid] = {
                'account_name': issue['account_name'],
                'portfolio': issue['portfolio'],
                'issues': []
            }
        by_account[cid]['issues'].append(issue)

    # Display each account
    for i, (cid, data) in enumerate(by_account.items(), 1):
        severity_icon = "🔴" if any(iss['issue_type'] in ['disapprovals', 'broken_urls', 'inappropriate'] for iss in data['issues']) else "🟠"

        print(f"{severity_icon} {data['account_name']} ({cid})")
        print(f"   Portfolio: {data['portfolio']}")

        for issue in data['issues']:
            issue_display = issue['issue_type'].replace('_', ' ').title()
            print(f"   - {issue_display}: {issue['occurrences']} occurrences ({issue['first_seen'][:10]} to {issue['last_seen'][:10]})")

        print()

    print("=" * 80)
    print()

    # Prompt user
    response = input("Create account files for these accounts? (yes/no/selective): ").strip().lower()

    decisions = {}

    if response in ['yes', 'y']:
        # Create all
        for cid in by_account.keys():
            decisions[cid] = True
        print("Creating account files for all flagged accounts...")

    elif response in ['selective', 's']:
        # Ask for each account
        for cid, data in by_account.items():
            answer = input(f"\nCreate file for {data['account_name']}? (y/n): ").strip().lower()
            decisions[cid] = answer in ['yes', 'y']

    else:
        # Skip all
        print("Skipping account file creation.")
        for cid in by_account.keys():
            decisions[cid] = False

    return decisions


def detect_chronic_issues(results: list, spreadsheet, portfolio: str = None, threshold: int = 3, days_back: int = 90):
    """Detect accounts with chronic creative issues (3+ occurrences in 90 days).

    Returns list of chronic issues with account details for manual review.
    """
    try:
        account_history_ws = spreadsheet.worksheet(ACCOUNT_HISTORY_TAB_NAME)
        history_data = account_history_ws.get_all_values()
    except gspread.exceptions.WorksheetNotFound:
        # No history yet, can't detect chronic issues
        return []

    chronic_issues = []

    # Only check accounts with HIGH or CRITICAL severity
    high_severity_accounts = [r for r in results if r['overall_severity'] in ['HIGH', 'CRITICAL']]

    for account in high_severity_accounts:
        cid = account['cid']
        account_name = account['account_name']
        account_portfolio = portfolio or 'custom'

        # Get all flagged issue types for this account
        flagged_issues = []
        issue_checks = {
            'dki': account['dki']['count'],
            'ai_assets': account['google_ai_assets']['count'],
            'broken_urls': account['url_validation']['count'],
            'disapprovals': account['ad_disapprovals']['count'],
            'seasonal': account['seasonal_promotions']['count'],
            'url_expansion': account['final_url_expansion']['count'],
            'auto_apply': account['auto_applied_recommendations']['count'],
            'inappropriate': account['inappropriate_content']['count'],
            'spelling': account['spelling']['count'],
            'irrelevance': account['irrelevance']['count'],
        }

        for issue_type, count in issue_checks.items():
            # Only flag actionable issues (exclude AI assets which are informational)
            if issue_type == 'ai_assets':
                continue

            if count > 0:
                flagged_issues.append(issue_type)

        # For each flagged issue, check history
        for issue_type in flagged_issues:
            occurrence_data = count_issue_occurrences_in_history(
                history_data=history_data,
                cid=cid,
                issue_type=issue_type,
                days_back=days_back
            )

            if occurrence_data['count'] >= threshold:
                chronic_issues.append({
                    'cid': cid,
                    'account_name': account_name,
                    'portfolio': account_portfolio,
                    'issue_type': issue_type,
                    'occurrences': occurrence_data['count'],
                    'first_seen': occurrence_data['first_seen'],
                    'last_seen': occurrence_data['last_seen'],
                    'current_count': issue_checks[issue_type],
                })

    return chronic_issues


def write_to_account_history(results: list, spreadsheet, portfolio: str = None):
    """Write per-account audit data to Account History tab for trend tracking.

    This enables comparison across runs and chronic issue detection, and is
    the tab the companion briefing reader consumes. The headers below are the
    CACHED-OUTPUT CONTRACT — never change them without updating
    read_latest_ads_checker.py in lockstep.
    """
    account_history_headers = [
        'Audit Date', 'Portfolio', 'CID', 'Account Name', 'Overall Severity',
        'DKI Count', 'AI Assets Count', 'Broken URLs Count',
        'Disapprovals Count', 'Seasonal Count', 'URL Expansion Count',
        'Auto-Apply Count', 'Inappropriate Count', 'Spelling Count', 'Irrelevance Count'
    ]

    # Build rows (one per account)
    account_rows = []
    audit_date = datetime.now().strftime('%Y-%m-%d %H:%M')

    for r in results:
        account_rows.append([
            audit_date,
            portfolio or 'custom',
            r['cid'],
            r['account_name'],
            r['overall_severity'],
            r['dki']['count'] if r['dki'] else 0,
            r['google_ai_assets']['count'] if r['google_ai_assets'] else 0,
            r['url_validation']['count'] if r['url_validation'] else 0,
            r['ad_disapprovals']['count'] if r['ad_disapprovals'] else 0,
            r['seasonal_promotions']['count'] if r['seasonal_promotions'] else 0,
            r['final_url_expansion']['count'] if r['final_url_expansion'] else 0,
            r['auto_applied_recommendations']['count'] if r['auto_applied_recommendations'] else 0,
            r['inappropriate_content']['count'] if r['inappropriate_content'] else 0,
            r['spelling']['count'] if r['spelling'] else 0,
            r['irrelevance']['count'] if r['irrelevance'] else 0,
        ])

    # Get or create Account History worksheet
    try:
        account_history_ws = spreadsheet.worksheet(ACCOUNT_HISTORY_TAB_NAME)
    except gspread.exceptions.WorksheetNotFound:
        account_history_ws = spreadsheet.add_worksheet(title=ACCOUNT_HISTORY_TAB_NAME, rows=5000, cols=20)
        account_history_ws.append_row(account_history_headers)

    # Check if headers exist (first row)
    existing = account_history_ws.row_values(1)
    if not existing or existing[0] != 'Audit Date':
        account_history_ws.insert_row(account_history_headers, 1)

    # Append the account rows
    account_history_ws.append_rows(account_rows)
    print(f"Appended {len(account_rows)} account rows to '{ACCOUNT_HISTORY_TAB_NAME}' tab")

    # Track total row count (archive rows older than ~180 days as maintenance)
    total_rows = len(account_history_ws.get_all_values())
    if total_rows > 1000:
        print(f"  Warning: {total_rows} rows in Account History. Consider archiving rows >180 days old.")


def main():
    parser = argparse.ArgumentParser(
        description="Ads Checker Audit — creative compliance (10 checks) with issue-history intelligence"
    )
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument('--cid', help='Single customer ID to audit (dashes ok)')
    scope.add_argument('--cids', help='Comma-separated customer IDs to audit')
    scope.add_argument('--portfolio',
                       help="Portfolio to audit, as defined in your accounts.json ('all' = every account)")
    scope.add_argument('--all', action='store_true',
                       help='Audit every account (registry if present, otherwise walks your MCC)')
    parser.add_argument('--accounts', default='accounts.json',
                        help='Path to accounts.json registry (default: ./accounts.json)')
    parser.add_argument('--config', default='google-ads.yaml',
                        help='Path to google-ads.yaml (default: ./google-ads.yaml)')
    parser.add_argument('--sheet-id',
                        help='Output Google Sheet ID (required unless --dry-run)')
    parser.add_argument('--dry-run', action='store_true', help='Run without writing to sheet')

    args = parser.parse_args()

    if not args.dry_run and not args.sheet_id:
        print("Error: --sheet-id is required for a live run (or use --dry-run)")
        sys.exit(1)

    # Initialize the Google Ads client from --config
    global ga_service, REGISTRY
    try:
        ads_client = GoogleAdsClient.load_from_storage(args.config)
    except Exception as e:
        print(f"Error: could not load Google Ads credentials from {args.config}: {e}")
        print("See the google-ads-api-setup skill for creating google-ads.yaml.")
        sys.exit(1)
    ga_service = ads_client.get_service("GoogleAdsService")

    # Load the account registry (optional — required only for named portfolios)
    REGISTRY = load_accounts_registry(args.accounts)

    # Normalize the scope: --all is equivalent to --portfolio all
    portfolio_scope = args.portfolio or ('all' if args.all else None)

    # Determine accounts
    if args.cid or args.cids:
        cid_list = [args.cid] if args.cid else args.cids.split(',')
        accounts = {}
        for raw_cid in cid_list:
            cid = raw_cid.strip().replace('-', '')
            if not cid:
                continue
            entry = REGISTRY.get(cid)
            accounts[cid] = entry['name'] if entry else f"Account {cid}"
        if not accounts:
            print("Error: no valid customer IDs provided")
            sys.exit(1)
    elif portfolio_scope == 'all' and not REGISTRY:
        # No registry — walk the MCC in google-ads.yaml
        login_customer_id = get_login_customer_id(args.config)
        if not login_customer_id:
            print(f"Error: no registry at {args.accounts} and no login_customer_id in {args.config}.")
            print("Provide an accounts.json, set login_customer_id (your MCC), or use --cid/--cids.")
            sys.exit(1)
        print(f"No registry at {args.accounts} — walking MCC {login_customer_id}...")
        try:
            mcc_accounts = get_mcc_accounts(ads_client, login_customer_id)
        except GoogleAdsException as e:
            print(f"Error walking MCC {login_customer_id}: {e}")
            sys.exit(1)
        accounts = {}
        for cid, name in mcc_accounts:
            accounts[cid] = name
            REGISTRY[cid] = {'name': name, 'portfolio': 'default'}
        if not accounts:
            print("Error: MCC walk returned no enabled client accounts")
            sys.exit(1)
    else:
        if not REGISTRY:
            print(f"Error: --portfolio requires an accounts.json registry (looked for {args.accounts}).")
            print("Use --cid/--cids, or --all to walk the MCC without a registry.")
            sys.exit(1)
        try:
            accounts = get_accounts_for_portfolio(portfolio_scope)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    # Build brand exceptions from all account names for spell checking
    all_accounts_for_exceptions = (
        {cid: entry['name'] for cid, entry in REGISTRY.items()} if REGISTRY else accounts
    )
    brand_exceptions = build_brand_exceptions_from_accounts(all_accounts_for_exceptions)
    print(f"Loaded {len(brand_exceptions)} brand terms as spelling exceptions")

    # Header
    print("=" * 80)
    print("ADS CHECKER AUDIT (10 CHECKS)")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Accounts to audit: {len(accounts)}")
    print(f"Checks: DKI, AI Assets, URLs, Disapprovals, Seasonal, URL Expansion, Auto-Apply, Inappropriate, Spelling, Irrelevance")
    print()

    # Run audits
    results = []
    for i, (cid, name) in enumerate(accounts.items(), 1):
        print(f"[{i}/{len(accounts)}] Auditing {name}...", end=" ", flush=True)

        result = run_audit(cid, name, brand_exceptions)
        results.append(result)

        # Print summary
        if result['error']:
            print(f"ERROR: {result['error']}")
        else:
            # Count actionable issues (exclude AI assets and URL expansion from count)
            actionable_issues = sum([
                result['dki']['count'],
                result['url_validation']['count'],
                result['ad_disapprovals']['count'],
                result['seasonal_promotions']['count'],
                result['auto_applied_recommendations'].get('high_risk_count', 0),
                result['inappropriate_content']['count'],
                result['spelling']['count'],
                result['irrelevance']['count'],
            ])
            ai_assets = result['google_ai_assets']['count']
            auto_created_enabled = result['auto_created_assets_setting']['enabled_count']
            url_expansion = result['final_url_expansion']['count']
            auto_apply = result['auto_applied_recommendations']['count']
            inappropriate = result['inappropriate_content']['count']
            spelling = result['spelling']['count']
            irrelevance = result['irrelevance']['count']
            severity = result['overall_severity']

            extras = []
            if ai_assets > 0:
                extras.append(f"{ai_assets} AI")
            if auto_created_enabled > 0:
                extras.append(f"{auto_created_enabled} auto-create ON")
            if url_expansion > 0:
                extras.append(f"{url_expansion} URL exp")
            if auto_apply > 0:
                extras.append(f"{auto_apply} auto-apply")
            if inappropriate > 0:
                extras.append(f"{inappropriate} inappropriate")
            if spelling > 0:
                extras.append(f"{spelling} spelling")
            if irrelevance > 0:
                extras.append(f"{irrelevance} irrelevance")

            if extras:
                print(f"{severity} ({actionable_issues} issues, {', '.join(extras)})")
            else:
                print(f"{severity} ({actionable_issues} issues)")

        # Rate limiting
        time.sleep(0.3)

    # Summary
    print()
    print("=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)

    severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'OK': 0, 'ERROR': 0}
    for r in results:
        severity_counts[r['overall_severity']] = severity_counts.get(r['overall_severity'], 0) + 1

    print(f"Total accounts: {len(results)}")
    print(f"  CRITICAL: {severity_counts['CRITICAL']}")
    print(f"  HIGH: {severity_counts['HIGH']}")
    print(f"  MEDIUM: {severity_counts['MEDIUM']}")
    print(f"  OK: {severity_counts['OK']}")
    print(f"  ERROR: {severity_counts['ERROR']}")

    # Compare to previous run and write to sheet
    if not args.dry_run:
        sheets_client = get_sheets_client(args.config)
        spreadsheet = sheets_client.open_by_key(args.sheet_id)

        # Compare to previous run (adds 'comparison' metadata to results)
        print("\nComparing to previous audit...")
        results = compare_to_previous_run(results, spreadsheet, portfolio_scope)

        # Show comparison summary
        print("\n" + "=" * 80)
        print("COMPARISON TO PREVIOUS RUN")
        print("=" * 80)

        first_run_count = sum(1 for r in results if r.get('comparison', {}).get('status') == 'FIRST_RUN')
        compared_count = sum(1 for r in results if r.get('comparison', {}).get('status') == 'COMPARED')

        print(f"First-time audits: {first_run_count}")
        print(f"Compared to previous: {compared_count}")

        if compared_count > 0:
            # Count accounts with NEW, INCREASED, RESOLVED issues
            new_issues = []
            increased_issues = []
            resolved_issues = []

            for r in results:
                if r.get('comparison', {}).get('status') != 'COMPARED':
                    continue

                deltas = r['comparison']['deltas']
                account_new = []
                account_increased = []
                account_resolved = []

                for issue_type, delta_info in deltas.items():
                    if delta_info['status'] == 'NEW' and delta_info['current'] > 0:
                        account_new.append(f"{issue_type} ({delta_info['current']})")
                    elif delta_info['status'] == 'INCREASED':
                        account_increased.append(f"{issue_type} (+{delta_info['delta']})")
                    elif delta_info['status'] == 'RESOLVED':
                        account_resolved.append(f"{issue_type}")

                if account_new:
                    new_issues.append(f"  • {r['account_name']}: {', '.join(account_new)}")
                if account_increased:
                    increased_issues.append(f"  • {r['account_name']}: {', '.join(account_increased)}")
                if account_resolved:
                    resolved_issues.append(f"  • {r['account_name']}: {', '.join(account_resolved)}")

            if new_issues:
                print(f"\nNEW ISSUES ({len(new_issues)} accounts):")
                for issue in new_issues[:10]:  # Show top 10
                    print(issue)
                if len(new_issues) > 10:
                    print(f"  ... and {len(new_issues) - 10} more")

            if increased_issues:
                print(f"\nINCREASED ISSUES ({len(increased_issues)} accounts):")
                for issue in increased_issues[:10]:
                    print(issue)
                if len(increased_issues) > 10:
                    print(f"  ... and {len(increased_issues) - 10} more")

            if resolved_issues:
                print(f"\nRESOLVED ISSUES ({len(resolved_issues)} accounts):")
                for issue in resolved_issues[:10]:
                    print(issue)
                if len(resolved_issues) > 10:
                    print(f"  ... and {len(resolved_issues) - 10} more")

            if not new_issues and not increased_issues and not resolved_issues:
                print("\nNo changes since last audit (all issue counts SAME)")

        # Detect chronic issues
        print("\nDetecting chronic issues...")
        chronic_issues = detect_chronic_issues(results, spreadsheet, portfolio_scope)

        if chronic_issues:
            # Group by account for manual review prompt
            by_account = {}
            for issue in chronic_issues:
                cid = issue['cid']
                if cid not in by_account:
                    by_account[cid] = []
                by_account[cid].append(issue)

            # Prompt user for account file creation
            decisions = prompt_account_file_creation(chronic_issues)

            # Create/update account files based on user decisions
            for cid, create_file in decisions.items():
                if not create_file:
                    continue

                account_issues = by_account[cid]
                account_name = account_issues[0]['account_name']
                portfolio_name = account_issues[0]['portfolio']

                account_file = account_file_path(account_name, portfolio_name)

                if os.path.exists(account_file):
                    # Update existing file
                    print(f"  Updating {account_file}...")
                    update_chronic_issues_in_account_file(account_file, account_issues)
                else:
                    # Create new file
                    print(f"  Creating {account_file}...")
                    created_file = create_account_file(cid, account_name, portfolio_name, account_issues)
                    print(f"  ✓ Created {created_file}")

            print("\nChronic issue logging complete.")
        else:
            print("No chronic issues detected (threshold: 3+ occurrences in 90 days)")

        # Write results
        write_to_sheet(results, args.sheet_id, args.config, dry_run=False, portfolio=portfolio_scope)
    else:
        write_to_sheet(results, args.sheet_id, args.config, dry_run=True, portfolio=portfolio_scope)

    print()
    print("=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
