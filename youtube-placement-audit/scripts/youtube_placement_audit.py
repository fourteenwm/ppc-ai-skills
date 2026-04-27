"""
YouTube Placement Brand Safety Audit for Google Ads

Queries Google Ads accounts for YouTube placements from PMAX, Demand Gen,
and Display campaigns, then flags brand safety violations (kids content,
adult content, gaming, non-English, spam) and writes results to Google Sheets.

Setup:
    1. pip install google-ads gspread google-auth pyyaml
    2. Create google-ads.yaml with your credentials (see README)
    3. Create a Google Sheet and paste the ID below
    4. Share that sheet with your service account email (or use OAuth)

Usage:
    python youtube_placement_audit.py --mcc 1234567890 --sheet YOUR_SHEET_ID
    python youtube_placement_audit.py --mcc 1234567890 --sheet YOUR_SHEET_ID --test --limit 5
    python youtube_placement_audit.py --mcc 1234567890 --sheet YOUR_SHEET_ID --force

Flags:
    --mcc       Your MCC account ID (required)
    --sheet     Google Sheet ID to write results (required)
    --creds     Path to google-ads.yaml (default: google-ads.yaml)
    --test      Preview only, don't write to sheet
    --force     Skip confirmation, write directly
    --limit N   Only process first N accounts (for testing)
    --days N    Date range in days (default: 30)
    --filter    Filter accounts by name substring (e.g. --filter "Acme")

Author: Kurt Henninger (adapted for sharing)
"""

import sys
import argparse
import re
import unicodedata
from datetime import datetime

import yaml
import gspread
from google.ads.googleads.client import GoogleAdsClient
from google.oauth2.credentials import Credentials

# ============================================================
# CONFIGURATION - Customize these keyword lists as needed
# ============================================================

FLAGGED_KEYWORDS = {
    # Kids content
    'toy': 'Kids content',
    'child': 'Kids content',
    'pokemon': 'Kids content',
    'doll': 'Kids content',
    'cartoon': 'Kids content',
    'nursery': 'Kids content',
    'peppa pig': 'Kids content',
    'disney': 'Kids content',
    'muppets': 'Kids content',
    'jim henson': 'Kids content',
    'story time': 'Kids content',
    'storytime': 'Kids content',
    'roblox': 'Kids content',
    'minecraft': 'Kids content',
    'fortnite': 'Kids content',

    # Adult content
    'xxx': 'Adult content',
    'sexy': 'Adult content',
    ' sex ': 'Adult content',
    'onlyfans': 'Adult content',

    # Gaming
    'gaming': 'Gaming content',
    'ninja': 'Gaming content',
    'twitch': 'Gaming content',

    # Spam / Clickbait
    '1-800': 'Spam',
    'viral': 'Spam/Clickbait',
    'prank': 'Spam/Clickbait',

    # Legal
    'dui': 'Legal',
    'bail bonds': 'Legal',
}

# Non-Latin scripts to flag (detected via Unicode character names)
NON_LATIN_SCRIPTS = [
    'CYRILLIC', 'ARABIC', 'HEBREW', 'CJK', 'HIRAGANA', 'KATAKANA',
    'HANGUL', 'DEVANAGARI', 'THAI', 'GREEK', 'ARMENIAN', 'GEORGIAN',
    'BENGALI', 'TAMIL', 'TELUGU', 'KANNADA', 'MALAYALAM', 'GUJARATI',
    'PUNJABI', 'TIBETAN', 'MYANMAR', 'KHMER', 'LAO', 'SINHALA'
]


# ============================================================
# HELPERS
# ============================================================

def contains_non_latin(text: str) -> bool:
    """Check if text contains non-Latin alphabet characters."""
    if not text:
        return False
    for char in text:
        if char.isalpha():
            try:
                name = unicodedata.name(char, '')
                for script in NON_LATIN_SCRIPTS:
                    if script in name:
                        return True
            except ValueError:
                if ord(char) > 127 and char.isalpha():
                    return True
    return False


def check_placement(placement_name: str) -> tuple:
    """Check if a placement name should be flagged.

    Returns: (is_flagged: bool, reason: str)
    """
    if not placement_name or placement_name.strip() == '':
        return True, "Null/Empty placement"

    name_lower = placement_name.lower()

    for keyword, reason in FLAGGED_KEYWORDS.items():
        if keyword.lower() in name_lower:
            return True, f"{reason}: '{keyword}'"

    if contains_non_latin(placement_name):
        return True, "Non-English content"

    return False, ""


def get_sheets_client(creds_path: str) -> gspread.Client:
    """Create a gspread client using OAuth credentials from google-ads.yaml.

    This reuses the same OAuth credentials you use for Google Ads API access.
    Your OAuth app needs the Google Sheets scope enabled in GCP.
    """
    with open(creds_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    creds = Credentials(
        token=None,
        refresh_token=config['refresh_token'],
        client_id=config['client_id'],
        client_secret=config['client_secret'],
        token_uri='https://oauth2.googleapis.com/token',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    return gspread.authorize(creds)


# ============================================================
# GOOGLE ADS QUERIES
# ============================================================

def get_accounts(client: GoogleAdsClient, mcc_id: str, name_filter: str = None) -> list:
    """Get all non-manager accounts under the MCC."""
    ga_service = client.get_service("GoogleAdsService")

    query = """
        SELECT
            customer_client.id,
            customer_client.descriptive_name,
            customer_client.manager,
            customer_client.status
        FROM customer_client
        WHERE customer_client.manager = false
        AND customer_client.status = 'ENABLED'
    """

    accounts = []
    response = ga_service.search(customer_id=mcc_id, query=query)

    for row in response:
        name = row.customer_client.descriptive_name
        if name_filter and name_filter.lower() not in name.lower():
            continue
        accounts.append({
            'id': str(row.customer_client.id),
            'name': name
        })

    return sorted(accounts, key=lambda x: x['name'])


def get_youtube_placements(client: GoogleAdsClient, customer_id: str, days: int = 30) -> list:
    """Get YouTube placements from PMAX, Demand Gen, and Display campaigns."""
    ga_service = client.get_service("GoogleAdsService")
    placements = []

    # PMAX YouTube placements (impressions only - API limitation)
    pmax_query = f"""
        SELECT
            campaign.name,
            performance_max_placement_view.display_name,
            performance_max_placement_view.placement_type,
            performance_max_placement_view.target_url,
            metrics.impressions
        FROM performance_max_placement_view
        WHERE segments.date DURING LAST_{days}_DAYS
        AND performance_max_placement_view.placement_type IN ('YOUTUBE_VIDEO', 'YOUTUBE_CHANNEL')
    """

    try:
        response = ga_service.search(customer_id=customer_id, query=pmax_query)
        for row in response:
            placements.append({
                'placement_name': row.performance_max_placement_view.display_name or '',
                'placement_url': row.performance_max_placement_view.target_url or '',
                'placement_type': f"PMAX-{row.performance_max_placement_view.placement_type.name}",
                'campaign': row.campaign.name,
                'campaign_type': 'PMAX',
                'impressions': row.metrics.impressions,
                'clicks': 0,
                'cost': 0,
                'conversions': 0
            })
    except Exception:
        pass

    # Display / Demand Gen / Video campaign YouTube placements (full metrics)
    for placement_type in ['YOUTUBE_VIDEO', 'YOUTUBE_CHANNEL']:
        detail_query = f"""
            SELECT
                campaign.name,
                campaign.advertising_channel_type,
                detail_placement_view.display_name,
                detail_placement_view.target_url,
                detail_placement_view.placement_type,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions
            FROM detail_placement_view
            WHERE segments.date DURING LAST_{days}_DAYS
            AND detail_placement_view.placement_type = '{placement_type}'
        """

        try:
            response = ga_service.search(customer_id=customer_id, query=detail_query)
            for row in response:
                placements.append({
                    'placement_name': row.detail_placement_view.display_name or '',
                    'placement_url': row.detail_placement_view.target_url or '',
                    'placement_type': placement_type.replace('_', ' ').title(),
                    'campaign': row.campaign.name,
                    'campaign_type': row.campaign.advertising_channel_type.name,
                    'impressions': row.metrics.impressions,
                    'clicks': row.metrics.clicks,
                    'cost': row.metrics.cost_micros / 1_000_000,
                    'conversions': row.metrics.conversions
                })
        except Exception:
            pass

    return placements


# ============================================================
# SHEET OUTPUT
# ============================================================

def write_to_sheet(flagged_placements: list, sheet_id: str, creds_path: str,
                   test_mode: bool = False, force_mode: bool = False):
    """Write flagged placements to Google Sheet (two tabs: keywords + non-English)."""

    if not flagged_placements:
        print("\nNo flagged YouTube placements found.")
        return

    # Separate non-English from keyword flags
    nea = [p for p in flagged_placements if p['flag_reason'] == "Non-English content"]
    keywords = [p for p in flagged_placements if p['flag_reason'] != "Non-English content"]

    nea_sorted = sorted(nea, key=lambda x: x['impressions'], reverse=True)
    kw_sorted = sorted(keywords, key=lambda x: x['impressions'], reverse=True)

    run_date = datetime.now().strftime("%Y-%m-%d")

    def to_rows(items):
        return [[
            p['placement_name'], p['placement_url'], p['account_name'], p['account_id'],
            p['campaign'], p['campaign_type'], p['placement_type'], p['flag_reason'],
            p['impressions'], p['clicks'], round(p['cost'], 2),
            round(p['conversions'], 2), run_date
        ] for p in items]

    headers = [
        "Placement Name", "Placement URL", "Account Name", "CID", "Campaign",
        "Campaign Type", "Placement Type", "Flag Reason", "Impressions",
        "Clicks", "Cost", "Conversions", "Run Date"
    ]

    # Preview
    print(f"\n{'='*70}")
    print("YOUTUBE PLACEMENT AUDIT RESULTS")
    print(f"{'='*70}")
    print(f"Total flagged: {len(flagged_placements)}")
    print(f"  Keyword flags: {len(kw_sorted)}")
    print(f"  Non-English:   {len(nea_sorted)}")

    if kw_sorted:
        print(f"\nTop 5 keyword flags by impressions:")
        for p in kw_sorted[:5]:
            print(f"  {p['impressions']:>8} | {p['flag_reason'][:25]:<25} | {p['placement_name'][:40]}")

    if nea_sorted:
        print(f"\nTop 5 non-English by impressions:")
        for p in nea_sorted[:5]:
            print(f"  {p['impressions']:>8} | {p['placement_name'][:50]}")

    if test_mode:
        print(f"\n[TEST MODE] Would write {len(kw_sorted)} keyword rows + {len(nea_sorted)} NEA rows")
        return

    if not force_mode:
        confirm = input(f"\nWrite {len(flagged_placements)} rows to sheet? (y/n): ")
        if confirm.lower() != 'y':
            print("Cancelled.")
            return

    # Write
    sheets = get_sheets_client(creds_path)
    spreadsheet = sheets.open_by_key(sheet_id)

    def write_tab(tab_name, rows):
        if not rows:
            print(f"  No data for '{tab_name}', skipping")
            return
        try:
            ws = spreadsheet.worksheet(tab_name)
        except gspread.exceptions.WorksheetNotFound:
            ws = spreadsheet.add_worksheet(title=tab_name, rows=len(rows) + 100, cols=13)
        ws.clear()
        ws.update(range_name='A1', values=[headers] + rows)
        print(f"  Wrote {len(rows)} rows to '{tab_name}'")

    print("\nWriting to Google Sheet...")
    write_tab("Bad - YouTube", to_rows(kw_sorted))
    write_tab("Bad - YouTube - NEA", to_rows(nea_sorted))
    print(f"\nSheet: https://docs.google.com/spreadsheets/d/{sheet_id}")


# ============================================================
# MAIN
# ============================================================

def main():
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description="YouTube Placement Brand Safety Audit for Google Ads",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with 3 accounts first
  python youtube_placement_audit.py --mcc 1234567890 --sheet SHEET_ID --test --limit 3

  # Full audit, write to sheet
  python youtube_placement_audit.py --mcc 1234567890 --sheet SHEET_ID --force

  # Only audit accounts with "Acme" in the name
  python youtube_placement_audit.py --mcc 1234567890 --sheet SHEET_ID --filter "Acme"
        """
    )
    parser.add_argument("--mcc", required=True, help="MCC account ID (no dashes)")
    parser.add_argument("--sheet", required=True, help="Google Sheet ID for output")
    parser.add_argument("--creds", default="google-ads.yaml", help="Path to google-ads.yaml")
    parser.add_argument("--test", action="store_true", help="Preview only, no write")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--limit", type=int, help="Process only first N accounts")
    parser.add_argument("--days", type=int, default=30, help="Date range in days (default: 30)")
    parser.add_argument("--filter", help="Only audit accounts matching this substring")

    args = parser.parse_args()

    print("=" * 70)
    print("YOUTUBE PLACEMENT BRAND SAFETY AUDIT")
    print("=" * 70)
    print(f"Date:       {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"MCC:        {args.mcc}")
    print(f"Date Range: Last {args.days} days")
    print(f"Output:     Sheet {args.sheet}")
    if args.filter:
        print(f"Filter:     Accounts matching '{args.filter}'")
    if args.test:
        print("Mode:       TEST (preview only)")
    if args.force:
        print("Mode:       FORCE (skip confirmation)")
    print("=" * 70)

    # Initialize Google Ads client
    client = GoogleAdsClient.load_from_storage(args.creds)

    # Get accounts
    print("\nFetching accounts...")
    accounts = get_accounts(client, args.mcc, name_filter=args.filter)

    if args.limit:
        accounts = accounts[:args.limit]

    print(f"  Found {len(accounts)} accounts")

    if not accounts:
        print("No accounts found. Check your MCC ID and filter.")
        return

    # Process each account
    all_flagged = []
    print("\nProcessing accounts...")

    for i, account in enumerate(accounts, 1):
        print(f"\n[{i}/{len(accounts)}] {account['name']} ({account['id']})")

        try:
            placements = get_youtube_placements(client, account['id'], days=args.days)

            if not placements:
                print(f"      No YouTube placements")
                continue

            print(f"      Found {len(placements)} YouTube placements")

            flagged_count = 0
            for p in placements:
                is_flagged, reason = check_placement(p['placement_name'])
                if is_flagged:
                    flagged_count += 1
                    all_flagged.append({
                        'account_name': account['name'],
                        'account_id': account['id'],
                        'placement_name': p['placement_name'],
                        'placement_url': p['placement_url'],
                        'placement_type': p['placement_type'],
                        'campaign': p['campaign'],
                        'campaign_type': p['campaign_type'],
                        'flag_reason': reason,
                        'impressions': p['impressions'],
                        'clicks': p['clicks'],
                        'cost': p['cost'],
                        'conversions': p['conversions']
                    })

            if flagged_count > 0:
                print(f"      [!] Flagged {flagged_count} placements")

        except Exception as e:
            error_msg = str(e)
            if 'PERMISSION_DENIED' in error_msg or 'NOT_ENABLED' in error_msg:
                print(f"      Skipped (no access)")
            else:
                print(f"      Error: {error_msg[:80]}")

    # Summary + write
    print(f"\n{'='*70}")
    print(f"TOTAL FLAGGED: {len(all_flagged)} YouTube placements")
    print(f"{'='*70}")

    write_to_sheet(all_flagged, args.sheet, args.creds,
                   test_mode=args.test, force_mode=args.force)

    print("\nAUDIT COMPLETE")


if __name__ == "__main__":
    main()
