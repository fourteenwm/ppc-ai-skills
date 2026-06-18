#!/usr/bin/env python3
"""SQR Pipeline Prep: read pending queries from a sheet and create batches.

Reads:
  - "Have Cost" tab (Column I = "Waiting") for pending queries
  - references/offbrand-keywords.txt for competitor terms (bundled with this skill)
  - (optional) a "GEO Source" tab for geo targets by CID — only needed for the
    optional geo step (see prep_geo_batches.py + references/geo-prompt.md)

Creates under ./data/sqr-pipeline/:
  ob_batches/ob_001.json ... ob_NNN.json
  account_lookup.json
  brand_lookup.json
  geo_targets.json          (empty {} unless a GEO Source tab is found)
  manifest.json
  run1/step{1,2}/  run2/step{1,2}/  run3/step{1,2}/  (empty, populated downstream)

Usage:
    python sqr_prep.py --sheet-id YOUR_SHEET_ID
    python sqr_prep.py --sheet-id YOUR_SHEET_ID --dry-run
    python sqr_prep.py --sheet-id YOUR_SHEET_ID --all  # include all rows, not just "Waiting"
    python sqr_prep.py --sheet-id YOUR_SHEET_ID --geo-tab "GEO Source"  # enable geo step input

Prerequisites:
    - token.json at project root with Google Sheets scope (or set
      SHEETS_TOKEN_PATH env var)
    - references/offbrand-keywords.txt bundled with this skill (default
      resolution: ../references/offbrand-keywords.txt relative to this
      script — override via --offbrand-keywords)
    - pip install google-auth google-api-python-client
"""

import argparse
import json
import math
import os
import re
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


# Defaults
BATCH_SIZE = 50
NUM_RUNS = 3

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent  # the sqr-pipeline skill folder

DEFAULT_DATA_DIR = Path(os.getenv("SQR_DATA_DIR", "./data/sqr-pipeline"))
DEFAULT_OFFBRAND_KEYWORDS = SKILL_DIR / "references" / "offbrand-keywords.txt"
SHEETS_TOKEN_PATH = Path(os.getenv("SHEETS_TOKEN_PATH", "./token.json"))


def load_sheets_service():
    """Load Google Sheets API service."""
    if not SHEETS_TOKEN_PATH.exists():
        raise FileNotFoundError(
            f"Sheets token not found at {SHEETS_TOKEN_PATH.absolute()}\n"
            "Set up OAuth credentials first or set SHEETS_TOKEN_PATH env var.\n"
            "See the google-ads-api-setup skill for the walkthrough."
        )
    creds = Credentials.from_authorized_user_file(
        str(SHEETS_TOKEN_PATH),
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(SHEETS_TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())
    return build('sheets', 'v4', credentials=creds)


def read_tab(service, sheet_id, tab_name, range_str):
    """Read data from a tab."""
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"'{tab_name}'!{range_str}"
    ).execute()
    return result.get('values', [])


def load_queries(service, sheet_id, input_tab='Have Cost', mode='waiting'):
    """Load queries from the input tab.

    Modes:
        'waiting' - only rows where Column I = 'Waiting' (new unprocessed queries)
        'all'     - all rows with data in CID (A) and Query (C), regardless of status
    """
    print(f"Reading '{input_tab}' tab...")
    values = read_tab(service, sheet_id, input_tab, "A:I")

    if not values:
        print("  No data found!")
        return []

    rows = values[1:]

    queries = []
    data_rows = 0
    waiting_count = 0
    processed_count = 0
    for row in rows:
        while len(row) < 9:
            row.append('')

        cid = row[0].strip()
        account = row[1].strip()
        query = row[2].strip()
        brand_names = row[7].strip()  # Column H
        status = row[8].strip()       # Column I

        if not cid or not query:
            continue

        data_rows += 1
        is_waiting = status.lower() == 'waiting'
        if is_waiting:
            waiting_count += 1
        else:
            processed_count += 1

        if mode == 'all' or is_waiting:
            queries.append({
                'CID': cid,
                'Account': account,
                'Query': query,
                'Brand_Names': brand_names
            })

    print(f"  Data rows: {data_rows} (filler rows skipped: {len(rows) - data_rows})")
    print(f"  Waiting: {waiting_count}, Already processed: {processed_count}")
    print(f"  Selected for pipeline ({mode} mode): {len(queries)}")
    return queries


def load_geo_targets(service, sheet_id, geo_tab):
    """Load geo targets from an optional GEO Source tab.

    Expects: CID (col A), semicolon-separated geo names (col B). Returns a dict
    keyed by digits-only CID -> list of geo names. Returns {} if the tab is
    absent or empty (the geo step is optional). prep_geo_batches.py matches
    query CIDs against these keys after normalizing to digits-only too.
    """
    if not geo_tab:
        return {}
    print(f"Reading optional '{geo_tab}' tab for geo targets...")
    try:
        values = read_tab(service, sheet_id, geo_tab, "A:B")
    except Exception:
        values = []
    if not values:
        print(f"  No '{geo_tab}' tab / no data — geo step disabled for this run.")
        return {}

    start_idx = 0
    if values[0] and any(str(h).strip().lower() in ('cid', 'customer id', 'account')
                         for h in values[0]):
        start_idx = 1

    geo_targets = {}
    for row in values[start_idx:]:
        if len(row) < 2:
            continue
        cid = re.sub(r'\D', '', str(row[0]))  # normalize to digits-only
        geo_names = str(row[1]).strip()
        if cid and geo_names:
            geo_targets[cid] = [g.strip() for g in geo_names.split(';') if g.strip()]

    print(f"  Loaded geo targets for {len(geo_targets)} CID(s)")
    return geo_targets


def load_offbrand_keywords(path: Path):
    """Load off-brand keywords list."""
    if not path.exists():
        raise FileNotFoundError(
            f"Off-brand keywords not found at {path}\n"
            "Expected references/offbrand-keywords.txt bundled with this skill, "
            "or pass --offbrand-keywords PATH."
        )
    with open(path, 'r', encoding='utf-8') as f:
        keywords = [line.strip() for line in f if line.strip()]
    print(f"Loaded {len(keywords)} off-brand keywords from {path}")
    return keywords


def main():
    parser = argparse.ArgumentParser(description='SQR Pipeline Prep')
    parser.add_argument('--sheet-id', required=True,
                        help='Google Sheet ID containing the SQR pipeline tabs')
    parser.add_argument('--input-tab', default='Have Cost',
                        help='Input tab name (default: "Have Cost")')
    parser.add_argument('--geo-tab', default=None,
                        help='Optional GEO Source tab name (CID in col A, '
                             'semicolon-separated geo names in col B). Enables the '
                             'optional geo step. Omit to skip geo entirely.')
    parser.add_argument('--data-dir', type=Path, default=DEFAULT_DATA_DIR,
                        help=f'Data directory (default: {DEFAULT_DATA_DIR})')
    parser.add_argument('--offbrand-keywords', type=Path,
                        default=DEFAULT_OFFBRAND_KEYWORDS,
                        help='Path to offbrand-keywords.txt '
                             '(default: ../references/offbrand-keywords.txt)')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE,
                        help=f'Queries per batch (default: {BATCH_SIZE})')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview counts without creating files')
    parser.add_argument('--all', action='store_true',
                        help='Process ALL data rows (not just Waiting)')
    args = parser.parse_args()

    print("=" * 60)
    print("SQR Pipeline Prep: Creating batches from pending queries")
    print("=" * 60)

    print("\nLoading Google Sheets credentials...")
    service = load_sheets_service()
    print("  Connected.")

    mode = 'all' if args.all else 'waiting'
    print()
    queries = load_queries(service, args.sheet_id, input_tab=args.input_tab, mode=mode)
    if not queries:
        print("\nNo pending queries found. Nothing to do.")
        return

    geo_targets = load_geo_targets(service, args.sheet_id, args.geo_tab)
    offbrand_keywords = load_offbrand_keywords(args.offbrand_keywords)

    cids = sorted(set(q['CID'] for q in queries))
    print(f"\nUnique CIDs: {len(cids)}")

    num_batches = math.ceil(len(queries) / args.batch_size)

    if args.dry_run:
        print(f"\n{'=' * 60}")
        print("DRY RUN - No files created")
        print(f"{'=' * 60}")
        print(f"  Would create {num_batches} batches of {args.batch_size}")
        print(f"  Total queries: {len(queries)}")
        print(f"  Geo targets loaded: {len(geo_targets)} CID(s)")
        print(f"  {num_batches} batches x {NUM_RUNS} runs = "
              f"{num_batches * NUM_RUNS} classification passes")
        return

    data_dir = args.data_dir

    # Clean previous run data
    if data_dir.exists():
        import shutil
        for subdir in ['ob_batches', 'run1', 'run2', 'run3']:
            target = data_dir / subdir
            if target.exists():
                shutil.rmtree(target)
        print("  Cleaned previous run data")

    # Create directory structure (step1 for classification, step2 for optional geo)
    print("\nCreating directory structure...")
    ob_batch_dir = data_dir / "ob_batches"
    ob_batch_dir.mkdir(parents=True, exist_ok=True)
    for run in range(1, NUM_RUNS + 1):
        (data_dir / f"run{run}" / "step1").mkdir(parents=True, exist_ok=True)
        (data_dir / f"run{run}" / "step2").mkdir(parents=True, exist_ok=True)
    print(f"  Created {data_dir}/run{{1,2,3}}/step{{1,2}}/")

    # Save geo targets (empty {} if no GEO Source tab — the geo step is optional)
    with open(data_dir / "geo_targets.json", 'w', encoding='utf-8') as f:
        json.dump(geo_targets, f, indent=2)
    print(f"  Saved geo targets ({len(geo_targets)} CIDs)")

    # Create off-brand batches
    print(f"\nCreating {num_batches} off-brand batches of {args.batch_size}...")

    total_query_count = 0
    for i in range(num_batches):
        start = i * args.batch_size
        end = min(start + args.batch_size, len(queries))
        batch_queries = queries[start:end]

        brand_names = {}
        query_list = []
        for q in batch_queries:
            cid = q['CID']
            if cid not in brand_names and q.get('Brand_Names'):
                brand_names[cid] = q['Brand_Names']
            query_list.append({'CID': cid, 'Query': q['Query']})

        batch_data = {
            'type': 'offbrand',
            'batch_num': i + 1,
            'total_batches': num_batches,
            'query_count': len(query_list),
            'queries': query_list,
            'brand_names': brand_names,
            'off_brand_keywords': offbrand_keywords,
        }

        batch_file = ob_batch_dir / f"ob_{i+1:03d}.json"
        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, indent=2, ensure_ascii=False)

        total_query_count += len(query_list)

    print(f"  Created {num_batches} batch files")

    # Save account and brand lookups for compare script
    account_lookup = {}
    brand_lookup = {}
    for q in queries:
        cid = q['CID']
        if cid not in account_lookup and q.get('Account'):
            account_lookup[cid] = q['Account']
        if cid not in brand_lookup and q.get('Brand_Names'):
            brand_lookup[cid] = q['Brand_Names']

    with open(data_dir / "account_lookup.json", 'w', encoding='utf-8') as f:
        json.dump(account_lookup, f, indent=2)
    with open(data_dir / "brand_lookup.json", 'w', encoding='utf-8') as f:
        json.dump(brand_lookup, f, indent=2)
    print(f"  Saved account ({len(account_lookup)}) and brand ({len(brand_lookup)}) lookups")

    # Save manifest
    manifest = {
        'pipeline': 'sqr-pipeline',
        'sheet_id': args.sheet_id,
        'input_tab': args.input_tab,
        'total_queries': len(queries),
        'batch_size': args.batch_size,
        'num_batches': num_batches,
        'num_runs': NUM_RUNS,
        'num_cids': len(cids),
        'cids': cids,
        'geo_cids': len(geo_targets),
        'offbrand_keywords_count': len(offbrand_keywords),
        'steps': ['step1_offbrand', 'step2_geo'],
        'status': 'prepared'
    }
    with open(data_dir / "manifest.json", 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"  Manifest saved")

    assert total_query_count == len(queries), f"Mismatch: {total_query_count} != {len(queries)}"

    print(f"\n{'=' * 60}")
    print("VERIFICATION")
    print(f"{'=' * 60}")
    print(f"  Total queries:       {len(queries)}")
    print(f"  Batch size:          {args.batch_size}")
    print(f"  Number of batches:   {num_batches}")
    print(f"  Unique CIDs:         {len(cids)}")
    print(f"  Geo target CIDs:     {len(geo_targets)}")
    print(f"  Off-brand keywords:  {len(offbrand_keywords)}")
    print(f"  VERIFIED: All {len(queries)} queries batched")
    print(f"\n{'=' * 60}")
    print("NEXT STEP: Run the 3-run classification (step 2 of the sqr-pipeline skill)")
    print(f"  Say: 'run SQR pipeline' in Claude Code")
    print(f"  {num_batches} batches x {NUM_RUNS} runs = "
          f"{num_batches * NUM_RUNS} classification passes")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
