"""RSA Bulk Edit - Query RSA ads and generate find/replace preview.

Queries RSA ads from specified Google Ads accounts, finds text matches,
and outputs a Google Sheet for review before manual Google Ads Editor import.

Usage:
    # Single account
    python rsa_bulk_edit.py --cid 1234567890 --search "color" --replace "colour"

    # Multiple accounts (comma-separated CIDs)
    python rsa_bulk_edit.py --cids "123,456,789" --search "color" --replace "colour"

    # With sheet output
    python rsa_bulk_edit.py --cid 1234567890 --search "color" --replace "colour" \
        --sheet-id YOUR_SHEET_ID

    # Dry run (console only)
    python rsa_bulk_edit.py --cid 1234567890 --search "color" --replace "colour" --dry-run

Prerequisites:
    - google-ads.yaml at project root with valid OAuth credentials (must include Sheets scope if using --sheet-id)
    - pip install google-ads gspread google-auth pyyaml
"""

import argparse
import sys
import io
import re
from google.ads.googleads.client import GoogleAdsClient
import gspread
from google.oauth2.credentials import Credentials
import yaml

# Windows console fix
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

RSA_QUERY = """
SELECT
  customer.descriptive_name,
  campaign.id,
  campaign.name,
  ad_group.id,
  ad_group.name,
  ad_group_ad.ad.id,
  ad_group_ad.ad.responsive_search_ad.headlines,
  ad_group_ad.ad.responsive_search_ad.descriptions,
  ad_group_ad.ad.responsive_search_ad.path1,
  ad_group_ad.ad.responsive_search_ad.path2,
  ad_group_ad.ad.final_urls,
  ad_group_ad.status
FROM ad_group_ad
WHERE
  ad_group_ad.ad.type = RESPONSIVE_SEARCH_AD
  AND ad_group_ad.status = ENABLED
  AND campaign.status = ENABLED
"""


def format_cid_with_dashes(cid: str) -> str:
    """Format CID with dashes for Google Ads Editor compatibility."""
    cid = cid.replace('-', '')
    return f"{cid[:3]}-{cid[3:6]}-{cid[6:]}"


def query_rsa_ads(client, cid: str) -> list:
    """Query all enabled RSA ads for an account."""
    ga_service = client.get_service("GoogleAdsService")
    results = []

    response = ga_service.search(customer_id=cid, query=RSA_QUERY)

    for row in response:
        ad = row.ad_group_ad.ad
        rsa = ad.responsive_search_ad
        results.append({
            'account_name': row.customer.descriptive_name,
            'cid': cid,
            'campaign_id': row.campaign.id,
            'campaign_name': row.campaign.name,
            'ad_group_id': row.ad_group.id,
            'ad_group_name': row.ad_group.name,
            'ad_id': ad.id,
            'headlines': [h.text for h in rsa.headlines],
            'descriptions': [d.text for d in rsa.descriptions],
            'path1': rsa.path1 if rsa.path1 else '',
            'path2': rsa.path2 if rsa.path2 else '',
            'final_url': ad.final_urls[0] if ad.final_urls else '',
        })

    return results


def find_and_replace(ads: list, search: str, replace: str, case_sensitive: bool = False) -> list:
    """Generate preview rows - one row per ad with all headlines/descriptions."""
    rows = []
    flags = 0 if case_sensitive else re.IGNORECASE
    pattern = re.compile(re.escape(search), flags)

    for ad in ads:
        row = {
            'campaign': ad['campaign_name'],
            'ad_group': ad['ad_group_name'],
            'final_url': ad['final_url'],
            'path1': ad['path1'],
            'path2': ad['path2'],
            'has_match': 'NO',
            'changes_made': [],
            'account_name': ad['account_name'],
            'cid': format_cid_with_dashes(ad['cid']),
            'ad_id': ad['ad_id'],
        }

        for i in range(1, 16):
            if i <= len(ad['headlines']):
                headline = ad['headlines'][i-1]
                has_match = bool(pattern.search(headline))
                new_text = pattern.sub(replace, headline) if has_match else headline
                row[f'headline_{i}'] = new_text
                if has_match:
                    row['has_match'] = 'YES'
                    row['changes_made'].append(f'H{i}')
            else:
                row[f'headline_{i}'] = ''

        for i in range(1, 5):
            if i <= len(ad['descriptions']):
                desc = ad['descriptions'][i-1]
                has_match = bool(pattern.search(desc))
                new_text = pattern.sub(replace, desc) if has_match else desc
                row[f'description_{i}'] = new_text
                if has_match:
                    row['has_match'] = 'YES'
                    row['changes_made'].append(f'D{i}')
            else:
                row[f'description_{i}'] = ''

        row['changes_made'] = ', '.join(row['changes_made']) if row['changes_made'] else ''
        rows.append(row)

    return rows


def write_to_sheet(rows: list, sheet_id: str, tab_name: str = "RSA Edits"):
    """Write preview rows to Google Sheet."""
    with open('google-ads.yaml', 'r') as f:
        config = yaml.safe_load(f)

    ads_config = config.get('google_ads', config)
    credentials = Credentials(
        token=None,
        refresh_token=ads_config.get('refresh_token'),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=ads_config.get('client_id'),
        client_secret=ads_config.get('client_secret'),
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )

    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(sheet_id)

    try:
        ws = spreadsheet.worksheet(tab_name)
        ws.clear()
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=30)

    headers = ['Account Name', 'Customer ID', 'Campaign', 'Ad Group']
    for i in range(1, 16):
        headers.append(f'Headline {i}')
    for i in range(1, 5):
        headers.append(f'Description {i}')
    headers.extend(['Path 1', 'Path 2', 'Final URL'])
    headers.extend(['Has Match', 'Changes Made', 'Ad ID'])

    data_rows = []
    for r in rows:
        row_data = [r['account_name'], r['cid'], r['campaign'], r['ad_group']]
        for i in range(1, 16):
            row_data.append(r.get(f'headline_{i}', ''))
        for i in range(1, 5):
            row_data.append(r.get(f'description_{i}', ''))
        row_data.extend([r['path1'], r['path2'], r['final_url']])
        row_data.extend([r['has_match'], r['changes_made'], r['ad_id']])
        data_rows.append(row_data)

    ws.append_row(headers)
    if data_rows:
        ws.append_rows(data_rows)

    print(f"Wrote {len(data_rows)} rows to '{tab_name}' tab")


def main():
    parser = argparse.ArgumentParser(description="RSA Bulk Edit Preview Generator")
    parser.add_argument('--cid', help='Single customer ID (no dashes)')
    parser.add_argument('--cids', help='Comma-separated customer IDs')
    parser.add_argument('--search', required=True, help='Text to search for')
    parser.add_argument('--replace', required=True, help='Replacement text')
    parser.add_argument('--sheet-id', help='Google Sheet ID for output')
    parser.add_argument('--tab-name', default='RSA Edits', help='Tab name for output (default: RSA Edits)')
    parser.add_argument('--case-sensitive', action='store_true', help='Case-sensitive search')
    parser.add_argument('--dry-run', action='store_true', help='Preview only, no sheet write')

    args = parser.parse_args()

    if not args.cid and not args.cids:
        print("Error: Must specify --cid or --cids")
        sys.exit(1)

    cids = []
    if args.cid:
        cids.append(args.cid.replace('-', ''))
    if args.cids:
        cids.extend([c.strip().replace('-', '') for c in args.cids.split(',')])

    print(f"RSA Bulk Edit Preview")
    print(f"=" * 60)
    print(f"Accounts: {len(cids)}")
    print(f"Search: '{args.search}'")
    print(f"Replace: '{args.replace}'")
    print(f"Case sensitive: {args.case_sensitive}")
    print(f"=" * 60)

    client = GoogleAdsClient.load_from_storage('google-ads.yaml')

    all_ads = []
    for cid in cids:
        print(f"\nQuerying {cid}...")
        try:
            ads = query_rsa_ads(client, cid)
            print(f"  Found {len(ads)} RSA ads")
            all_ads.extend(ads)
        except Exception as e:
            print(f"  Error: {e}")

    print(f"\nTotal RSA ads: {len(all_ads)}")

    rows = find_and_replace(all_ads, args.search, args.replace, args.case_sensitive)
    match_rows = [r for r in rows if r['has_match'] == 'YES']
    print(f"Ads with matches: {len(match_rows)} / {len(rows)}")

    if args.dry_run:
        print("\n[DRY RUN - No sheet write]")
        print("\nMatched ads preview:")
        for r in match_rows[:10]:
            print(f"  {r['account_name']} | Ad ID: {r['ad_id']}")
            print(f"    Changes: {r['changes_made']}")
    elif args.sheet_id:
        write_to_sheet(rows, args.sheet_id, args.tab_name)
        print(f"\nSheet updated: https://docs.google.com/spreadsheets/d/{args.sheet_id}")
    else:
        print("\nNo --sheet-id provided. Use --sheet-id to write results.")


if __name__ == "__main__":
    main()
