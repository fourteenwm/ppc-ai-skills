"""Query Google Ads Campaign Settings.

Retrieves detailed campaign configuration including targeting, bidding, budget,
network settings, device adjustments, and URL exclusions. Use this to verify
current settings before making recommendations.

Usage:
    python query_campaign_settings.py <customer_id> "<campaign_name>"

Example:
    python query_campaign_settings.py 1234567890 "Pmax: Example Campaign"

Returns:
    - Campaign status, budget, bidding strategy
    - Geographic targeting (locations, radius, targeting type)
    - Device targeting and bid adjustments
    - URL exclusions
    - Network settings

Prerequisites:
    - google-ads.yaml at project root with valid OAuth credentials
    - pip install google-ads
"""

import sys
import os
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


def query_campaign_settings(client, customer_id, campaign_name):
    """Query campaign settings and configuration."""

    ga_service = client.get_service("GoogleAdsService")

    print("=" * 100)
    print(f"CAMPAIGN SETTINGS: {campaign_name}")
    print("=" * 100)
    print(f"Customer ID: {customer_id}")
    print(f"Campaign: {campaign_name}\n")

    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.advertising_channel_type,
            campaign.advertising_channel_sub_type,
            campaign_budget.amount_micros,
            campaign.bidding_strategy_type,
            campaign.target_cpa.target_cpa_micros,
            campaign.target_roas.target_roas,
            campaign.maximize_conversion_value.target_roas
        FROM campaign
        WHERE campaign.name = '{campaign_name}'
    """

    try:
        response = ga_service.search_stream(customer_id=customer_id, query=query)

        campaign_id = None
        for batch in response:
            for row in batch.results:
                campaign_id = row.campaign.id

                print("BASIC SETTINGS")
                print("=" * 100)
                print(f"Campaign ID: {row.campaign.id}")
                print(f"Status: {row.campaign.status.name}")
                print(f"Type: {row.campaign.advertising_channel_type.name}")
                if row.campaign.advertising_channel_sub_type:
                    print(f"Subtype: {row.campaign.advertising_channel_sub_type.name}")
                print(f"Budget: ${row.campaign_budget.amount_micros / 1_000_000:.2f}")
                print(f"Bid Strategy: {row.campaign.bidding_strategy_type.name}")

                if row.campaign.bidding_strategy_type.name == "TARGET_CPA":
                    if row.campaign.target_cpa.target_cpa_micros:
                        print(f"  Target CPA: ${row.campaign.target_cpa.target_cpa_micros / 1_000_000:.2f}")
                elif row.campaign.bidding_strategy_type.name == "TARGET_ROAS":
                    if row.campaign.target_roas.target_roas:
                        print(f"  Target ROAS: {row.campaign.target_roas.target_roas:.2f}x")
                elif row.campaign.bidding_strategy_type.name == "MAXIMIZE_CONVERSION_VALUE":
                    if row.campaign.maximize_conversion_value.target_roas:
                        print(f"  Target ROAS: {row.campaign.maximize_conversion_value.target_roas:.2f}x")
                    else:
                        print(f"  Target ROAS: Not set (maximize without constraint)")

                print()

        if not campaign_id:
            print(f"ERROR: Campaign '{campaign_name}' not found")
            return

        # Location Targeting
        print("GEOGRAPHIC TARGETING")
        print("=" * 100)

        location_query = f"""
            SELECT
                campaign.id,
                campaign_criterion.location.geo_target_constant,
                campaign_criterion.negative,
                campaign_criterion.type
            FROM campaign_criterion
            WHERE campaign.id = {campaign_id}
                AND campaign_criterion.type IN ('LOCATION', 'PROXIMITY')
        """

        response = ga_service.search_stream(customer_id=customer_id, query=location_query)

        locations = []
        proximities = []
        negative_locations = []

        for batch in response:
            for row in batch.results:
                if row.campaign_criterion.type.name == "LOCATION":
                    geo_target = row.campaign_criterion.location.geo_target_constant
                    if row.campaign_criterion.negative:
                        negative_locations.append(geo_target)
                    else:
                        locations.append(geo_target)
                elif row.campaign_criterion.type.name == "PROXIMITY":
                    proximities.append(row.campaign_criterion)

        if locations:
            print(f"Targeted Locations: {len(locations)} location(s)")
            for loc in locations[:10]:
                loc_id = loc.split('/')[-1]
                print(f"  - Geo Target ID: {loc_id}")

        if proximities:
            print(f"\nRadius Targeting: {len(proximities)} radius target(s)")
            print("  - Proximity targeting detected")

        if negative_locations:
            print(f"\nExcluded Locations: {len(negative_locations)} location(s)")
            for loc in negative_locations[:10]:
                loc_id = loc.split('/')[-1]
                print(f"  - Excluded Geo Target ID: {loc_id}")

        if not locations and not proximities:
            print("No location targeting found (targeting all locations)")

        print()

        # Geo Target Type
        settings_query = f"""
            SELECT
                campaign.id,
                campaign.geo_target_type_setting.positive_geo_target_type,
                campaign.geo_target_type_setting.negative_geo_target_type
            FROM campaign
            WHERE campaign.id = {campaign_id}
        """

        response = ga_service.search_stream(customer_id=customer_id, query=settings_query)

        for batch in response:
            for row in batch.results:
                print("LOCATION TARGETING TYPE")
                print("=" * 100)
                if row.campaign.geo_target_type_setting.positive_geo_target_type:
                    target_type = row.campaign.geo_target_type_setting.positive_geo_target_type.name
                    if target_type == "PRESENCE":
                        print("Presence: People in or regularly in your targeted locations")
                    elif target_type == "AREA_OF_INTEREST":
                        print("Presence or Interest: People in, regularly in, OR interested in your targeted locations")
                    else:
                        print(f"Target Type: {target_type}")
                print()

        # URL Expansion
        print("URL EXPANSION")
        print("=" * 100)

        url_query = f"""
            SELECT campaign.id, campaign.url_expansion_opt_out
            FROM campaign
            WHERE campaign.id = {campaign_id}
        """

        response = ga_service.search_stream(customer_id=customer_id, query=url_query)
        for batch in response:
            for row in batch.results:
                if row.campaign.url_expansion_opt_out:
                    print("URL Expansion: Opted out (using only provided URLs)")
                else:
                    print("URL Expansion: Enabled (Google may expand to similar URLs)")

        print("\nNote: Specific URL exclusion rules not accessible via API")
        print("Manual check required in Google Ads UI: Campaign Settings -> URL exclusions\n")

        # Device Targeting
        print("DEVICE TARGETING")
        print("=" * 100)

        device_query = f"""
            SELECT
                campaign.id,
                campaign_criterion.device.type,
                campaign_criterion.bid_modifier
            FROM campaign_criterion
            WHERE campaign.id = {campaign_id}
                AND campaign_criterion.type = 'DEVICE'
        """

        response = ga_service.search_stream(customer_id=customer_id, query=device_query)

        devices_found = False
        for batch in response:
            for row in batch.results:
                devices_found = True
                device_type = row.campaign_criterion.device.type.name
                bid_modifier = row.campaign_criterion.bid_modifier if row.campaign_criterion.bid_modifier else 1.0
                adjustment = (bid_modifier - 1.0) * 100

                if adjustment > 0:
                    print(f"{device_type}: +{adjustment:.0f}% bid adjustment")
                elif adjustment < 0:
                    print(f"{device_type}: {adjustment:.0f}% bid adjustment")
                else:
                    print(f"{device_type}: No bid adjustment")

        if not devices_found:
            print("No device bid adjustments configured")

        print()

        # Network Settings
        print("NETWORK SETTINGS")
        print("=" * 100)

        network_query = f"""
            SELECT
                campaign.id,
                campaign.network_settings.target_google_search,
                campaign.network_settings.target_search_network,
                campaign.network_settings.target_content_network,
                campaign.network_settings.target_partner_search_network
            FROM campaign
            WHERE campaign.id = {campaign_id}
        """

        response = ga_service.search_stream(customer_id=customer_id, query=network_query)

        for batch in response:
            for row in batch.results:
                ns = row.campaign.network_settings
                print(f"Google Search: {ns.target_google_search}")
                print(f"Search Partners: {ns.target_partner_search_network}")
                print(f"Display Network: {ns.target_content_network}")
                print(f"Search Network: {ns.target_search_network}")

        print()
        print("=" * 100)
        print("CAMPAIGN SETTINGS QUERY COMPLETE")
        print("=" * 100)

    except GoogleAdsException as ex:
        print(f"Google Ads API Error: {ex}")
        for error in ex.failure.errors:
            print(f"  Error: {error.message}")
        sys.exit(1)


def main():
    if len(sys.argv) < 3:
        print("ERROR: Missing required arguments")
        print("\nUsage:")
        print('  python query_campaign_settings.py <customer_id> "<campaign_name>"')
        print("\nExample:")
        print('  python query_campaign_settings.py 1234567890 "Pmax: Example Campaign"')
        sys.exit(1)

    customer_id = sys.argv[1].replace('-', '')
    campaign_name = sys.argv[2]

    client = GoogleAdsClient.load_from_storage("google-ads.yaml")
    query_campaign_settings(client, customer_id, campaign_name)


if __name__ == "__main__":
    main()
