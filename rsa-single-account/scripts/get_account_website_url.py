#!/usr/bin/env python3
"""
Get Account Website URL (Step 2 of the rsa-single-account skill)

Given a Customer ID, hunts for the business website in three passes:
customer-level URL settings, campaign URL settings, then ENABLED ad
final URLs — and reports the most common domain as the likely website.

The CID is read from stdin, so the script pipes cleanly:

Usage:
    echo "1234567890" | python get_account_website_url.py
    echo "1234567890" | python get_account_website_url.py --config google-ads.yaml

Prerequisites:
    - google-ads.yaml at project root (see the google-ads-api-setup skill)
    - pip install google-ads
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


def main():
    parser = argparse.ArgumentParser(
        description='Find the business website for a Google Ads account (CID via stdin)'
    )
    parser.add_argument('--config', default='google-ads.yaml',
                        help='Path to google-ads.yaml (default: ./google-ads.yaml)')
    args = parser.parse_args()

    ads_client = load_google_ads_client(args.config)

    customer_id = input("Enter customer ID (no dashes): ").strip().replace('-', '')
    if not customer_id:
        print("Error: no customer ID provided")
        sys.exit(1)

    ads_service = ads_client.get_service("GoogleAdsService")

    # Pass 1 — customer-level URL settings
    query = """
        SELECT
            customer.descriptive_name,
            customer.id,
            customer.final_url_suffix,
            customer.tracking_url_template
        FROM customer
    """

    print(f"Querying customer {customer_id}...")
    print()

    try:
        response = ads_service.search(customer_id=customer_id, query=query)
        for row in response:
            print(f"Account: {row.customer.descriptive_name}")
            print(f"CID: {row.customer.id}")
            print(f"Final URL Suffix: {row.customer.final_url_suffix}")
            print(f"Tracking Template: {row.customer.tracking_url_template}")
            print()
    except Exception as e:
        print(f"Error: {e}")

    # Pass 2 — campaign URL settings
    campaign_query = """
        SELECT
            campaign.name,
            campaign.final_url_suffix,
            campaign.tracking_url_template
        FROM campaign
        WHERE campaign.status = 'ENABLED'
        LIMIT 5
    """

    print("Checking campaigns for URL patterns...")
    print()

    try:
        response = ads_service.search(customer_id=customer_id, query=campaign_query)
        for row in response:
            print(f"Campaign: {row.campaign.name}")
            print(f"  Final URL Suffix: {row.campaign.final_url_suffix}")
            print(f"  Tracking Template: {row.campaign.tracking_url_template}")
            print()
    except Exception as e:
        print(f"Error: {e}")

    # Pass 3 — ENABLED ad final URLs (the reliable source)
    ad_query = """
        SELECT
            ad_group_ad.ad.final_urls,
            ad_group_ad.ad.type,
            ad_group.name
        FROM ad_group_ad
        WHERE ad_group_ad.status = 'ENABLED'
        LIMIT 10
    """

    print("Checking ads for final URLs...")
    print()

    try:
        response = ads_service.search(customer_id=customer_id, query=ad_query)
        urls = set()
        for row in response:
            if row.ad_group_ad.ad.final_urls:
                for url in row.ad_group_ad.ad.final_urls:
                    urls.add(url)
                    if len(urls) <= 5:  # Only print first 5 unique URLs
                        print(f"Found URL: {url}")

        if urls:
            print()
            print(f"Total unique URLs found: {len(urls)}")
            print()
            print("Most common domain:")
            # Extract domain from URLs
            domains = {}
            for url in urls:
                try:
                    domain = url.split('/')[2]
                    domains[domain] = domains.get(domain, 0) + 1
                except IndexError:
                    pass

            if domains:
                most_common = max(domains.items(), key=lambda x: x[1])
                print(f"  {most_common[0]} ({most_common[1]} ads)")
                print(f"  Primary website likely: https://{most_common[0]}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    main()
