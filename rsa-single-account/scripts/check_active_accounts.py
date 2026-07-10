#!/usr/bin/env python3
"""
Check Active Accounts (Step 1 of the rsa-single-account skill)

Lists client accounts with spend this month so an account name can be
resolved to a Customer ID (CID). "Active" = ENABLED, non-manager, and
cost > $0 month-to-date.

Account source (first match wins):
    1. --accounts accounts.json — a registry file (same schema as the
       ads-checker skill; see below)
    2. MCC walk — every ENABLED non-manager account under the
       login_customer_id in your google-ads.yaml

Usage:
    python check_active_accounts.py
    python check_active_accounts.py --name "example"        # filter by name substring
    python check_active_accounts.py --accounts accounts.json
    python check_active_accounts.py --exclude 1234567891,0987654321

accounts.json format (optional):
    {
      "accounts": {
        "example-auto": {
          "id": "1234567890",
          "name": "Example Auto Repair",
          "portfolio": "default"
        }
      }
    }

Prerequisites:
    - google-ads.yaml at project root (see the google-ads-api-setup skill),
      with login_customer_id set to your MCC for registry-less runs
    - pip install google-ads
"""

import argparse
import io
import json
import sys

import yaml
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


def get_login_customer_id(config_path):
    """Read login_customer_id (your MCC) from google-ads.yaml."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        login_cid = str(config.get('login_customer_id', '') or '').replace('-', '').strip()
        return login_cid or None
    except Exception:
        return None


def load_accounts_registry(path):
    """Load an optional accounts.json registry → [(cid, name), ...]."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {path}: {e}")
        sys.exit(1)

    accounts = []
    for slug, entry in (data.get('accounts') or {}).items():
        cid = str(entry.get('id', '')).replace('-', '').strip()
        name = entry.get('name') or slug
        if cid:
            accounts.append((cid, name))
    return accounts or None


def get_mcc_accounts(service, login_customer_id):
    """Walk the MCC's customer_client resource → [(cid, name), ...]."""
    query = '''
        SELECT
            customer_client.id,
            customer_client.descriptive_name
        FROM customer_client
        WHERE customer_client.status = 'ENABLED'
          AND customer_client.manager = FALSE
    '''
    response = service.search(customer_id=login_customer_id, query=query)
    return [(str(row.customer_client.id), row.customer_client.descriptive_name)
            for row in response]


def main():
    parser = argparse.ArgumentParser(
        description='List accounts with spend this month (name ↔ CID resolution)'
    )
    parser.add_argument('--config', default='google-ads.yaml',
                        help='Path to google-ads.yaml (default: ./google-ads.yaml)')
    parser.add_argument('--accounts', default='accounts.json',
                        help='Optional accounts.json registry (default: ./accounts.json; '
                             'falls back to an MCC walk if absent)')
    parser.add_argument('--name',
                        help='Only show accounts whose name contains this substring '
                             '(case-insensitive)')
    parser.add_argument('--exclude',
                        help='Comma-separated CIDs to skip (e.g. non-target verticals '
                             'living under the same MCC)')
    args = parser.parse_args()

    client = load_google_ads_client(args.config)
    service = client.get_service('GoogleAdsService')

    excluded_cids = set()
    if args.exclude:
        excluded_cids = {c.strip().replace('-', '') for c in args.exclude.split(',') if c.strip()}

    # Resolve the account list: registry first, MCC walk otherwise
    accounts = load_accounts_registry(args.accounts)
    if accounts:
        print(f'Using account registry: {args.accounts}')
    else:
        login_customer_id = get_login_customer_id(args.config)
        if not login_customer_id:
            print(f"Error: no registry at {args.accounts} and no login_customer_id "
                  f"in {args.config}.")
            print("Provide an accounts.json, or set login_customer_id (your MCC) "
                  "in google-ads.yaml.")
            sys.exit(1)
        print(f'Walking MCC {login_customer_id}...')
        try:
            accounts = get_mcc_accounts(service, login_customer_id)
        except Exception as e:
            print(f'Error walking MCC {login_customer_id}: {e}')
            sys.exit(1)

    if args.name:
        needle = args.name.lower()
        accounts = [(cid, name) for cid, name in accounts if needle in (name or '').lower()]

    print(f'Checking MTD spend for {len(accounts)} accounts...\n')

    spend_query = '''
        SELECT
            customer.descriptive_name,
            metrics.cost_micros
        FROM customer
        WHERE segments.date DURING THIS_MONTH
    '''

    active_accounts = []
    excluded_count = 0

    for account_id, account_name in accounts:
        if account_id in excluded_cids:
            excluded_count += 1
            print(f'{account_id}: {account_name} - EXCLUDED')
            continue

        try:
            response = service.search(customer_id=account_id, query=spend_query)
            for row in response:
                spend = row.metrics.cost_micros / 1_000_000
                if spend > 0:
                    active_accounts.append((account_id, account_name, spend))
                    print(f'{account_id}: {account_name} - ${spend:,.2f}')
        except Exception:
            print(f'{account_id}: {account_name} - Error')

    print(f'\n{"=" * 80}')
    print(f'Total accounts checked: {len(accounts)}')
    if excluded_count > 0:
        print(f'Excluded accounts: {excluded_count}')
    print(f'Accounts with spend this month: {len(active_accounts)}')
    print(f'{"=" * 80}')

    # Output list for use in batch processing
    if active_accounts:
        print('\nActive account IDs (for batch processing):')
        for account_id, account_name, spend in active_accounts:
            print(f'{account_id}  # {account_name} - ${spend:,.2f}')


if __name__ == '__main__':
    main()
