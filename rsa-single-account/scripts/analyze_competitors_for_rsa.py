#!/usr/bin/env python3
"""
Competitive Analysis for RSA Generation (Step 3 of the rsa-single-account skill)

Finds competitors via SERP API and analyzes their messaging to identify
differentiation opportunities: which USPs are saturated (3+ competitors
use them — de-emphasize) and which of the client's USPs nobody else
mentions (emphasize).

Supports vertical-specific analysis via vertical_configs.json (ships
alongside this script with three example verticals — extend it for yours):
- property_management: Apartment/multifamily keywords
- auto_repair: Auto repair shop keywords
- plumbing: Plumbing service keywords

Usage:
    python analyze_competitors_for_rsa.py "<service>" "<location>" [--vertical <vertical>]

Example:
    python analyze_competitors_for_rsa.py "apartments" "Houston TX" --vertical property_management
    python analyze_competitors_for_rsa.py "auto repair" "Austin TX" --vertical auto_repair
    python analyze_competitors_for_rsa.py "plumbing" "Denver CO" --vertical plumbing

Prerequisites:
    - SERP_API_KEY environment variable (set in .env or shell)
      Get a key at serpapi.com
    - pip install google-search-results python-dotenv
"""

import sys
import io
import json
import os
from pathlib import Path
from serpapi import GoogleSearch
from collections import Counter

# Windows console encoding fix
if sys.platform == 'win32' and sys.stdout is not None:
    try:
        if hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass


def get_serpapi_key():
    """SERP API key from the SERP_API_KEY environment variable (.env supported)."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    api_key = os.environ.get('SERP_API_KEY')
    if not api_key:
        print("Error: SERP_API_KEY environment variable not set.")
        print("Get a key at serpapi.com, then add SERP_API_KEY to a .env file "
              "at project root or export it in your shell.")
        return None
    return api_key


def load_vertical_config(vertical: str = None):
    """
    Load vertical-specific configuration for competitive analysis.

    Args:
        vertical (str): Vertical name (see vertical_configs.json for the
                       shipped example set). If None, returns the default
                       (auto_repair for backwards compatibility).

    Returns:
        dict: Vertical configuration with usp_keywords, service_keywords, cta_keywords
    """
    config_path = Path(__file__).parent / 'vertical_configs.json'

    try:
        with open(config_path, 'r') as f:
            all_configs = json.load(f)
    except FileNotFoundError:
        print(f"Warning: Vertical configs not found at {config_path}, using defaults")
        return get_default_config()

    # Default to auto_repair for backwards compatibility
    if vertical is None:
        vertical = 'auto_repair'

    if vertical not in all_configs:
        available = [k for k in all_configs.keys() if not k.startswith('_')]
        print(f"Warning: Unknown vertical '{vertical}', available: {available}")
        print(f"Falling back to auto_repair")
        vertical = 'auto_repair'

    config = all_configs[vertical]
    print(f"[VERTICAL] Loaded config for: {config.get('display_name', vertical)}")
    return config


def get_default_config():
    """Return default config (auto_repair) if vertical_configs.json not found."""
    return {
        "display_name": "Auto Repair (Default)",
        "usp_keywords": {
            "licensed": "Licensed/Certified",
            "insured": "Licensed/Certified",
            "certified": "Licensed/Certified",
            "free estimate": "Free Estimates",
            "free quote": "Free Estimates",
            "same day": "Same-Day Service",
            "24/7": "24/7 Availability",
            "24 hour": "24/7 Availability",
            "family owned": "Family Owned",
            "years experience": "Years of Experience",
            "warranty": "Warranty/Guarantee",
            "guarantee": "Warranty/Guarantee",
            "best price": "Pricing Claims",
            "low price": "Pricing Claims",
            "affordable": "Pricing Claims",
            "competitive": "Pricing Claims",
            "satisfaction": "Satisfaction Guarantee"
        },
        "service_keywords": [
            "oil change", "brake", "tire", "engine", "transmission",
            "inspection", "diagnostic", "repair", "maintenance"
        ],
        "cta_keywords": [
            "call now", "book now", "schedule", "get quote",
            "contact us", "learn more", "call today"
        ],
        "saturation_threshold": 3,
        "unique_threshold": 1
    }


def search_competitors(service, location, vertical: str = None):
    """
    Search for competitors using SERP API.

    Args:
        service (str): Service type (e.g., "auto repair", "apartments")
        location (str): Location (e.g., "Austin TX", "Houston TX")
        vertical (str): Optional vertical for logging purposes

    Returns:
        dict: Search results with competitors
    """
    api_key = get_serpapi_key()
    if not api_key:
        return None

    query = f"{service} {location}"
    vertical_label = f" [{vertical}]" if vertical else ""
    print(f"Searching for: {query}{vertical_label}\n")

    params = {
        "q": query,
        "location": location,
        "api_key": api_key,
        "engine": "google"
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        return results
    except Exception as e:
        print(f"Error querying SERP API: {e}")
        return None


def extract_competitor_messaging(results, vertical_config: dict = None):
    """
    Extract competitor messaging from SERP results.

    Args:
        results (dict): SERP API results
        vertical_config (dict): Vertical-specific configuration with usp_keywords,
                               service_keywords, cta_keywords. If None, uses defaults.

    Returns:
        dict: Analyzed competitor messaging
    """
    # Load default config if none provided
    if vertical_config is None:
        vertical_config = get_default_config()

    analysis = {
        "competitors_found": 0,
        "competitor_names": [],
        "common_usps": [],
        "common_services": [],
        "pricing_mentions": [],
        "social_proof_types": [],
        "call_to_actions": [],
        "unique_angles": [],
        "vertical": vertical_config.get("display_name", "Unknown")
    }

    # Get vertical-specific keywords
    usp_keywords = vertical_config.get("usp_keywords", {})
    service_keywords = vertical_config.get("service_keywords", [])
    cta_keywords = vertical_config.get("cta_keywords", [])

    # Analyze paid ads
    ads_results = results.get("ads", [])
    print(f"Analyzing {len(ads_results)} paid ads with {len(usp_keywords)} USP keywords...\n")

    usps_mentioned = []
    services_mentioned = []
    ctas_found = []

    for i, ad in enumerate(ads_results[:5], 1):  # Top 5 ads
        title = ad.get("title", "")
        description = ad.get("description", "")
        sitelinks = ad.get("sitelinks", [])

        competitor_name = ad.get("displayed_link", "").replace("www.", "").split("/")[0]
        if competitor_name:
            analysis["competitor_names"].append(competitor_name)

        print(f"Competitor {i}: {title}")
        print(f"  Description: {description[:80]}...")

        # Extract USPs from ad copy
        ad_text = f"{title} {description}".lower()

        # Use vertical-specific USP keywords
        for keyword, usp_category in usp_keywords.items():
            if keyword in ad_text:
                usps_mentioned.append(usp_category)
                print(f"  USP: {usp_category} (matched: '{keyword}')")

        # Use vertical-specific service keywords
        for service_keyword in service_keywords:
            if service_keyword in ad_text:
                services_mentioned.append(service_keyword.title())

        # Use vertical-specific CTA keywords
        for cta in cta_keywords:
            if cta in ad_text:
                ctas_found.append(cta.title())

        print()

    # Analyze Local Service Ads (LSAs)
    local_service_ads = results.get("local_service_ads", [])
    if local_service_ads:
        print(f"Analyzing {len(local_service_ads)} Local Service Ads...\n")

        for lsa in local_service_ads[:3]:
            competitor_name = lsa.get("title", "")
            rating = lsa.get("rating")
            reviews = lsa.get("reviews")

            print(f"LSA: {competitor_name}")
            if rating:
                print(f"  Rating: {rating}★ ({reviews} reviews)")
                analysis["social_proof_types"].append(f"Rating: {rating}★")

    # Count most common USPs
    usp_counts = Counter(usps_mentioned)
    analysis["common_usps"] = [
        {"usp": usp, "frequency": count}
        for usp, count in usp_counts.most_common(10)
    ]

    # Count most common services
    service_counts = Counter(services_mentioned)
    analysis["common_services"] = [
        {"service": service, "frequency": count}
        for service, count in service_counts.most_common(10)
    ]

    # Count most common CTAs
    cta_counts = Counter(ctas_found)
    analysis["call_to_actions"] = [
        {"cta": cta, "frequency": count}
        for cta, count in cta_counts.most_common(5)
    ]

    analysis["competitors_found"] = len(ads_results) + len(local_service_ads)

    return analysis


def identify_gaps(client_usps, competitor_analysis):
    """
    Identify competitive gaps and differentiation opportunities.

    Args:
        client_usps (list): Client's USPs from website
        competitor_analysis (dict): Competitor messaging analysis

    Returns:
        dict: Gap analysis and recommendations
    """
    gaps = {
        "unique_to_client": [],
        "overemphasized_by_competitors": [],
        "underemphasized_by_competitors": [],
        "differentiation_angles": []
    }

    # Get competitor USPs (mentioned by 2+ competitors = common)
    common_competitor_usps = [
        usp["usp"] for usp in competitor_analysis["common_usps"]
        if usp["frequency"] >= 2
    ]

    # Find client USPs NOT commonly mentioned by competitors
    for client_usp in client_usps:
        client_usp_lower = client_usp.lower()

        # Check if this USP is rare among competitors
        is_unique = True
        for competitor_usp in common_competitor_usps:
            if competitor_usp.lower() in client_usp_lower or client_usp_lower in competitor_usp.lower():
                is_unique = False
                break

        if is_unique:
            gaps["unique_to_client"].append({
                "usp": client_usp,
                "recommendation": "EMPHASIZE - Unique differentiator"
            })

    # Find overemphasized competitor USPs (3+ mentions = saturated)
    for usp_data in competitor_analysis["common_usps"]:
        if usp_data["frequency"] >= 3:
            gaps["overemphasized_by_competitors"].append({
                "usp": usp_data["usp"],
                "frequency": usp_data["frequency"],
                "recommendation": "DE-EMPHASIZE - Saturated, not differentiating"
            })

    return gaps


def format_for_rsa_generation(competitor_analysis, gap_analysis):
    """
    Format competitive insights for RSA generation.

    Args:
        competitor_analysis (dict): Competitor analysis
        gap_analysis (dict): Gap analysis

    Returns:
        dict: Formatted insights for RSA generator
    """
    insights = {
        "competitive_landscape": {
            "competitors_found": competitor_analysis["competitors_found"],
            "most_common_usps": [usp["usp"] for usp in competitor_analysis["common_usps"][:5]],
            "most_common_services": [s["service"] for s in competitor_analysis["common_services"][:5]],
            "most_common_ctas": [cta["cta"] for cta in competitor_analysis["call_to_actions"][:3]]
        },
        "differentiation_opportunities": {
            "unique_client_usps": [item["usp"] for item in gap_analysis["unique_to_client"]],
            "avoid_saturated_usps": [item["usp"] for item in gap_analysis["overemphasized_by_competitors"]],
            "emphasis_strategy": "Focus on unique USPs, de-emphasize saturated claims"
        },
        "rsa_generation_guidance": {
            "prioritize_in_headlines": gap_analysis["unique_to_client"][:3] if gap_analysis["unique_to_client"] else [],
            "avoid_in_headlines": [item["usp"] for item in gap_analysis["overemphasized_by_competitors"][:2]],
            "competitive_angle": "Stand out by emphasizing what competitors don't mention"
        }
    }

    return insights


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Competitive Analysis for RSA Generation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python analyze_competitors_for_rsa.py "apartments" "Houston TX" --vertical property_management
  python analyze_competitors_for_rsa.py "auto repair" "Austin TX" --vertical auto_repair
  python analyze_competitors_for_rsa.py "plumbing" "Denver CO" --vertical plumbing
        '''
    )
    parser.add_argument('service', help='Service type (e.g., "apartments", "auto repair")')
    parser.add_argument('location', help='Location (e.g., "Houston TX")')
    parser.add_argument('--vertical', '-v', default='auto_repair',
                       help='Vertical for industry-specific keyword analysis, as defined '
                            'in vertical_configs.json (default: auto_repair)')

    args = parser.parse_args()

    service = args.service
    location = args.location
    vertical = args.vertical

    # Load vertical-specific configuration
    vertical_config = load_vertical_config(vertical)

    # Search for competitors
    results = search_competitors(service, location, vertical)
    if not results:
        print("[ERROR] Failed to retrieve competitor data")
        sys.exit(1)

    # Extract competitor messaging using vertical config
    competitor_analysis = extract_competitor_messaging(results, vertical_config)

    # Print summary
    print("\n" + "="*60)
    print("COMPETITIVE ANALYSIS SUMMARY")
    print("="*60)
    print(f"\nCompetitors Found: {competitor_analysis['competitors_found']}")

    print(f"\nMost Common USPs (across competitors):")
    for usp_data in competitor_analysis["common_usps"][:5]:
        print(f"  - {usp_data['usp']} (mentioned by {usp_data['frequency']} competitors)")

    print(f"\nMost Common Services Advertised:")
    for service_data in competitor_analysis["common_services"][:5]:
        print(f"  - {service_data['service']} (mentioned {service_data['frequency']} times)")

    print(f"\nMost Common CTAs:")
    for cta_data in competitor_analysis["call_to_actions"][:3]:
        print(f"  - {cta_data['cta']} (mentioned {cta_data['frequency']} times)")

    # Example gap analysis (requires client USPs from website)
    print("\n" + "="*60)
    print("Example client USPs (replace with actual from website):")
    example_client_usps = [
        "ASE Certified Master Technicians",
        "Lifetime Warranty on Labor",
        "Free Loaner Cars Available",
        "Family Owned Since 1985"
    ]

    for usp in example_client_usps:
        print(f"  - {usp}")

    gap_analysis = identify_gaps(example_client_usps, competitor_analysis)

    print("\n" + "="*60)
    print("GAP ANALYSIS")
    print("="*60)

    if gap_analysis["unique_to_client"]:
        print("\n[+] UNIQUE TO CLIENT (EMPHASIZE):")
        for item in gap_analysis["unique_to_client"]:
            print(f"  - {item['usp']}")
            print(f"    -> {item['recommendation']}")

    if gap_analysis["overemphasized_by_competitors"]:
        print("\n[!] SATURATED BY COMPETITORS (DE-EMPHASIZE):")
        for item in gap_analysis["overemphasized_by_competitors"]:
            print(f"  - {item['usp']} (mentioned by {item['frequency']} competitors)")
            print(f"    -> {item['recommendation']}")

    # Format for RSA generation
    rsa_insights = format_for_rsa_generation(competitor_analysis, gap_analysis)

    print("\n" + "="*60)
    print("RSA GENERATION GUIDANCE")
    print("="*60)
    print(f"\nPrioritize in Headlines:")
    for item in rsa_insights["rsa_generation_guidance"]["prioritize_in_headlines"]:
        print(f"  [+] {item['usp']}")

    print(f"\nAvoid in Headlines (saturated):")
    for usp in rsa_insights["rsa_generation_guidance"]["avoid_in_headlines"]:
        print(f"  [-] {usp}")

    print(f"\n[*] Strategy: {rsa_insights['rsa_generation_guidance']['competitive_angle']}")

    # Save to JSON for agent consumption
    output_file = "competitive_insights.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "competitor_analysis": competitor_analysis,
            "gap_analysis": gap_analysis,
            "rsa_insights": rsa_insights,
            "vertical": vertical
        }, f, indent=2)

    print(f"\n[OK] Analysis saved to: {output_file}")


if __name__ == "__main__":
    main()
