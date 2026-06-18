#!/usr/bin/env python3
"""MCC Search Query Report — pull search terms across an MCC into a Google Sheet.

Pulls search terms (clicks > 0, last N days) for accounts under your MCC and
writes them to the "SQR" tab of your Google Sheet. This is step 0 of the
sqr-pipeline (or use your own scheduled Google Ads Script instead).

Account selection (pick one):
  (default)   All ENABLED, non-manager accounts under the MCC
  --labels    Comma-separated label names (accounts must have ALL of them)
  --cids      Comma-separated customer IDs

Options:
  --clear     Clear the SQR tab before writing (default: append/overwrite in place)
  --dry-run   Show matching accounts without querying or writing
  --days N    Lookback period (default: 30)
  --mcc-id    MCC customer ID (default: login_customer_id from google-ads.yaml)

Usage:
    python mcc_search_query_report.py --sheet-id YOUR_SHEET_ID
    python mcc_search_query_report.py --sheet-id YOUR_SHEET_ID --labels "Search,Active"
    python mcc_search_query_report.py --sheet-id YOUR_SHEET_ID --cids 1234567890,2345678901
    python mcc_search_query_report.py --sheet-id YOUR_SHEET_ID --clear

Prerequisites:
    - google-ads.yaml at project root (Google Ads API credentials, with
      login_customer_id set to your MCC) — see google-ads-api-setup skill
    - token.json at project root with the Sheets scope OR a google-ads.yaml
      refresh token that includes the spreadsheets scope (tried in that order)
    - pip install google-ads google-auth google-api-python-client pyyaml
"""

import sys
import io
import os
import json
import argparse
from datetime import datetime, timedelta
from collections import defaultdict

from google.ads.googleads.client import GoogleAdsClient
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import yaml

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SQR_TAB_DEFAULT = "SQR"
HEADERS = ["Account ID", "Account Name", "Query", "Clicks", "Impressions", "Cost", "Conversions"]


# --- Auth helpers ---

def get_sheets_service(sheets_token_path, ads_config_path):
    """Build authenticated Google Sheets API service.

    Prefers token.json (OAuth with the spreadsheets scope); falls back to the
    refresh token in google-ads.yaml if it carries the spreadsheets scope.
    """
    if os.path.exists(sheets_token_path):
        with open(sheets_token_path, 'r', encoding='utf-8') as f:
            token_data = json.load(f)
        credentials = Credentials(
            token=token_data.get('token') or token_data.get('access_token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data.get('token_uri', "https://oauth2.googleapis.com/token"),
            client_id=token_data.get('client_id'),
            client_secret=token_data.get('client_secret'),
            scopes=token_data.get('scopes', ["https://www.googleapis.com/auth/spreadsheets"]),
        )
    elif os.path.exists(ads_config_path):
        with open(ads_config_path, 'r', encoding='utf-8') as f:
            ads_config = yaml.safe_load(f)
        credentials = Credentials(
            token=None,
            refresh_token=ads_config.get('refresh_token'),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=ads_config.get('client_id'),
            client_secret=ads_config.get('client_secret'),
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
    else:
        print("ERROR: Cannot authenticate to Sheets.")
        print(f"  Neither {sheets_token_path} nor {ads_config_path} exists.")
        print("  See google-ads-api-setup skill for credential setup.")
        sys.exit(1)
    return build('sheets', 'v4', credentials=credentials)


# --- Sheet helpers ---

def ensure_headers(sheets_service, sheet_id, tab):
    """Ensure the SQR tab exists and has the correct headers."""
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id, range=f"{tab}!A1:G1",
        ).execute()
        current = result.get('values', [[]])[0]
        if current != HEADERS:
            print("  Headers missing or incorrect - resetting row 1")
            sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id, range=f"{tab}!A1:G1",
                valueInputOption="RAW", body={"values": [HEADERS]},
            ).execute()
    except Exception:
        print(f"  Creating '{tab}' tab with headers")
        sheets_service.spreadsheets().values().append(
            spreadsheetId=sheet_id, range=f"{tab}!A1",
            valueInputOption="RAW", body={"values": [HEADERS]},
        ).execute()


def clear_sqr_data(sheets_service, sheet_id, tab):
    """Clear all data rows in the SQR tab (keep headers)."""
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id, range=f"{tab}!A:A",
        ).execute()
        rows = result.get('values', [])
        if len(rows) > 1:
            sheets_service.spreadsheets().values().clear(
                spreadsheetId=sheet_id, range=f"{tab}!A2:G{len(rows)}",
            ).execute()
            print(f"  Cleared {len(rows) - 1} existing rows")
    except Exception as e:
        print(f"  Warning: Could not clear sheet ({e})")


def write_rows_to_sheet(sheets_service, sheet_id, tab, rows, start_row=2):
    """Write data rows to the SQR tab starting at a specific row (default: row 2)."""
    if not rows:
        return
    end_row = start_row + len(rows) - 1
    sheets_service.spreadsheets().values().update(
        spreadsheetId=sheet_id, range=f"{tab}!A{start_row}:G{end_row}",
        valueInputOption="RAW", body={"values": rows},
    ).execute()


# --- Account resolution ---

def find_label_ids(ga_service, mcc_id, label_names):
    """Find label IDs by name at the MCC level. Returns {label_name: label_id}."""
    query = "SELECT label.id, label.name FROM label"
    response = ga_service.search(customer_id=mcc_id, query=query)
    all_labels = {row.label.name: str(row.label.id) for row in response}
    found = {}
    for name in label_names:
        if name in all_labels:
            found[name] = all_labels[name]
        else:
            print(f"  WARNING: Label '{name}' not found in MCC")
            print(f"  Available labels: {', '.join(sorted(all_labels.keys()))}")
    return found


def get_labeled_accounts(ga_service, mcc_id, label_names):
    """Get accounts that have ALL specified labels. Returns [(cid, name), ...]."""
    label_ids = find_label_ids(ga_service, mcc_id, label_names)
    if len(label_ids) != len(label_names):
        missing = set(label_names) - set(label_ids.keys())
        print(f"  ERROR: Missing labels: {missing}")
        return []

    label_account_sets = []
    for label_name, label_id in label_ids.items():
        label_resource = f"customers/{mcc_id}/labels/{label_id}"
        query = f"""
            SELECT customer_client.id, customer_client.descriptive_name
            FROM customer_client
            WHERE customer_client.status = 'ENABLED'
              AND customer_client.manager = FALSE
              AND customer_client.applied_labels CONTAINS ANY ('{label_resource}')
        """
        response = ga_service.search(customer_id=mcc_id, query=query)
        accounts = {str(row.customer_client.id): row.customer_client.descriptive_name
                    for row in response}
        label_account_sets.append(accounts)
        print(f"  Label '{label_name}': {len(accounts)} accounts")

    if not label_account_sets:
        return []
    common_cids = set(label_account_sets[0].keys())
    for account_set in label_account_sets[1:]:
        common_cids &= set(account_set.keys())
    name_map = label_account_sets[0]
    return [(cid, name_map[cid]) for cid in sorted(common_cids)]


def get_all_enabled_accounts(ga_service, mcc_id):
    """Get all ENABLED, non-manager accounts under the MCC. Returns [(cid, name), ...]."""
    query = """
        SELECT customer_client.id, customer_client.descriptive_name
        FROM customer_client
        WHERE customer_client.status = 'ENABLED'
          AND customer_client.manager = FALSE
    """
    response = ga_service.search(customer_id=mcc_id, query=query)
    accounts = {str(row.customer_client.id): row.customer_client.descriptive_name
                for row in response}
    return [(cid, accounts[cid]) for cid in sorted(accounts.keys())]


# --- Search term query ---

def query_search_terms(ga_service, customer_id, days=30):
    """Query search terms for one account, aggregated per term."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    date_from = start_date.strftime("%Y-%m-%d")
    date_to = end_date.strftime("%Y-%m-%d")

    query = f"""
        SELECT
            search_term_view.search_term,
            metrics.clicks,
            metrics.impressions,
            metrics.cost_micros,
            metrics.conversions
        FROM search_term_view
        WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
          AND metrics.clicks > 0
    """

    aggregated = defaultdict(lambda: {
        'clicks': 0, 'impressions': 0, 'cost_micros': 0, 'conversions': 0.0
    })
    response = ga_service.search(customer_id=customer_id, query=query)
    for row in response:
        term = row.search_term_view.search_term
        aggregated[term]['clicks'] += row.metrics.clicks
        aggregated[term]['impressions'] += row.metrics.impressions
        aggregated[term]['cost_micros'] += row.metrics.cost_micros
        aggregated[term]['conversions'] += row.metrics.conversions

    results = []
    for term, metrics in sorted(aggregated.items()):
        results.append([
            term,
            metrics['clicks'],
            metrics['impressions'],
            round(metrics['cost_micros'] / 1_000_000, 2),
            round(metrics['conversions'], 2),
        ])
    return results


# --- Main ---

def main():
    parser = argparse.ArgumentParser(
        description='MCC Search Query Report - pull search terms to a Google Sheet')
    parser.add_argument('--sheet-id', required=True,
                        help='Google Sheet ID to write the SQR tab')
    parser.add_argument('--tab-name', default=SQR_TAB_DEFAULT,
                        help=f'Output tab name (default: "{SQR_TAB_DEFAULT}")')
    parser.add_argument('--config', default='google-ads.yaml',
                        help='Google Ads credentials YAML (default: ./google-ads.yaml)')
    parser.add_argument('--sheets-token', default='token.json',
                        help='Google Sheets OAuth token JSON (default: ./token.json). '
                             'Falls back to credentials in --config if not found.')
    parser.add_argument('--mcc-id', default=None,
                        help='MCC customer ID (default: login_customer_id from the YAML)')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--labels', help='Comma-separated label names (accounts need ALL)')
    group.add_argument('--cids', help='Comma-separated customer IDs')

    parser.add_argument('--clear', action='store_true',
                        help='Clear the SQR tab before writing (default: write in place)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show matching accounts without querying or writing')
    parser.add_argument('--days', type=int, default=30,
                        help='Lookback period in days (default: 30)')
    args = parser.parse_args()

    print(f"\n{'='*80}")
    print("MCC SEARCH QUERY REPORT")
    print(f"{'='*80}")
    print(f"Lookback: {args.days} days")

    if not os.path.exists(args.config):
        print(f"\nERROR: Google Ads credentials not found at {args.config}")
        print("See google-ads-api-setup skill for setup.")
        sys.exit(1)

    print("\nInitializing...")
    ads_client = GoogleAdsClient.load_from_storage(args.config)
    ga_service = ads_client.get_service("GoogleAdsService")
    sheets_service = get_sheets_service(args.sheets_token, args.config)

    mcc_id = args.mcc_id or getattr(ads_client, "login_customer_id", None)
    if not mcc_id:
        print("\nERROR: No MCC ID. Set login_customer_id in google-ads.yaml or pass --mcc-id.")
        sys.exit(1)
    mcc_id = str(mcc_id).replace('-', '')

    # Resolve accounts
    print("\nResolving accounts...")
    if args.cids:
        accounts = [(cid.strip(), f"CID {cid.strip()}") for cid in args.cids.split(',')]
        print(f"  Mode: Direct CIDs ({len(accounts)} accounts)")
    elif args.labels:
        label_names = [l.strip() for l in args.labels.split(',')]
        print(f"  Mode: Labels {label_names}")
        accounts = get_labeled_accounts(ga_service, mcc_id, label_names)
    else:
        print(f"  Mode: All ENABLED non-manager accounts under MCC {mcc_id}")
        accounts = get_all_enabled_accounts(ga_service, mcc_id)

    if not accounts:
        print("\n  No matching accounts found.")
        sys.exit(1)

    print(f"\n  Matched {len(accounts)} accounts:")
    for cid, name in accounts[:25]:
        print(f"    - {name} ({cid})")
    if len(accounts) > 25:
        print(f"    ... and {len(accounts) - 25} more")

    if args.dry_run:
        print(f"\n  (dry run - no queries or writes)")
        print(f"{'='*80}\n")
        return

    print("\nPreparing sheet...")
    ensure_headers(sheets_service, args.sheet_id, args.tab_name)
    if args.clear:
        clear_sqr_data(sheets_service, args.sheet_id, args.tab_name)

    print("\nQuerying search terms...")
    all_rows = []
    for i, (cid, name) in enumerate(accounts, 1):
        try:
            terms = query_search_terms(ga_service, cid, days=args.days)
            account_rows = [[cid, name] + row for row in terms]
            all_rows.extend(account_rows)
            print(f"  [{i}/{len(accounts)}] {name}: {len(terms)} search terms")
        except Exception as e:
            print(f"  [{i}/{len(accounts)}] {name}: ERROR - {e}")

    if all_rows:
        print(f"\nWriting {len(all_rows)} rows to sheet...")
        BATCH_SIZE = 5000
        for batch_start in range(0, len(all_rows), BATCH_SIZE):
            batch = all_rows[batch_start:batch_start + BATCH_SIZE]
            sheet_start_row = 2 + batch_start
            write_rows_to_sheet(sheets_service, args.sheet_id, args.tab_name,
                                batch, start_row=sheet_start_row)
            if len(all_rows) > BATCH_SIZE:
                print(f"  Wrote batch {batch_start // BATCH_SIZE + 1} ({len(batch)} rows)")
        print(f"  Done! {len(all_rows)} total rows written.")
    else:
        print("\n  No search term data found across any accounts.")

    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Accounts processed: {len(accounts)}")
    print(f"Total search terms: {len(all_rows)}")
    print(f"Tab: {args.tab_name}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
