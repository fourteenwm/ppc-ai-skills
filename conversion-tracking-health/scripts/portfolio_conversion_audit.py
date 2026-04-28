#!/usr/bin/env python3
"""Portfolio Conversion Audit.

Audits conversion tracking health across multiple Google Ads accounts.
Groups problematic conversions by severity (worst first).

Usage:
    # Audit a list of accounts from a CSV file (cid,name per row)
    python portfolio_conversion_audit.py --accounts-file accounts.csv

    # Audit specific accounts by CID (comma-separated)
    python portfolio_conversion_audit.py --cids 1234567890,2345678901

    # Single account
    python portfolio_conversion_audit.py --cid 1234567890

    # Custom lookback period (default: 90 days)
    python portfolio_conversion_audit.py --cids 1234567890 --days 180

Features:
    - Groups results by severity: No Data -> Stale -> Warning
    - Only shows problematic conversions (skips healthy ones)
    - Filters out store visit, mobile app, and Google-hosted conversions
    - Tracks only primary conversion actions (used in optimization)
    - Skips accounts with no spend in the last 7 days

Prerequisites:
    - google-ads.yaml at project root (Google Ads API credentials)
    - pip install google-ads

Accounts file format (CSV, no header):
    1234567890,Client Name A
    XXXXXXXXXX,Client Name B
"""

import argparse
import csv
import io
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta

from google.ads.googleads.client import GoogleAdsClient


# Fix Windows console encoding
if sys.platform == 'win32' and sys.stdout is not None:
    try:
        if hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'buffer') and not isinstance(sys.stderr, io.TextIOWrapper):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass


# Conversion types to ignore (store visits, mobile app installs, Google-hosted)
IGNORED_CONVERSION_TYPES = {
    'STORE_VISITS',
    'GOOGLE_HOSTED',
    'ANDROID_INSTALLS_ALL_OTHER_APPS',
    'ANDROID_IN_APP_ACTION',
    'IOS_IN_APP_ACTION',
    'IOS_FIRST_OPEN',
    'FIREBASE_ANDROID_FIRST_OPEN',
    'FIREBASE_ANDROID_IN_APP_ACTION',
    'FIREBASE_IOS_FIRST_OPEN',
    'FIREBASE_IOS_IN_APP_ACTION',
}


def should_ignore_conversion_type(conversion_type: str) -> bool:
    """Determine if a conversion action type should be ignored."""
    return conversion_type in IGNORED_CONVERSION_TYPES


def get_all_conversion_actions(customer_id: str, ads_client, include_ignored: bool = False):
    """Query all conversion actions configured in the account.

    Args:
        customer_id: Google Ads customer ID (no dashes)
        ads_client: Initialized GoogleAdsClient
        include_ignored: If False (default), filters out store/mobile/Google-hosted actions
    """
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


def get_last_conversion_dates(customer_id: str, ads_client, lookback_days: int = 90):
    """Query conversion performance to find the last date each action fired.

    Uses metrics.conversions (only primary conversion actions used in optimization).
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
            metrics.conversions
        FROM campaign
        WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
          AND metrics.conversions > 0
        ORDER BY segments.date DESC
    """

    last_dates = {}

    try:
        response = ga_service.search(customer_id=customer_id, query=query)

        for row in response:
            action_name = row.segments.conversion_action_name
            date_str = row.segments.date
            conversions = row.metrics.conversions

            # Ordered by date DESC, so first hit is most recent
            if action_name not in last_dates:
                last_dates[action_name] = {
                    'last_date': date_str,
                    'conversions': conversions
                }

    except Exception as e:
        print(f"Error querying conversion dates: {e}")
        return {}

    return last_dates


def calculate_days_ago(date_str: str) -> int:
    """Calculate days between date string (YYYY-MM-DD) and today."""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    today = datetime.now()
    delta = today - date_obj
    return delta.days


def load_accounts_file(path: str):
    """Load accounts from a CSV file (cid,name per row).

    Returns list of (customer_id, account_name) tuples.
    """
    accounts = []
    if not os.path.exists(path):
        print(f"Error: Accounts file not found: {path}")
        return accounts

    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or not row[0].strip():
                continue
            cid = row[0].strip().replace('-', '')
            name = row[1].strip() if len(row) > 1 else f"CID {cid}"
            accounts.append((cid, name))

    return accounts


def has_recent_spend(customer_id: str, ads_client, lookback_days: int = 7) -> bool:
    """Check if the account has spent anything in the last N days."""
    ga_service = ads_client.get_service("GoogleAdsService")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)
    date_from = start_date.strftime("%Y-%m-%d")
    date_to = end_date.strftime("%Y-%m-%d")

    query = f"""
        SELECT
            metrics.cost_micros
        FROM customer
        WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
    """

    try:
        response = ga_service.search(customer_id=customer_id, query=query)

        total_spend = 0
        for row in response:
            total_spend += row.metrics.cost_micros

        return total_spend > 0

    except Exception as e:
        print(f"Error checking spend for {customer_id}: {e}")
        return False


def audit_single_account(customer_id: str, account_name: str, ads_client,
                         lookback_days: int = 90, require_spend: bool = True):
    """Audit conversion health for a single account.

    Returns:
        dict with keys 'no_data', 'stale', 'warning' (each a list of conversion actions).
        Returns None if `require_spend` is True and the account has no recent spend.
    """
    results = {
        'no_data': [],
        'stale': [],
        'warning': []
    }

    try:
        if require_spend and not has_recent_spend(customer_id, ads_client, lookback_days=7):
            return None

        conversion_actions, ignored_count = get_all_conversion_actions(customer_id, ads_client)

        if not conversion_actions:
            return results

        last_dates = get_last_conversion_dates(customer_id, ads_client, lookback_days)

        for action_name, details in conversion_actions.items():
            # Only track primary conversions (included in optimization)
            if not details['include_in_conversions']:
                continue

            if action_name in last_dates:
                last_date = last_dates[action_name]['last_date']
                days_ago = calculate_days_ago(last_date)

                entry = {
                    'account_name': account_name,
                    'conversion_action': action_name,
                    'last_date': last_date,
                    'days_ago': days_ago
                }

                if days_ago <= 14:
                    # Healthy - skip
                    pass
                elif days_ago <= 30:
                    results['warning'].append(entry)
                else:
                    results['stale'].append(entry)
            else:
                if details['status'] == 'ENABLED':
                    results['no_data'].append({
                        'account_name': account_name,
                        'conversion_action': action_name,
                        'last_date': 'Never fired',
                        'days_ago': None
                    })

    except Exception as e:
        print(f"Error auditing {account_name}: {e}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Audit conversion tracking health across one or more Google Ads accounts'
    )
    parser.add_argument('--cid',
                        help='Single customer ID (no dashes)')
    parser.add_argument('--cids',
                        help='Comma-separated list of customer IDs')
    parser.add_argument('--accounts-file',
                        help='CSV file of accounts to audit (cid,name per row, no header)')
    parser.add_argument('--days', type=int, default=90,
                        help='Lookback period in days (default: 90)')
    parser.add_argument('--config', default='google-ads.yaml',
                        help='Path to google-ads.yaml (default: ./google-ads.yaml)')
    parser.add_argument('--include-no-spend', action='store_true',
                        help='Audit accounts even if they have no spend in the last 7 days')

    args = parser.parse_args()

    if not args.cid and not args.cids and not args.accounts_file:
        print("Error: must provide --cid, --cids, or --accounts-file")
        parser.print_help()
        sys.exit(1)

    try:
        ads_client = GoogleAdsClient.load_from_storage(args.config)
    except Exception as e:
        print(f"Failed to load Google Ads client from {args.config}: {e}")
        sys.exit(1)

    # Build account list
    accounts = []
    if args.accounts_file:
        accounts.extend(load_accounts_file(args.accounts_file))

    if args.cids:
        for cid in args.cids.split(','):
            cid = cid.strip().replace('-', '')
            if cid:
                accounts.append((cid, f"CID {cid}"))

    if args.cid:
        cid = args.cid.strip().replace('-', '')
        accounts.append((cid, f"CID {cid}"))

    if not accounts:
        print("Error: No accounts to audit")
        sys.exit(1)

    print(f"\n{'='*100}")
    print(f"PORTFOLIO CONVERSION AUDIT")
    print(f"{'='*100}")
    print(f"Accounts to audit: {len(accounts)}")
    print(f"Lookback period: {args.days} days")
    print(f"Analysis date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*100}\n")

    print("Auditing accounts...\n")

    all_no_data = []
    all_stale = []
    all_warning = []
    accounts_checked = 0
    accounts_skipped = 0

    for customer_id, account_name in accounts:
        results = audit_single_account(
            customer_id, account_name, ads_client, args.days,
            require_spend=not args.include_no_spend,
        )

        if results is None:
            print(f"  [skipped] {account_name} (no spend in last 7 days)")
            accounts_skipped += 1
            continue

        print(f"  [ok] {account_name}")

        all_no_data.extend(results['no_data'])
        all_stale.extend(results['stale'])
        all_warning.extend(results['warning'])
        accounts_checked += 1

    print(f"\nAudit complete. Checked {accounts_checked} accounts, skipped {accounts_skipped} (no spend).\n")

    print(f"\n{'='*100}")
    print(f"RESULTS - PROBLEMATIC CONVERSIONS ONLY")
    print(f"{'='*100}\n")

    total_issues = len(all_no_data) + len(all_stale) + len(all_warning)

    if total_issues == 0:
        print("NO ISSUES FOUND - All conversion actions are healthy.\n")
        return

    if all_no_data:
        print(f"NO RECENT CONVERSIONS ({args.days}+ days) - {len(all_no_data)} issues\n")
        print(f"{'Account Name':<50} | {'Conversion Action':<40} | {'Last Activity':<15}")
        print(f"{'-'*50} | {'-'*40} | {'-'*15}")
        for entry in all_no_data:
            account = entry['account_name'][:48]
            action = entry['conversion_action'][:38]
            last = entry['last_date']
            print(f"{account:<50} | {action:<40} | {last:<15}")
        print()

    if all_stale:
        print(f"STALE (30+ days) - {len(all_stale)} issues\n")
        print(f"{'Account Name':<50} | {'Conversion Action':<40} | {'Last Activity':<15}")
        print(f"{'-'*50} | {'-'*40} | {'-'*15}")
        for entry in sorted(all_stale, key=lambda x: x['days_ago'], reverse=True):
            account = entry['account_name'][:48]
            action = entry['conversion_action'][:38]
            last = f"{entry['days_ago']} days ago"
            print(f"{account:<50} | {action:<40} | {last:<15}")
        print()

    if all_warning:
        print(f"WARNING (15-30 days) - {len(all_warning)} issues\n")
        print(f"{'Account Name':<50} | {'Conversion Action':<40} | {'Last Activity':<15}")
        print(f"{'-'*50} | {'-'*40} | {'-'*15}")
        for entry in sorted(all_warning, key=lambda x: x['days_ago'], reverse=True):
            account = entry['account_name'][:48]
            action = entry['conversion_action'][:38]
            last = f"{entry['days_ago']} days ago"
            print(f"{account:<50} | {action:<40} | {last:<15}")
        print()

    print(f"\n{'='*100}")
    print(f"SUMMARY")
    print(f"{'='*100}\n")
    print(f"Total accounts checked: {accounts_checked}")
    print(f"Accounts skipped (no spend in 7 days): {accounts_skipped}")
    print(f"Total problematic conversions: {total_issues}")
    print(f"  No recent data:       {len(all_no_data)}")
    print(f"  Stale (30+ days):     {len(all_stale)}")
    print(f"  Warning (15-30 days): {len(all_warning)}")
    print(f"\n{'='*100}\n")


if __name__ == "__main__":
    main()
