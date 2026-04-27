"""
YouTube Channel Extractor - Post-Processing for Placement Audit

After running the placement audit, this script reads the flagged videos from
your Google Sheet, looks up which YouTube channel each video belongs to via
the YouTube Data API v3, and aggregates them by channel.

The payoff: Instead of negating 24,000 individual videos, you negate ~9,000
channels. Each channel exclusion blocks ALL future videos from that channel.

Setup:
    1. pip install google-api-python-client gspread google-auth pyyaml
    2. Enable YouTube Data API v3 in your GCP project
    3. Create an API key (or use existing one)
    4. Add youtube_api_key to your google-ads.yaml

Usage:
    python youtube_channel_extractor.py --sheet YOUR_SHEET_ID --api-key YOUR_KEY
    python youtube_channel_extractor.py --sheet YOUR_SHEET_ID --creds google-ads.yaml
    python youtube_channel_extractor.py --sheet YOUR_SHEET_ID --creds google-ads.yaml --nea-only
    python youtube_channel_extractor.py --sheet YOUR_SHEET_ID --creds google-ads.yaml --test

Flags:
    --sheet       Google Sheet ID (same one the audit wrote to)
    --api-key     YouTube Data API v3 key (or use --creds)
    --creds       Path to google-ads.yaml containing youtube_api_key
    --nea-only    Only process Non-English Alphabet tab
    --keywords-only  Only process keyword-flagged tab
    --test        Preview only, don't write to sheet
    --force       Skip confirmation
    --limit N     Only process first N videos (for testing)

Author: Kurt Henninger (adapted for sharing)
"""

import sys
import argparse
import yaml
from collections import defaultdict
from datetime import datetime

import gspread
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BATCH_SIZE = 50  # YouTube API limit per request


# ============================================================
# AUTH HELPERS
# ============================================================

def get_youtube_api_key(api_key: str = None, creds_path: str = None) -> str:
    """Get YouTube API key from CLI arg or google-ads.yaml."""
    if api_key:
        return api_key
    if creds_path:
        with open(creds_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        key = config.get('youtube_api_key')
        if key:
            return key
    raise ValueError(
        "YouTube API key required. Either pass --api-key or add "
        "'youtube_api_key: YOUR_KEY' to your google-ads.yaml"
    )


def get_sheets_client(creds_path: str) -> gspread.Client:
    """Create gspread client using OAuth credentials from google-ads.yaml."""
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
# READ FLAGGED VIDEOS FROM SHEET
# ============================================================

def get_flagged_videos(spreadsheet, source_tabs: list) -> dict:
    """Read flagged videos from audit sheet tabs.

    Returns: dict mapping video_id -> aggregated data
    """
    print("Reading flagged videos from audit sheets...")

    videos = defaultdict(lambda: {
        'impressions': 0,
        'clicks': 0,
        'cost': 0.0,
        'flag_reasons': set(),
        'accounts': set(),
        'video_name': '',
        'count': 0
    })

    for tab_name in source_tabs:
        try:
            ws = spreadsheet.worksheet(tab_name)
            all_values = ws.get_all_values()

            if len(all_values) < 2:
                print(f"  {tab_name}: No data rows")
                continue

            headers = all_values[0]
            data_rows = all_values[1:]
            print(f"  {tab_name}: {len(data_rows):,} rows")

            # Find columns by header name
            col_map = {h: i for i, h in enumerate(headers)}

            for row in data_rows:
                url = row[col_map.get('Placement URL', 1)] if 'Placement URL' in col_map else ''
                if '/video/' not in url:
                    continue

                video_id = url.split('/video/')[-1].split('?')[0]

                impressions = row[col_map['Impressions']] if 'Impressions' in col_map else 0
                videos[video_id]['impressions'] += int(impressions or 0)

                clicks = row[col_map['Clicks']] if 'Clicks' in col_map else 0
                videos[video_id]['clicks'] += int(clicks or 0)

                cost = row[col_map['Cost']] if 'Cost' in col_map else 0
                if isinstance(cost, str):
                    cost = float(cost.replace('$', '').replace(',', '') or 0)
                videos[video_id]['cost'] += float(cost or 0)

                if 'Flag Reason' in col_map:
                    videos[video_id]['flag_reasons'].add(row[col_map['Flag Reason']])
                if 'Account Name' in col_map:
                    videos[video_id]['accounts'].add(row[col_map['Account Name']])
                if 'Placement Name' in col_map:
                    videos[video_id]['video_name'] = row[col_map['Placement Name']][:60]
                videos[video_id]['count'] += 1

        except Exception as e:
            print(f"  Warning: Could not read '{tab_name}': {e}")

    print(f"Total unique videos: {len(videos):,}")
    return dict(videos)


# ============================================================
# YOUTUBE API CHANNEL LOOKUP
# ============================================================

def batch_lookup_channels(video_ids: list, youtube) -> dict:
    """Lookup channel info for videos in batches of 50.

    Returns: dict mapping video_id -> {channel_id, channel_title}
    """
    results = {}
    total_batches = (len(video_ids) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(video_ids), BATCH_SIZE):
        batch = video_ids[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1

        try:
            request = youtube.videos().list(
                part='snippet',
                id=','.join(batch)
            )
            response = request.execute()

            for item in response.get('items', []):
                results[item['id']] = {
                    'channel_id': item['snippet']['channelId'],
                    'channel_title': item['snippet']['channelTitle']
                }

            if batch_num % 10 == 0 or batch_num == total_batches:
                print(f"  Batch {batch_num}/{total_batches} ({len(results):,} resolved)")

        except Exception as e:
            print(f"  Warning: Batch {batch_num} failed: {e}")

    return results


# ============================================================
# AGGREGATE + OUTPUT
# ============================================================

def aggregate_by_channel(videos: dict, channel_lookup: dict) -> list:
    """Aggregate video data by channel. Returns list sorted by video count desc."""
    channels = defaultdict(lambda: {
        'channel_id': '', 'channel_title': '', 'video_count': 0,
        'total_impressions': 0, 'total_clicks': 0, 'total_cost': 0.0,
        'flag_reasons': set(), 'accounts': set(), 'sample_videos': []
    })

    for video_id, video_data in videos.items():
        if video_id not in channel_lookup:
            continue

        ch = channel_lookup[video_id]
        cid = ch['channel_id']

        channels[cid]['channel_id'] = cid
        channels[cid]['channel_title'] = ch['channel_title']
        channels[cid]['video_count'] += 1
        channels[cid]['total_impressions'] += video_data['impressions']
        channels[cid]['total_clicks'] += video_data['clicks']
        channels[cid]['total_cost'] += video_data['cost']
        channels[cid]['flag_reasons'].update(video_data['flag_reasons'])
        channels[cid]['accounts'].update(video_data['accounts'])

        if len(channels[cid]['sample_videos']) < 5:
            channels[cid]['sample_videos'].append(video_data['video_name'])

    return sorted(channels.values(), key=lambda x: x['video_count'], reverse=True)


def write_channels_to_sheet(channels: list, spreadsheet, tab_name: str,
                            test_mode: bool = False, force_mode: bool = False):
    """Write aggregated channel data to a sheet tab."""

    headers = [
        "Channel Name", "Channel URL", "Channel ID", "Flagged Videos",
        "Total Impressions", "Total Clicks", "Total Cost", "Flag Reasons",
        "Accounts Affected", "Sample Videos", "Run Date"
    ]

    run_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = [headers]

    for ch in channels:
        rows.append([
            ch['channel_title'],
            f"youtube.com/channel/{ch['channel_id']}",
            ch['channel_id'],
            ch['video_count'],
            ch['total_impressions'],
            ch['total_clicks'],
            f"${ch['total_cost']:.2f}",
            ", ".join(sorted(ch['flag_reasons'] - {''}))[:100],
            len(ch['accounts']),
            " | ".join(ch['sample_videos'][:3])[:150],
            run_date
        ])

    print(f"\n  {tab_name}: {len(rows) - 1:,} channels")

    if test_mode:
        print(f"  [TEST] Top 10:")
        for row in rows[1:11]:
            print(f"    {row[3]:>4} videos | {row[0][:40]}")
        return

    if not force_mode:
        confirm = input(f"  Write {len(rows) - 1} channels to '{tab_name}'? (y/n): ")
        if confirm.lower() != 'y':
            print("  Skipped.")
            return

    try:
        ws = spreadsheet.worksheet(tab_name)
        ws.clear()
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=tab_name, rows=len(rows) + 100, cols=15)

    ws.update(rows, value_input_option='USER_ENTERED')
    print(f"  Wrote {len(rows) - 1:,} channels")


# ============================================================
# MAIN
# ============================================================

def main():
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description="Extract YouTube channels from flagged placement audit results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract channels from both tabs
  python youtube_channel_extractor.py --sheet SHEET_ID --creds google-ads.yaml --force

  # Only non-English alphabet channels
  python youtube_channel_extractor.py --sheet SHEET_ID --creds google-ads.yaml --nea-only

  # Test with 100 videos first
  python youtube_channel_extractor.py --sheet SHEET_ID --api-key YOUR_KEY --test --limit 100
        """
    )
    parser.add_argument("--sheet", required=True, help="Google Sheet ID (audit output)")
    parser.add_argument("--api-key", help="YouTube Data API v3 key")
    parser.add_argument("--creds", default="google-ads.yaml", help="Path to google-ads.yaml")
    parser.add_argument("--nea-only", action="store_true", help="Only process Non-English tab")
    parser.add_argument("--keywords-only", action="store_true", help="Only process keyword tab")
    parser.add_argument("--test", action="store_true", help="Preview only")
    parser.add_argument("--force", action="store_true", help="Skip confirmation")
    parser.add_argument("--limit", type=int, help="Limit videos to process")

    args = parser.parse_args()

    print("=" * 60)
    print("YOUTUBE CHANNEL EXTRACTOR")
    print("=" * 60)

    # Resolve API key
    api_key = get_youtube_api_key(args.api_key, args.creds)
    youtube = build('youtube', 'v3', developerKey=api_key)

    # Connect to sheet
    sheets = get_sheets_client(args.creds)
    spreadsheet = sheets.open_by_key(args.sheet)

    # Determine which tabs to process
    jobs = []
    if not args.nea_only:
        jobs.append({
            'source_tabs': ['Bad - YouTube'],
            'output_tab': 'Channels to Negate',
            'label': 'Keyword-flagged'
        })
    if not args.keywords_only:
        jobs.append({
            'source_tabs': ['Bad - YouTube - NEA'],
            'output_tab': 'Channels to Negate - NEA',
            'label': 'Non-English Alphabet'
        })

    for job in jobs:
        print(f"\n--- {job['label']} ---")

        videos = get_flagged_videos(spreadsheet, job['source_tabs'])
        if not videos:
            print("  No flagged videos found, skipping")
            continue

        video_ids = list(videos.keys())
        if args.limit:
            video_ids = video_ids[:args.limit]
            print(f"  Limited to {len(video_ids):,} videos")

        print(f"\n  Looking up channels for {len(video_ids):,} videos...")
        channel_lookup = batch_lookup_channels(video_ids, youtube)
        print(f"  Resolved {len(channel_lookup):,} videos")

        unresolved = len(video_ids) - len(channel_lookup)
        if unresolved > 0:
            print(f"  ({unresolved:,} not found - deleted/private)")

        channels = aggregate_by_channel(videos, channel_lookup)
        print(f"  {len(channels):,} unique channels")

        write_channels_to_sheet(channels, spreadsheet, job['output_tab'],
                                test_mode=args.test, force_mode=args.force)

    # Summary
    print(f"\n{'='*60}")
    print("DONE")
    print(f"Sheet: https://docs.google.com/spreadsheets/d/{args.sheet}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
