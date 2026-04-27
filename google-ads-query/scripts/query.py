#!/usr/bin/env python3
"""
Unified Google Ads Query Script

Queries Google Ads API and saves results to CSV.
Implements the CSV-first pattern for context-efficient analysis.

Usage:
    python query.py --profile agency_1 --account example-account --resource search-terms --days 30

Output:
    Saves CSV to data/google-ads/[profile]/YYYYMMDD-[account]-[resource].csv
    Prints only file path and row count (minimal context usage)
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.util import get_nested_attr
import proto


def get_project_root():
    """Get the PPC Power project root directory."""
    # Script is at .claude/skills/google-ads-query/scripts/query.py
    return Path(__file__).parent.parent.parent.parent.parent


def load_accounts(profile):
    """Load accounts.json for the specified profile."""
    root = get_project_root()
    accounts_path = root / 'credentials' / profile / 'accounts.json'

    if not accounts_path.exists():
        raise FileNotFoundError(f"Accounts file not found: {accounts_path}")

    with open(accounts_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data


def resolve_account(accounts_data, account_query):
    """Resolve account name/alias to account info."""
    query_lower = account_query.lower().strip()
    accounts = accounts_data.get('accounts', {})

    # Try exact key match first
    if query_lower in accounts:
        return query_lower, accounts[query_lower]

    # Try alias match
    for key, info in accounts.items():
        if query_lower == key:
            return key, info
        if query_lower == info.get('name', '').lower():
            return key, info
        if query_lower in [a.lower() for a in info.get('aliases', [])]:
            return key, info

    # Try partial match
    matches = []
    for key, info in accounts.items():
        name = info.get('name', '').lower()
        if query_lower in key or query_lower in name:
            matches.append((key, info))

    if len(matches) == 1:
        return matches[0]

    # No match found - raise with suggestions
    if matches:
        suggestions = [f"  - {k} ({v.get('name')})" for k, v in matches[:5]]
        raise ValueError(
            f"Ambiguous account '{account_query}'. Did you mean:\n" +
            "\n".join(suggestions)
        )
    else:
        # Show first 5 accounts as suggestions
        suggestions = list(accounts.keys())[:5]
        raise ValueError(
            f"Account '{account_query}' not found. Available accounts include:\n  - " +
            "\n  - ".join(suggestions)
        )


def load_gaql_template(resource):
    """Load GAQL template for the specified resource."""
    root = get_project_root()
    template_path = root / '.claude' / 'skills' / 'google-ads-query' / 'references' / f'{resource}.gaql'

    if not template_path.exists():
        raise FileNotFoundError(f"GAQL template not found: {template_path}")

    return template_path.read_text(encoding='utf-8')


def calculate_date_range(days):
    """Calculate date range for GAQL WHERE clause."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    return (
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )


def format_value(value):
    """Format a value from Google Ads API response."""
    if isinstance(value, proto.Message):
        return proto.Message.to_dict(value)
    elif isinstance(value, proto.Enum):
        return value.name
    else:
        return value


def execute_query(credentials_path, customer_id, mcc_id, query):
    """Execute GAQL query and return results as list of dicts."""
    client = GoogleAdsClient.load_from_storage(credentials_path)
    ga_service = client.get_service("GoogleAdsService")

    # Add PARAMETERS to omit unselected resource names
    if "PARAMETERS" not in query:
        query = query.strip()
        if not query.endswith(';'):
            query += " PARAMETERS omit_unselected_resource_names=true"

    # Use search_stream for better handling
    response = ga_service.search_stream(
        customer_id=str(customer_id),
        query=query
    )

    output = []
    for batch in response:
        for row in batch.results:
            # Use field_mask to extract only the requested fields
            row_dict = {
                field_path: format_value(get_nested_attr(row, field_path))
                for field_path in batch.field_mask.paths
            }
            output.append(row_dict)

    return output


def flatten_nested_dict(d, parent_key='', sep='.'):
    """Flatten nested dictionaries into dot-notation keys."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_nested_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def save_to_csv(results, output_path):
    """Save query results to CSV file."""
    if not results:
        return 0

    # Flatten any nested dicts in the results
    rows = []
    headers = set()

    for row_dict in results:
        flat = flatten_nested_dict(row_dict)
        rows.append(flat)
        headers.update(flat.keys())

    # Sort headers for consistent column order
    headers = sorted(list(headers))

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def main():
    parser = argparse.ArgumentParser(description='Query Google Ads and save to CSV')
    parser.add_argument('--profile', required=True, help='Profile name (e.g. agency_1 or agency_2)')
    parser.add_argument('--account', required=True, help='Account name or alias')
    parser.add_argument('--resource', required=True, help='Resource type (e.g., search-terms)')
    parser.add_argument('--days', type=int, default=30, help='Number of days (default: 30)')
    parser.add_argument('--output', help='Output file path (auto-generated if not specified)')

    args = parser.parse_args()

    root = get_project_root()

    try:
        # Load credentials
        credentials_path = root / 'credentials' / args.profile / 'google-ads.yaml'
        if not credentials_path.exists():
            print(f"ERROR: Credentials not found: {credentials_path}", file=sys.stderr)
            sys.exit(1)

        # Load accounts
        accounts_data = load_accounts(args.profile)
        mcc_id = accounts_data.get('_meta', {}).get('mcc_id')

        # Resolve account
        account_key, account_info = resolve_account(accounts_data, args.account)
        customer_id = account_info['id']

        # Load GAQL template
        gaql_template = load_gaql_template(args.resource)

        # Calculate date range and substitute
        start_date, end_date = calculate_date_range(args.days)
        gaql = gaql_template.replace('{DATE_RANGE}', f"BETWEEN '{start_date}' AND '{end_date}'")

        # Generate output path if not specified
        if args.output:
            output_path = Path(args.output)
        else:
            date_str = datetime.now().strftime('%Y%m%d')
            output_path = root / 'data' / 'google-ads' / args.profile / f'{date_str}-{account_key}-{args.resource}.csv'

        # Execute query (returns list of dicts)
        results = execute_query(str(credentials_path), customer_id, mcc_id, gaql)

        # Save to CSV
        row_count = save_to_csv(results, output_path)

        # Output minimal info (for context efficiency)
        rel_path = output_path.relative_to(root)
        print(f"File: {rel_path}")
        print(f"Rows: {row_count}")

    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except GoogleAdsException as ex:
        print(f"ERROR: Google Ads API error:", file=sys.stderr)
        for error in ex.failure.errors:
            print(f"  - {error.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
