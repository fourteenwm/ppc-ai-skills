#!/usr/bin/env python3
"""
Google Ads Query -> CSV

Queries the Google Ads API using a shipped GAQL template and saves results
to CSV. Implements the CSV-first pattern for context-efficient analysis:
data lands in a file, only the file path and row count print.

Usage:
    # Bare CID -- no other files needed beyond your credentials
    python query.py --cid 1234567890 --resource search-terms --days 30

    # Account name or alias, resolved via an optional accounts.json registry
    python query.py --account "riverside flats" --resource campaigns

Credentials:
    google-ads.yaml at project root (override with --config) -- see the
    google-ads-api-setup skill for creating it. Querying client accounts
    through a manager account requires login_customer_id in the yaml.

accounts.json (optional; default ./accounts.json, override with --accounts):
    A name->CID registry so you can say "riverside flats" instead of pasting
    CIDs. Copy accounts.example.json from this skill's folder and edit.
    Bare --cid runs never read it.

Output:
    data/YYYYMMDD-[account]-[resource].csv in the current directory
    (override with --output). Read-only: this script only ever runs
    SELECT queries; it never mutates anything.
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.util import get_nested_attr
import proto

SKILL_DIR = Path(__file__).resolve().parent.parent


def load_ads_client(config_path):
    """Load Google Ads client from yaml config."""
    if not Path(config_path).exists():
        print(f"ERROR: Credentials not found at {config_path}", file=sys.stderr)
        print("See the google-ads-api-setup skill for how to create google-ads.yaml",
              file=sys.stderr)
        sys.exit(1)
    return GoogleAdsClient.load_from_storage(str(config_path))


def normalize_cid(cid):
    """Strip dashes from a customer ID and validate it's 10 digits."""
    digits = str(cid).replace('-', '').strip()
    if not (digits.isdigit() and len(digits) == 10):
        raise ValueError(
            f"'{cid}' is not a valid customer ID (expected 10 digits, dashes ok)"
        )
    return digits


def load_accounts(accounts_path):
    """Load the optional accounts.json registry."""
    path = Path(accounts_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Accounts registry not found: {accounts_path}\n"
            "--account needs a registry mapping names to CIDs. Either:\n"
            "  - copy accounts.example.json (in this skill's folder) to "
            "accounts.json and edit, or\n"
            "  - skip the registry and pass the account's CID directly: "
            "--cid 1234567890"
        )

    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def resolve_account(accounts_data, account_query):
    """Resolve account name/alias to (key, info) via the registry."""
    query_lower = account_query.lower().strip()
    accounts = accounts_data.get('accounts', {})

    # Try exact key match first
    if query_lower in accounts:
        return query_lower, accounts[query_lower]

    # Try name/alias match
    for key, info in accounts.items():
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

    # No unique match - raise with suggestions
    if matches:
        suggestions = [f"  - {k} ({v.get('name')})" for k, v in matches[:5]]
        raise ValueError(
            f"Ambiguous account '{account_query}'. Did you mean:\n" +
            "\n".join(suggestions)
        )
    else:
        suggestions = list(accounts.keys())[:5]
        raise ValueError(
            f"Account '{account_query}' not found. Available accounts include:\n  - " +
            "\n  - ".join(suggestions)
        )


def load_gaql_template(resource):
    """Load the GAQL template shipped alongside this script."""
    template_path = SKILL_DIR / 'references' / f'{resource}.gaql'

    if not template_path.exists():
        available = sorted(p.stem for p in (SKILL_DIR / 'references').glob('*.gaql'))
        raise FileNotFoundError(
            f"No GAQL template for resource '{resource}'.\n"
            "Available resources: " + ", ".join(available)
        )

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


def execute_query(client, customer_id, query):
    """Execute GAQL query and return results as list of dicts."""
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
    parser = argparse.ArgumentParser(
        description='Query Google Ads and save to CSV (read-only)')
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument('--cid',
                        help='Customer ID to query (10 digits, dashes ok)')
    target.add_argument('--account',
                        help='Account name or alias, resolved via the accounts.json registry')
    parser.add_argument('--resource', required=True,
                        help='Resource type (e.g. search-terms; see references/resources.md)')
    parser.add_argument('--days', type=int, default=30,
                        help='Number of days to query (default: 30)')
    parser.add_argument('--output',
                        help='Output CSV path (default: data/YYYYMMDD-[account]-[resource].csv)')
    parser.add_argument('--config', default='google-ads.yaml',
                        help='Path to google-ads.yaml (default: ./google-ads.yaml)')
    parser.add_argument('--accounts', default='accounts.json',
                        help='Path to accounts.json registry (default: ./accounts.json; '
                             'only read when --account is used)')

    args = parser.parse_args()

    try:
        # Resolve the target account to a CID + filename slug
        if args.cid:
            customer_id = normalize_cid(args.cid)
            account_slug = customer_id
        else:
            accounts_data = load_accounts(args.accounts)
            account_key, account_info = resolve_account(accounts_data, args.account)
            customer_id = normalize_cid(account_info['id'])
            account_slug = account_key

        # Load GAQL template and substitute the date range
        gaql_template = load_gaql_template(args.resource)
        start_date, end_date = calculate_date_range(args.days)
        gaql = gaql_template.replace(
            '{DATE_RANGE}', f"BETWEEN '{start_date}' AND '{end_date}'")

        # Generate output path if not specified
        if args.output:
            output_path = Path(args.output)
        else:
            date_str = datetime.now().strftime('%Y%m%d')
            output_path = Path('data') / f'{date_str}-{account_slug}-{args.resource}.csv'

        # Execute query (read-only SELECT)
        client = load_ads_client(args.config)
        results = execute_query(client, customer_id, gaql)

        # Save to CSV
        row_count = save_to_csv(results, output_path)

        # Output minimal info (for context efficiency)
        if row_count == 0:
            print("Rows: 0 (no file written - query returned nothing; "
                  "try a longer --days window)")
            return

        try:
            display_path = output_path.relative_to(Path.cwd())
        except ValueError:
            display_path = output_path
        print(f"File: {display_path}")
        print(f"Rows: {row_count}")

    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except GoogleAdsException as ex:
        print("ERROR: Google Ads API error:", file=sys.stderr)
        for error in ex.failure.errors:
            print(f"  - {error.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
