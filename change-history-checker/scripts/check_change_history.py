#!/usr/bin/env python3
"""Check Google Ads account change history for any date range.

Uses the change_status resource which has no 30-day limit (unlike change_event).

Usage:
    python check_change_history.py 1234567890 --start 2025-11-01 --end 2025-11-30
    python check_change_history.py 1234567890 --start 2025-11-01 --end 2025-11-30 --types ASSET CUSTOMER_ASSET
    python check_change_history.py 1234567890 --start 2025-11-01 --end 2025-11-30 --detailed

Prerequisites:
    - google-ads.yaml at project root with valid OAuth credentials
    - pip install google-ads pyyaml
"""

from google.ads.googleads.client import GoogleAdsClient
import argparse


def check_changes(customer_id: str, start_date: str, end_date: str, resource_types: list = None, detailed: bool = False):
    """Query change history for an account.

    Args:
        customer_id: Google Ads customer ID (no dashes)
        start_date: Start date YYYY-MM-DD
        end_date: End date YYYY-MM-DD
        resource_types: Optional list of resource types to filter (e.g., ['ASSET', 'AD_GROUP'])
        detailed: If True, show asset details for extension changes
    """
    client = GoogleAdsClient.load_from_storage('google-ads.yaml')
    ga_service = client.get_service('GoogleAdsService')

    type_filter = ''
    if resource_types:
        types_str = ', '.join(f"'{t}'" for t in resource_types)
        type_filter = f'AND change_status.resource_type IN ({types_str})'

    if detailed and (not resource_types or any(t in ['ASSET', 'CUSTOMER_ASSET', 'AD_GROUP_ASSET'] for t in resource_types)):
        query = f'''
            SELECT
                change_status.resource_name,
                change_status.resource_type,
                change_status.resource_status,
                change_status.last_change_date_time,
                asset.type,
                asset.name,
                asset.sitelink_asset.link_text,
                asset.callout_asset.callout_text,
                asset.structured_snippet_asset.header,
                asset.structured_snippet_asset.values
            FROM change_status
            WHERE change_status.last_change_date_time >= '{start_date}'
            AND change_status.last_change_date_time <= '{end_date}'
            {type_filter}
            ORDER BY change_status.last_change_date_time DESC
            LIMIT 500
        '''
    else:
        query = f'''
            SELECT
                change_status.resource_name,
                change_status.resource_type,
                change_status.resource_status,
                change_status.last_change_date_time
            FROM change_status
            WHERE change_status.last_change_date_time >= '{start_date}'
            AND change_status.last_change_date_time <= '{end_date}'
            {type_filter}
            ORDER BY change_status.last_change_date_time DESC
            LIMIT 500
        '''

    response = ga_service.search(customer_id=customer_id, query=query)

    changes = {}
    for row in response:
        date = row.change_status.last_change_date_time[:10]
        resource_type = row.change_status.resource_type.name
        status = row.change_status.resource_status.name

        key = f'{date}|{resource_type}'
        if key not in changes:
            changes[key] = {'count': 0, 'statuses': set(), 'details': []}
        changes[key]['count'] += 1
        changes[key]['statuses'].add(status)

        if detailed and hasattr(row, 'asset') and row.asset.type:
            asset_type = row.asset.type.name
            detail = None
            if asset_type == 'SITELINK':
                detail = f"Sitelink: {row.asset.sitelink_asset.link_text}"
            elif asset_type == 'CALLOUT':
                detail = f"Callout: {row.asset.callout_asset.callout_text}"
            elif asset_type == 'STRUCTURED_SNIPPET':
                header = row.asset.structured_snippet_asset.header
                values = list(row.asset.structured_snippet_asset.values)
                detail = f"Snippet ({header}): {values}"
            elif asset_type != 'UNKNOWN':
                detail = f"{asset_type}: {row.asset.name or 'unnamed'}"

            if detail and detail not in changes[key]['details']:
                changes[key]['details'].append(detail)

    print(f"\n{'='*60}")
    print(f"Change History: {customer_id}")
    print(f"Period: {start_date} to {end_date}")
    print(f"{'='*60}")

    current_date = None
    for key in sorted(changes.keys(), reverse=True):
        date, resource_type = key.split('|')
        if date != current_date:
            print(f"\n{date}:")
            current_date = date
        info = changes[key]
        statuses = ', '.join(sorted(info['statuses']))
        print(f"  {resource_type}: {info['count']} changes ({statuses})")

        if detailed and info['details']:
            for detail in info['details'][:10]:
                print(f"    - {detail}")
            if len(info['details']) > 10:
                print(f"    ... and {len(info['details']) - 10} more")


def list_accounts():
    """List all accessible client accounts under the MCC."""
    client = GoogleAdsClient.load_from_storage('google-ads.yaml')
    ga_service = client.get_service('GoogleAdsService')

    import yaml
    with open('google-ads.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    login_cid = str(config.get('login_customer_id', '')).replace('-', '')

    if not login_cid:
        print("ERROR: login_customer_id not set in google-ads.yaml")
        return

    query = '''
        SELECT
            customer_client.id,
            customer_client.descriptive_name
        FROM customer_client
        WHERE customer_client.manager = FALSE
        AND customer_client.status = 'ENABLED'
        ORDER BY customer_client.descriptive_name
    '''

    response = ga_service.search(customer_id=login_cid, query=query)

    print("\nAccessible Accounts:")
    print("-" * 50)
    for row in response:
        print(f"{row.customer_client.descriptive_name}: {row.customer_client.id}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check Google Ads change history')
    parser.add_argument('customer_id', nargs='?', help='Customer ID (no dashes)')
    parser.add_argument('--start', help='Start date YYYY-MM-DD')
    parser.add_argument('--end', help='End date YYYY-MM-DD')
    parser.add_argument('--types', nargs='+', help='Resource types to filter (e.g., ASSET AD_GROUP)')
    parser.add_argument('--detailed', '-d', action='store_true', help='Show asset details')
    parser.add_argument('--list-accounts', action='store_true', help='List all accounts under MCC')
    args = parser.parse_args()

    if args.list_accounts:
        list_accounts()
    elif args.customer_id and args.start and args.end:
        check_changes(args.customer_id, args.start, args.end, args.types, args.detailed)
    else:
        parser.print_help()
