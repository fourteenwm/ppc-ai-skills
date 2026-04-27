#!/usr/bin/env python3
"""Non-Serving Keyword Scanner.

Scans Google Ads accounts for keywords with 0 impressions over a threshold period
(default 180 days) and writes a report to a Google Sheet for human review.

Human-in-the-loop by design: generates a report only, never auto-pauses.

Usage:
    # Scan all accounts listed in accounts.md (expects file at ./accounts.md)
    python non_serving_keyword_scan.py --sheet-id YOUR_SHEET_ID

    # Scan a single account by CID
    python non_serving_keyword_scan.py --cid 1234567890 --sheet-id YOUR_SHEET_ID

    # Scan multiple accounts (comma-separated CIDs)
    python non_serving_keyword_scan.py --cids "1234567890,2345678901" --sheet-id YOUR_SHEET_ID

    # Scan all accounts under the MCC (walks customer_client resource)
    python non_serving_keyword_scan.py --all --sheet-id YOUR_SHEET_ID

    # Custom threshold and tab name
    python non_serving_keyword_scan.py --sheet-id YOUR_SHEET_ID --days 90 --tab-name "Dead Keywords 90d"

    # Different accounts.md location
    python non_serving_keyword_scan.py --accounts /path/to/my/accounts.md --sheet-id YOUR_SHEET_ID

Prerequisites:
    - google-ads.yaml at project root (Google Ads API + Sheets scopes on the refresh token)
    - accounts.md at project root if using default scan-all mode (see accounts.md format below)
    - pip install google-ads gspread google-auth pyyaml

accounts.md format:
    ### CID: 123-456-7890
    - Account Name (first line is used as display name)
    - Alias (optional additional names under same CID)

    ### CID: 234-567-8901
    - Another Account Name
"""

import argparse
import os
import re
import sys
import io
from datetime import datetime, timedelta
from pathlib import Path

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
import gspread
from google.oauth2.credentials import Credentials
import yaml

# Windows console fix
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Ad groups to exclude (case-insensitive) — typically dynamic pricing ad groups
# where keywords cycle in and out of the account regularly.
EXCLUDED_AD_GROUPS = ["special", "specials"]


def parse_accounts_file(accounts_path: Path) -> list[tuple[str, str]]:
    """Parse accounts.md to extract CIDs and their associated account names.

    Returns:
        List of tuples (cid_without_dashes, first_account_name) for each unique CID
    """
    if not accounts_path.exists():
        raise FileNotFoundError(f"Accounts file not found: {accounts_path}")

    content = accounts_path.read_text(encoding="utf-8")

    # Pattern to match CID headers: ### CID: 123-456-7890
    cid_pattern = re.compile(r"### CID: (\d{3}-\d{3}-\d{4})")

    # Pattern to match account names (lines starting with "- ")
    account_pattern = re.compile(r"^- (.+)$", re.MULTILINE)

    accounts = []
    current_cid = None
    current_accounts = []

    for line in content.split("\n"):
        cid_match = cid_pattern.search(line)
        if cid_match:
            if current_cid and current_accounts:
                accounts.append((current_cid.replace("-", ""), current_accounts[0]))
            current_cid = cid_match.group(1)
            current_accounts = []

        account_match = account_pattern.match(line)
        if account_match and current_cid:
            current_accounts.append(account_match.group(1))

    if current_cid and current_accounts:
        accounts.append((current_cid.replace("-", ""), current_accounts[0]))

    return accounts


def get_mcc_accounts(client: GoogleAdsClient, login_customer_id: str) -> list[tuple[str, str]]:
    """Walk the MCC's customer_client resource to get all active accounts.

    Returns:
        List of (cid_without_dashes, descriptive_name) tuples
    """
    ga_service = client.get_service("GoogleAdsService")
    query = """
        SELECT
            customer_client.client_customer,
            customer_client.descriptive_name,
            customer_client.id,
            customer_client.status,
            customer_client.manager
        FROM customer_client
        WHERE customer_client.status = 'ENABLED'
          AND customer_client.manager = FALSE
    """

    accounts = []
    try:
        response = ga_service.search(customer_id=login_customer_id, query=query)
        for row in response:
            cid = str(row.customer_client.id)
            name = row.customer_client.descriptive_name or f"Account {cid}"
            accounts.append((cid, name))
    except GoogleAdsException as ex:
        error_msg = ex.failure.errors[0].message if ex.failure.errors else str(ex)
        print(f"MCC traversal error: {error_msg}")
        sys.exit(1)

    return accounts


def get_sheets_client(config_path: str) -> gspread.Client:
    """Create gspread client using OAuth credentials from google-ads.yaml.

    Requires the refresh token in google-ads.yaml to include these scopes:
        - https://www.googleapis.com/auth/spreadsheets
        - https://www.googleapis.com/auth/drive.readonly
    """
    with open(config_path, "r", encoding="utf-8") as f:
        ads_config = yaml.safe_load(f)

    credentials = Credentials(
        token=None,
        refresh_token=ads_config.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=ads_config.get("client_id"),
        client_secret=ads_config.get("client_secret"),
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.readonly",
        ],
    )

    return gspread.authorize(credentials)


def scan_account_keywords(
    client: GoogleAdsClient,
    customer_id: str,
    account_name: str,
    days: int,
) -> list[dict]:
    """Scan a single account for non-serving keywords."""
    ga_service = client.get_service("GoogleAdsService")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    date_from = start_date.strftime("%Y-%m-%d")
    date_to = end_date.strftime("%Y-%m-%d")

    query = f"""
        SELECT
            customer.descriptive_name,
            campaign.name,
            ad_group.name,
            ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type,
            ad_group_criterion.criterion_id,
            metrics.impressions,
            metrics.clicks,
            metrics.conversions,
            metrics.cost_micros
        FROM keyword_view
        WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
          AND ad_group_criterion.status = 'ENABLED'
          AND ad_group.status = 'ENABLED'
          AND campaign.status = 'ENABLED'
          AND campaign.advertising_channel_type = 'SEARCH'
          AND metrics.impressions = 0
    """

    results = []

    try:
        response = ga_service.search_stream(customer_id=customer_id, query=query)

        for batch in response:
            for row in batch.results:
                ad_group_name = row.ad_group.name

                if ad_group_name.lower() in EXCLUDED_AD_GROUPS:
                    continue

                results.append({
                    "account_name": row.customer.descriptive_name or account_name,
                    "cid": customer_id,
                    "campaign": row.campaign.name,
                    "ad_group": ad_group_name,
                    "keyword": row.ad_group_criterion.keyword.text,
                    "match_type": row.ad_group_criterion.keyword.match_type.name,
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "conversions": row.metrics.conversions,
                    "cost": row.metrics.cost_micros / 1_000_000,
                })

    except GoogleAdsException as ex:
        error_msg = ex.failure.errors[0].message if ex.failure.errors else str(ex)
        print(f"API Error: {error_msg}")
        return []

    return results


def write_to_sheet(
    sheets_client: gspread.Client,
    spreadsheet_id: str,
    tab_name: str,
    data: list[dict],
    days: int,
):
    """Write results to Google Sheet."""
    spreadsheet = sheets_client.open_by_key(spreadsheet_id)

    try:
        worksheet = spreadsheet.worksheet(tab_name)
        worksheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=15)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    headers = [
        "Account Name", "CID", "Campaign", "Ad Group", "Keyword",
        "Match Type", f"Impressions ({days}d)", "Clicks", "Conversions", "Cost"
    ]

    rows = [headers]
    for item in data:
        rows.append([
            item["account_name"],
            item["cid"],
            item["campaign"],
            item["ad_group"],
            item["keyword"],
            item["match_type"],
            item["impressions"],
            item["clicks"],
            item["conversions"],
            f"${item['cost']:.2f}",
        ])

    if rows:
        worksheet.update(values=rows, range_name=f"A1:J{len(rows)}")

    worksheet.update(values=[[f"Last Scan: {timestamp}"]], range_name="L1")

    return worksheet.url


def load_ads_client(config_path: str) -> GoogleAdsClient:
    """Load Google Ads client from yaml config."""
    if not os.path.exists(config_path):
        print(f"ERROR: Credentials not found at {config_path}")
        print("See the google-ads-api-setup skill for how to create google-ads.yaml")
        sys.exit(1)
    return GoogleAdsClient.load_from_storage(config_path)


def main():
    parser = argparse.ArgumentParser(
        description='Scan Google Ads accounts for keywords with 0 impressions over a threshold period.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Account selection (mutually exclusive)
    account_group = parser.add_mutually_exclusive_group()
    account_group.add_argument('--cid', help='Single account CID (digits only)')
    account_group.add_argument('--cids', help='Comma-separated list of CIDs')
    account_group.add_argument('--all', action='store_true',
                               help='Scan all enabled accounts under the MCC (uses login_customer_id from google-ads.yaml)')
    account_group.add_argument('--accounts', default='accounts.md',
                               help='Path to accounts.md file (default: ./accounts.md)')

    # Sheet output (required)
    parser.add_argument('--sheet-id', required=True,
                        help='Google Sheet ID for output (find in sheet URL between /d/ and /edit)')
    parser.add_argument('--tab-name', default='Non-Serving Keywords',
                        help='Sheet tab name (default: "Non-Serving Keywords")')

    # Scan parameters
    parser.add_argument('--days', type=int, default=180,
                        help='Days threshold for zero-impression check (default: 180)')
    parser.add_argument('--config', default='google-ads.yaml',
                        help='Path to google-ads.yaml (default: ./google-ads.yaml)')

    args = parser.parse_args()

    print("=" * 70)
    print("NON-SERVING KEYWORD SCANNER")
    print(f"Threshold: {args.days} days with 0 impressions")
    print("=" * 70)
    print()

    # Load clients
    print("Initializing Google Ads client...")
    ads_client = load_ads_client(args.config)

    print("Initializing Google Sheets client...")
    sheets_client = get_sheets_client(args.config)

    # Build account list
    if args.cid:
        accounts = [(args.cid, f"Account {args.cid}")]
    elif args.cids:
        accounts = [(cid.strip(), f"Account {cid.strip()}") for cid in args.cids.split(',') if cid.strip()]
    elif args.all:
        print("Walking MCC for enabled accounts...")
        # Get login_customer_id from yaml
        with open(args.config, 'r', encoding='utf-8') as f:
            ads_config = yaml.safe_load(f)
        login_cid = str(ads_config.get('login_customer_id', ''))
        if not login_cid:
            print("ERROR: --all requires login_customer_id in google-ads.yaml")
            sys.exit(1)
        accounts = get_mcc_accounts(ads_client, login_cid)
    else:
        accounts_path = Path(args.accounts)
        print(f"Loading accounts from {accounts_path}...")
        accounts = parse_accounts_file(accounts_path)

    print(f"Found {len(accounts)} account(s) to scan\n")

    if not accounts:
        print("No accounts to scan. Exiting.")
        sys.exit(0)

    # Scan all accounts
    all_results = []
    accounts_with_issues = 0
    failed_accounts = []

    print("Scanning accounts...\n")

    for i, (cid, account_name) in enumerate(accounts, 1):
        print(f"[{i}/{len(accounts)}] Scanning {account_name}...", end=" ")

        try:
            results = scan_account_keywords(ads_client, cid, account_name, args.days)

            if results:
                all_results.extend(results)
                accounts_with_issues += 1
                print(f"{len(results)} non-serving keywords")
            else:
                print("0 non-serving keywords")

        except Exception as ex:
            print(f"ERROR: {ex}")
            failed_accounts.append((cid, account_name, str(ex)))

    # Summary
    print("\n" + "=" * 70)
    print("SCAN COMPLETE")
    print("=" * 70)
    print(f"Total accounts scanned: {len(accounts)}")
    print(f"Accounts with non-serving keywords: {accounts_with_issues}")
    print(f"Total non-serving keywords found: {len(all_results)}")

    if failed_accounts:
        print(f"\nFailed accounts ({len(failed_accounts)}):")
        for cid, name, error in failed_accounts:
            print(f"  - {name} ({cid}): {error}")

    if all_results:
        print("\nWriting results to Google Sheet...")
        write_to_sheet(
            sheets_client,
            args.sheet_id,
            args.tab_name,
            all_results,
            args.days,
        )
        print(f"\nResults written to:")
        print(f"https://docs.google.com/spreadsheets/d/{args.sheet_id}/edit")
    else:
        print("\nNo non-serving keywords found. Sheet not updated.")


if __name__ == "__main__":
    main()
