"""Audit Performance Max Asset Automation Settings.

Checks all PMAX campaigns for automatically created asset settings.
Reports which settings are OPTED_IN vs OPTED_OUT.

Settings Checked:
- TEXT_ASSET_AUTOMATION (auto-generated headlines/descriptions)
- FINAL_URL_EXPANSION_TEXT_ASSET_AUTOMATION (URL expansion)
- GENERATE_ENHANCED_YOUTUBE_VIDEOS (video enhancement)
- GENERATE_IMAGE_ENHANCEMENT (image auto-cropping)
- GENERATE_IMAGE_EXTRACTION (sourcing images from URLs)

Usage:
    # Single account by CID
    python audit_pmax_asset_automation.py --cid 1234567890

    # Multiple accounts (comma-separated)
    python audit_pmax_asset_automation.py --cids "1234567890,2345678901"

    # All accounts under MCC
    python audit_pmax_asset_automation.py --all

Output:
    Per-account breakdown showing each PMAX campaign's asset automation settings
    with compliance status (all should be OPTED_OUT for full compliance).

Prerequisites:
    - google-ads.yaml at project root with valid OAuth credentials
    - pip install google-ads
"""

import sys
import argparse

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

ASSET_AUTOMATION_TYPES = {
    "TEXT_ASSET_AUTOMATION": "Auto-created text (headlines/descriptions)",
    "FINAL_URL_EXPANSION_TEXT_ASSET_AUTOMATION": "Final URL expansion",
    "GENERATE_ENHANCED_YOUTUBE_VIDEOS": "Auto-created videos",
    "GENERATE_IMAGE_ENHANCEMENT": "Auto image enhancement (cropping)",
    "GENERATE_IMAGE_EXTRACTION": "Auto image extraction from URLs",
}


def list_mcc_accounts(client):
    """List all enabled client accounts under the MCC."""
    import yaml
    with open('google-ads.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    login_cid = str(config.get('login_customer_id', '')).replace('-', '')

    if not login_cid:
        print("ERROR: login_customer_id not set in google-ads.yaml — cannot use --all")
        sys.exit(1)

    ga_service = client.get_service('GoogleAdsService')
    query = '''
        SELECT customer_client.id, customer_client.descriptive_name
        FROM customer_client
        WHERE customer_client.manager = FALSE
        AND customer_client.status = 'ENABLED'
        ORDER BY customer_client.descriptive_name
    '''
    response = ga_service.search(customer_id=login_cid, query=query)
    return [{'cid': str(row.customer_client.id), 'name': row.customer_client.descriptive_name} for row in response]


def audit_account_pmax_settings(client, customer_id):
    """Audit PMAX asset automation settings for a single account."""
    ga_service = client.get_service("GoogleAdsService")

    query = """
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.asset_automation_settings
        FROM campaign
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
            AND campaign.status IN ('ENABLED', 'PAUSED')
        ORDER BY campaign.name
    """

    try:
        response = ga_service.search_stream(customer_id=customer_id, query=query)

        campaigns = []
        for batch in response:
            for row in batch.results:
                campaign_data = {
                    'id': row.campaign.id,
                    'name': row.campaign.name,
                    'status': row.campaign.status.name,
                    'settings': {}
                }

                # Default all to OPTED_IN since that's the Google default
                for automation_type in ASSET_AUTOMATION_TYPES.keys():
                    campaign_data['settings'][automation_type] = "OPTED_IN"

                # Override with actual settings if present
                for setting in row.campaign.asset_automation_settings:
                    type_name = setting.asset_automation_type.name
                    status_name = setting.asset_automation_status.name
                    if type_name in ASSET_AUTOMATION_TYPES:
                        campaign_data['settings'][type_name] = status_name

                campaigns.append(campaign_data)

        return campaigns

    except GoogleAdsException as ex:
        print(f"  ERROR querying account {customer_id}: {ex.failure.errors[0].message}")
        return None


def print_account_report(account_name, customer_id, campaigns):
    """Print formatted report for a single account."""
    print("=" * 80)
    print(f"ACCOUNT: {account_name}")
    print(f"CID: {customer_id}")
    print("=" * 80)

    if not campaigns:
        print("  No PMAX campaigns found")
        print()
        return 0, 0

    total_settings = 0
    compliant_settings = 0

    for campaign in campaigns:
        print(f"\n  Campaign: {campaign['name']}")
        print(f"  Status: {campaign['status']}")
        print(f"  Asset Automation Settings:")

        campaign_compliant = 0
        campaign_total = len(ASSET_AUTOMATION_TYPES)

        for automation_type, description in ASSET_AUTOMATION_TYPES.items():
            status = campaign['settings'].get(automation_type, "OPTED_IN")
            if status == "OPTED_OUT":
                icon = "[OK]"
                campaign_compliant += 1
            else:
                icon = "[!]"
            print(f"    {icon} {description}: {status}")

        total_settings += campaign_total
        compliant_settings += campaign_compliant

        if campaign_compliant == campaign_total:
            print(f"  -> FULLY COMPLIANT ({campaign_compliant}/{campaign_total})")
        else:
            print(f"  -> NEEDS ATTENTION ({campaign_compliant}/{campaign_total} opted out)")

    print()
    return compliant_settings, total_settings


def main():
    parser = argparse.ArgumentParser(description='Audit PMAX asset automation settings')
    parser.add_argument('--cid', help='Single customer ID (no dashes)')
    parser.add_argument('--cids', help='Comma-separated customer IDs')
    parser.add_argument('--all', action='store_true', help='Audit all accounts under MCC (requires login_customer_id in google-ads.yaml)')
    args = parser.parse_args()

    if not args.cid and not args.cids and not args.all:
        parser.print_help()
        print("\nExamples:")
        print('  python audit_pmax_asset_automation.py --cid 1234567890')
        print('  python audit_pmax_asset_automation.py --cids "1234567890,2345678901"')
        print('  python audit_pmax_asset_automation.py --all')
        sys.exit(1)

    client = GoogleAdsClient.load_from_storage("google-ads.yaml")

    accounts_to_audit = []
    if args.all:
        print("Listing all accounts under MCC...")
        accounts_to_audit = list_mcc_accounts(client)
        print(f"Found {len(accounts_to_audit)} accounts to audit\n")
    elif args.cid:
        accounts_to_audit = [{'cid': args.cid.replace('-', ''), 'name': f'CID {args.cid}'}]
    elif args.cids:
        for cid in args.cids.split(','):
            cid_clean = cid.strip().replace('-', '')
            accounts_to_audit.append({'cid': cid_clean, 'name': f'CID {cid_clean}'})

    print("\n" + "=" * 80)
    print("PERFORMANCE MAX ASSET AUTOMATION AUDIT")
    print("=" * 80)
    print(f"Accounts to audit: {len(accounts_to_audit)}")
    print("=" * 80 + "\n")

    total_compliant = 0
    total_settings = 0
    accounts_with_issues = []

    for account in accounts_to_audit:
        campaigns = audit_account_pmax_settings(client, account['cid'])
        if campaigns is None:
            continue
        compliant, total = print_account_report(account['name'], account['cid'], campaigns)
        total_compliant += compliant
        total_settings += total
        if compliant < total:
            accounts_with_issues.append({
                'name': account['name'],
                'cid': account['cid'],
                'compliant': compliant,
                'total': total
            })

    print("=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    print(f"Total accounts audited: {len(accounts_to_audit)}")
    print(f"Total settings checked: {total_settings}")
    print(f"Compliant settings: {total_compliant}")
    print(f"Non-compliant settings: {total_settings - total_compliant}")

    if accounts_with_issues:
        print(f"\nAccounts needing attention: {len(accounts_with_issues)}")
        for account in accounts_with_issues:
            pct = (account['compliant'] / account['total'] * 100) if account['total'] > 0 else 0
            print(f"  - {account['name']} ({account['cid']}): {account['compliant']}/{account['total']} ({pct:.0f}%)")
    else:
        print("\nAll accounts fully compliant!")

    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
