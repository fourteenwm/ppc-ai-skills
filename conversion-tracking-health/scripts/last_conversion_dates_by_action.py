"""Last Conversion Dates by Action.

This script identifies the most recent date each conversion action recorded
conversions. Helps detect broken conversion tracking or stale conversion actions.

Usage:
    # By account name (auto-discovers CID from MCC)
    python last_conversion_dates_by_action.py "Acme Plumbing"

    # By customer ID (faster — no MCC lookup)
    python last_conversion_dates_by_action.py --cid 1234567890

    # Custom lookback period (default: 90 days)
    python last_conversion_dates_by_action.py --cid 1234567890 --days 180

Features:
    - Auto-discovers customer ID from account name (via MCC lookup)
    - Queries all conversion actions configured in account
    - Finds last conversion date for each action
    - Highlights stale actions (>30 days) and never-fired actions
    - Filters out store/mobile/Google-hosted action types

Prerequisites:
    - google-ads.yaml at project root with valid OAuth credentials
    - pip install google-ads
"""

from google.ads.googleads.client import GoogleAdsClient
from datetime import datetime, timedelta
import sys
import io
import argparse
from collections import defaultdict

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def get_customer_id_from_name(account_name, ads_client):
    """Auto-discover customer ID from account name by querying MCC."""
    try:
        customer_service = ads_client.get_service("CustomerService")
        accessible_customers = customer_service.list_accessible_customers()
        ga_service = ads_client.get_service("GoogleAdsService")

        for resource_name in accessible_customers.resource_customers:
            customer_id = resource_name.split('/')[-1]
            query = f"""
                SELECT customer.id, customer.descriptive_name
                FROM customer WHERE customer.id = {customer_id}
            """
            try:
                response = ga_service.search(customer_id=customer_id, query=query)
                for row in response:
                    if account_name.lower() in row.customer.descriptive_name.lower():
                        return customer_id, row.customer.descriptive_name
            except:
                continue

    except Exception as e:
        print(f"Warning: Could not auto-discover customer ID: {e}")
        print("Please provide customer ID directly with --cid flag")
        return None, None

    return None, None


def should_ignore_conversion_type(conversion_type):
    """Filter out store visits, Google-hosted, and mobile app actions."""
    IGNORED_TYPES = [
        'STORE_VISITS', 'GOOGLE_HOSTED',
        'ANDROID_INSTALLS_ALL_OTHER_APPS', 'ANDROID_IN_APP_ACTION',
        'IOS_IN_APP_ACTION', 'IOS_FIRST_OPEN',
        'FIREBASE_ANDROID_FIRST_OPEN', 'FIREBASE_ANDROID_IN_APP_ACTION',
        'FIREBASE_IOS_FIRST_OPEN', 'FIREBASE_IOS_IN_APP_ACTION',
    ]
    return conversion_type in IGNORED_TYPES


def get_all_conversion_actions(customer_id, ads_client, include_ignored=False):
    """Query all conversion actions configured in the account."""
    ga_service = ads_client.get_service("GoogleAdsService")

    query = """
        SELECT
            conversion_action.id,
            conversion_action.name,
            conversion_action.type,
            conversion_action.status,
            conversion_action.category,
            conversion_action.include_in_conversions_metric
        FROM conversion_action
        WHERE conversion_action.status != 'REMOVED'
        ORDER BY conversion_action.name
    """

    conversion_actions = {}
    ignored_count = 0

    try:
        response = ga_service.search(customer_id=customer_id, query=query)

        for row in response:
            ca = row.conversion_action
            conversion_type = ca.type_.name

            if not include_ignored and should_ignore_conversion_type(conversion_type):
                ignored_count += 1
                continue

            conversion_actions[ca.name] = {
                'id': ca.id,
                'type': conversion_type,
                'status': ca.status.name,
                'category': ca.category.name,
                'include_in_conversions': ca.include_in_conversions_metric
            }

    except Exception as e:
        print(f"Error querying conversion actions: {e}")
        return {}, 0

    return conversion_actions, ignored_count


def get_last_conversion_dates(customer_id, ads_client, lookback_days=90):
    """Query conversion performance segmented by date and action.

    Uses metrics.all_conversions so both optimization-included and
    observation-only conversions are captured.
    """
    ga_service = ads_client.get_service("GoogleAdsService")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)
    date_from = start_date.strftime("%Y-%m-%d")
    date_to = end_date.strftime("%Y-%m-%d")

    query = f"""
        SELECT
            segments.conversion_action_name,
            segments.date,
            metrics.conversions,
            metrics.all_conversions
        FROM campaign
        WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
          AND metrics.all_conversions > 0
        ORDER BY segments.date DESC
    """

    last_dates = {}

    try:
        response = ga_service.search(customer_id=customer_id, query=query)
        for row in response:
            action_name = row.segments.conversion_action_name
            date_str = row.segments.date
            if action_name not in last_dates:
                last_dates[action_name] = {
                    'last_date': date_str,
                    'conversions': row.metrics.conversions,
                    'all_conversions': row.metrics.all_conversions
                }
    except Exception as e:
        print(f"Error querying conversion dates: {e}")
        return {}

    return last_dates


def calculate_days_ago(date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return (datetime.now() - date_obj).days


def main():
    parser = argparse.ArgumentParser(description='Find last conversion date for each conversion action')
    parser.add_argument('account_name', nargs='?', help='Account name to search for (e.g., "Acme Plumbing")')
    parser.add_argument('--cid', help='Customer ID (alternative to account name)')
    parser.add_argument('--days', type=int, default=90, help='Lookback period in days (default: 90)')
    args = parser.parse_args()

    if not args.account_name and not args.cid:
        print("Error: Must provide either account name or --cid")
        parser.print_help()
        sys.exit(1)

    try:
        ads_client = GoogleAdsClient.load_from_storage("google-ads.yaml")
    except Exception as e:
        print(f"Failed to load Google Ads client: {e}")
        sys.exit(1)

    if args.cid:
        customer_id = args.cid.replace('-', '')
        account_name = f"CID {customer_id}"
    else:
        customer_id, account_name = get_customer_id_from_name(args.account_name, ads_client)
        if not customer_id:
            print(f"Error: Could not find account matching '{args.account_name}'")
            sys.exit(1)

    print(f"\n{'='*80}")
    print(f"LAST CONVERSION DATES BY ACTION")
    print(f"{'='*80}")
    print(f"Account: {account_name}")
    print(f"Customer ID: {customer_id}")
    print(f"Lookback Period: {args.days} days")
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")

    print(f"{'-'*80}")
    print(f"STEP 1: CONFIGURED CONVERSION ACTIONS")
    print(f"{'-'*80}\n")

    conversion_actions, ignored_count = get_all_conversion_actions(customer_id, ads_client)

    if not conversion_actions and ignored_count == 0:
        print("WARNING: No conversion actions found in account!")
        sys.exit(0)

    print(f"Found {len(conversion_actions)} website conversion actions configured")
    if ignored_count > 0:
        print(f"(Filtered out {ignored_count} store/mobile/Google-hosted actions)")
    print()

    for name, details in conversion_actions.items():
        status_marker = "[OK]" if details['status'] == 'ENABLED' else "[!]"
        include_marker = "(in)" if details['include_in_conversions'] else "(obs)"
        print(f"  {status_marker} {include_marker} {name}")
        print(f"     Type: {details['type']} | Category: {details['category']} | Status: {details['status']}")

    print(f"\n(in) = Included in 'Conversions' column")
    print(f"(obs) = Observation only (not included in 'Conversions')")

    print(f"\n\n{'-'*80}")
    print(f"STEP 2: LAST CONVERSION DATES (Last {args.days} Days)")
    print(f"{'-'*80}\n")

    last_dates = get_last_conversion_dates(customer_id, ads_client, args.days)

    if not last_dates:
        print("WARNING: No conversions found in the lookback period!")
        print(f"Consider increasing the --days parameter (currently {args.days})")
        sys.exit(0)

    print(f"\n{'-'*80}")
    print(f"STEP 3: ANALYSIS - CONVERSION ACTION HEALTH")
    print(f"{'-'*80}\n")

    healthy = []
    warning = []
    stale = []
    never_fired = []

    for action_name, details in conversion_actions.items():
        if action_name in last_dates:
            last_date = last_dates[action_name]['last_date']
            days_ago = calculate_days_ago(last_date)
            entry = {
                'name': action_name, 'last_date': last_date, 'days_ago': days_ago,
                'status': details['status'], 'include_in_conversions': details['include_in_conversions']
            }
            if days_ago <= 14:
                healthy.append(entry)
            elif days_ago <= 30:
                warning.append(entry)
            else:
                stale.append(entry)
        else:
            never_fired.append({
                'name': action_name, 'status': details['status'],
                'include_in_conversions': details['include_in_conversions']
            })

    if healthy:
        print(f"HEALTHY - Last conversion within 14 days ({len(healthy)} actions)\n")
        for entry in sorted(healthy, key=lambda x: x['days_ago']):
            days_text = "today" if entry['days_ago'] == 0 else f"{entry['days_ago']} days ago"
            include_marker = "(in)" if entry['include_in_conversions'] else "(obs)"
            print(f"  - {include_marker} {entry['name']}: {entry['last_date']} ({days_text})")
        print()

    if warning:
        print(f"WARNING - Last conversion 15-30 days ago ({len(warning)} actions)\n")
        for entry in sorted(warning, key=lambda x: x['days_ago'], reverse=True):
            include_marker = "(in)" if entry['include_in_conversions'] else "(obs)"
            print(f"  - {include_marker} {entry['name']}: {entry['last_date']} ({entry['days_ago']} days ago)")
        print()

    if stale:
        print(f"STALE - Last conversion 30+ days ago ({len(stale)} actions)\n")
        for entry in sorted(stale, key=lambda x: x['days_ago'], reverse=True):
            include_marker = "(in)" if entry['include_in_conversions'] else "(obs)"
            print(f"  - {include_marker} {entry['name']}: {entry['last_date']} ({entry['days_ago']} days ago)")
            print(f"     INVESTIGATE: May indicate broken tracking or low volume")
        print()

    if never_fired:
        print(f"NO RECENT CONVERSIONS - No activity in last {args.days} days ({len(never_fired)} actions)\n")
        for entry in never_fired:
            include_marker = "(in)" if entry['include_in_conversions'] else "(obs)"
            print(f"  - {include_marker} {entry['name']} (Status: {entry['status']})")
            if entry['status'] == 'ENABLED':
                print(f"     INVESTIGATE: Enabled but no conversions recorded")
        print()

    print(f"\n{'-'*80}")
    print(f"STEP 4: SUMMARY & RECOMMENDATIONS")
    print(f"{'-'*80}\n")

    actions_with_data = len(healthy) + len(warning) + len(stale)

    print(f"Total Conversion Actions: {len(conversion_actions)}")
    print(f"Actions with Recent Data: {actions_with_data}")
    print(f"  Healthy (<=14 days): {len(healthy)}")
    print(f"  Warning (15-30 days): {len(warning)}")
    print(f"  Stale (30+ days): {len(stale)}")
    print(f"  No Recent Data: {len(never_fired)}")

    print(f"\nRECOMMENDED ACTIONS:\n")

    if stale or never_fired:
        print("HIGH PRIORITY:")
        if stale:
            print(f"  - Investigate {len(stale)} stale conversion action(s) - may indicate broken tracking")
        if never_fired:
            enabled_never_fired = [e for e in never_fired if e['status'] == 'ENABLED']
            if enabled_never_fired:
                print(f"  - Review {len(enabled_never_fired)} enabled action(s) with no conversions")
                print(f"    Consider disabling if tracking is broken, or removing if not needed")
        print()

    if warning:
        print("MEDIUM PRIORITY:")
        print(f"  - Monitor {len(warning)} conversion action(s) with declining activity")
        print()

    if healthy:
        print(f"{len(healthy)} conversion action(s) are healthy and recording conversions regularly")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
