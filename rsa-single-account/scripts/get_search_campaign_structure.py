#!/usr/bin/env python3
"""
Get Search Campaign Structure (Step 4 of the rsa-single-account skill)

Retrieves active Search campaigns (with "Search" in the name) and their
active ad groups — the ad group name becomes the primary keyword for that
ad group's RSA.

The "name contains 'Search'" filter is a deliberate production-safety
choice: it keeps the RSA generator away from campaigns that merely run on
the SEARCH channel (brand tests, DSAs, experiments) unless they're named
as Search builds. Adapt the LIKE clause if your naming convention differs.

Usage:
    python get_search_campaign_structure.py <customer_id>
    python get_search_campaign_structure.py 1234567890 --config google-ads.yaml
"""

import argparse
import io
import sys

from google.ads.googleads.client import GoogleAdsClient

# Windows console encoding fix
if sys.platform == 'win32' and sys.stdout is not None:
    try:
        if hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass


def load_google_ads_client(config_path):
    """Load the Google Ads client from google-ads.yaml."""
    try:
        return GoogleAdsClient.load_from_storage(config_path)
    except Exception as e:
        print(f"Error: could not load Google Ads credentials from {config_path}: {e}")
        print("See the google-ads-api-setup skill for creating google-ads.yaml.")
        sys.exit(1)


def get_search_campaign_structure(customer_id, config_path='google-ads.yaml'):
    """
    Get active Search campaigns and ad groups filtered by campaign name containing 'Search'.

    Args:
        customer_id (str): Customer ID (CID) to query
        config_path (str): Path to google-ads.yaml

    Returns:
        list: List of dicts with campaign and ad group details
    """
    ads_client = load_google_ads_client(config_path)
    ads_service = ads_client.get_service("GoogleAdsService")

    # GAQL query
    # Filter: ENABLED campaigns, SEARCH channel, name contains "Search", ENABLED ad groups
    query = """
        SELECT
            customer.descriptive_name,
            campaign.id,
            campaign.name,
            ad_group.id,
            ad_group.name
        FROM ad_group
        WHERE
            campaign.status = 'ENABLED'
            AND campaign.advertising_channel_type = 'SEARCH'
            AND campaign.name LIKE '%Search%'
            AND ad_group.status = 'ENABLED'
        ORDER BY campaign.name, ad_group.name
    """

    print(f"Querying customer {customer_id} for Search campaign structure...")
    print(f"Filter: Campaign name contains 'Search'\n")

    try:
        response = ads_service.search(customer_id=customer_id, query=query)

        structure = []
        for row in response:
            structure.append({
                "account_name": row.customer.descriptive_name,
                "campaign_id": row.campaign.id,
                "campaign_name": row.campaign.name,
                "ad_group_id": row.ad_group.id,
                "ad_group_name": row.ad_group.name
            })

        # Print summary
        print(f"Found {len(structure)} ad groups across campaigns:")

        # Group by campaign for display
        campaigns = {}
        for item in structure:
            campaign_name = item["campaign_name"]
            if campaign_name not in campaigns:
                campaigns[campaign_name] = []
            campaigns[campaign_name].append(item["ad_group_name"])

        for campaign_name, ad_groups in campaigns.items():
            print(f"\n{campaign_name}:")
            for ad_group_name in ad_groups:
                print(f"  - {ad_group_name}")

        return structure

    except Exception as e:
        print(f"Error querying Google Ads API: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description='Get active Search campaigns + ad groups for RSA generation'
    )
    parser.add_argument('customer_id', help='Customer ID to query (dashes ok)')
    parser.add_argument('--config', default='google-ads.yaml',
                        help='Path to google-ads.yaml (default: ./google-ads.yaml)')
    args = parser.parse_args()

    customer_id = args.customer_id.replace("-", "")  # Remove dashes if present

    result = get_search_campaign_structure(customer_id, config_path=args.config)

    if result:
        print(f"\n[OK] Successfully retrieved {len(result)} ad groups")
    else:
        print("\n[ERROR] Failed to retrieve campaign structure")
        sys.exit(1)


if __name__ == "__main__":
    main()
