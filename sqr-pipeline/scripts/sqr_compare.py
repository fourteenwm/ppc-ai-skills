#!/usr/bin/env python3
"""SQR Pipeline Compare: merge 3-run results and write the agree tabs to a sheet.

Reads Step 1 (classification) and, if present, Step 2 (geo) results across the
3 runs, computes consensus, and writes two tabs to the target Google Sheet:
  "3-3 Agree"  - All 3 runs agree this is a negate candidate (highest confidence)
  "2-3 Agree"  - 2 of 3 runs agree (majority)

The geo stage is OPTIONAL. If you ran it, an off-brand query only becomes a
NEGATE when the geo check did not FAIL (i.e. it does not collide with a location
the advertiser actively targets). If you did NOT run the geo stage, every
off-brand consensus is a NEGATE — the geo columns are simply left blank.

Column Schema (A-N):
  A: CID, B: Query, C: Account, D: Brand Names,
  E: R1 Category, F: R2 Category, G: R3 Category,
  H: R1 Geo Check, I: R2 Geo Check, J: R3 Geo Check,
  K: R1 Conflicting Geo, L: R2 Conflicting Geo,
  M: Include? (human review — mark "x"), N: Count

Usage:
    python sqr_compare.py --sheet-id YOUR_SHEET_ID
    python sqr_compare.py --sheet-id YOUR_SHEET_ID --dry-run

Prerequisites:
    - sqr_prep.py must have been run first (creates data/sqr-pipeline/manifest.json)
    - run{1,2,3}/step1 directories populated by the classification step
    - (optional) run{1,2,3}/step2 directories populated by the geo step
    - token.json at project root with Google Sheets scope (or set
      SHEETS_TOKEN_PATH env var)
    - pip install google-auth google-api-python-client
"""

import argparse
import json
import os
import re
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


NUM_RUNS = 3
NUM_COLS = 14

DEFAULT_DATA_DIR = Path(os.getenv("SQR_DATA_DIR", "./data/sqr-pipeline"))
SHEETS_TOKEN_PATH = Path(os.getenv("SHEETS_TOKEN_PATH", "./token.json"))


# ================================================================
# Google Sheets helpers
# ================================================================

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


def ensure_tab_exists(service, spreadsheet_id, tab_name, num_cols=NUM_COLS):
    """Create tab if it doesn't exist."""
    metadata = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        fields='sheets.properties.title'
    ).execute()
    existing = [s['properties']['title'] for s in metadata.get('sheets', [])]
    if tab_name not in existing:
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': [{'addSheet': {'properties': {
                'title': tab_name,
                'gridProperties': {'rowCount': 1000, 'columnCount': num_cols}
            }}}]}
        ).execute()
        print(f"  Created tab '{tab_name}'")


def clear_tab(service, spreadsheet_id, tab_name):
    """Clear all data from a tab."""
    try:
        service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=f"'{tab_name}'!A:Z"
        ).execute()
    except Exception:
        pass  # Tab may not exist yet


def ensure_sheet_size(service, spreadsheet_id, tab_name, needed_rows, needed_cols=NUM_COLS):
    """Expand sheet if needed."""
    metadata = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id, fields='sheets.properties'
    ).execute()
    for sheet in metadata.get('sheets', []):
        props = sheet['properties']
        if props['title'] == tab_name:
            current_rows = props['gridProperties']['rowCount']
            current_cols = props['gridProperties']['columnCount']
            updates = {}
            if current_rows < needed_rows:
                updates['rowCount'] = needed_rows + 100
            if current_cols < needed_cols:
                updates['columnCount'] = needed_cols + 2
            if updates:
                service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={'requests': [{'updateSheetProperties': {
                        'properties': {
                            'sheetId': props['sheetId'],
                            'gridProperties': updates
                        },
                        'fields': ','.join(f'gridProperties.{k}' for k in updates)
                    }}]}
                ).execute()
            break


def write_batch(service, spreadsheet_id, tab_name, values, num_cols=NUM_COLS):
    """Write values to a tab in batches."""
    if not values:
        return 0
    ensure_sheet_size(service, spreadsheet_id, tab_name, len(values) + 10, num_cols)
    BATCH_SIZE = 5000
    total = 0
    for i in range(0, len(values), BATCH_SIZE):
        batch = values[i:i + BATCH_SIZE]
        start_row = i + 1
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'{tab_name}'!A{start_row}",
            valueInputOption='RAW',
            body={'values': batch}
        ).execute()
        total += len(batch)
    return total


# ================================================================
# Data loading
# ================================================================

def load_step1_results(data_dir: Path, run_num: int, expected_batches: int):
    """Load all Step 1 (off-brand classification) results for a run."""
    run_dir = data_dir / f"run{run_num}" / "step1"
    results = []
    missing = []
    for batch_num in range(1, expected_batches + 1):
        f = run_dir / f"ob_{batch_num:03d}.json"
        if not f.exists():
            missing.append(batch_num)
            continue
        with open(f, 'r', encoding='utf-8') as fh:
            raw = json.load(fh)
        for r in raw:
            if isinstance(r, dict):
                results.append(r)
            elif isinstance(r, list) and len(r) >= 3:
                results.append({'CID': r[0], 'Query': r[1], 'Category': r[2]})
    return results, missing


def load_step2_results(data_dir: Path, run_num: int):
    """Load all Step 2 (geo conflict) results for a run, if any."""
    run_dir = data_dir / f"run{run_num}" / "step2"
    results = []
    if not run_dir.exists():
        return results
    for geo_file in sorted(run_dir.glob("geo_*.json")):
        with open(geo_file, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        for r in raw:
            if isinstance(r, dict):
                # Normalize field names
                if 'Result' in r and 'Geo_Check' not in r:
                    r['Geo_Check'] = r['Result']
                r.setdefault('Conflicting_Geo', '')
                r.setdefault('Confidence', '')
                results.append(r)
            elif isinstance(r, list) and len(r) >= 3:
                results.append({
                    'CID': r[0], 'Query': r[1],
                    'Geo_Check': r[2],
                    'Conflicting_Geo': r[3] if len(r) > 3 else '',
                    'Confidence': r[4] if len(r) > 4 else ''
                })
    return results


def load_lookups(data_dir: Path):
    """Load account and brand lookups saved by sqr_prep.py."""
    account_lookup = {}
    brand_lookup = {}

    acct_file = data_dir / "account_lookup.json"
    if acct_file.exists():
        with open(acct_file, 'r', encoding='utf-8') as f:
            account_lookup = json.load(f)

    brand_file = data_dir / "brand_lookup.json"
    if brand_file.exists():
        with open(brand_file, 'r', encoding='utf-8') as f:
            brand_lookup = json.load(f)

    return account_lookup, brand_lookup


# ================================================================
# Pipeline logic
# ================================================================

def compute_pipeline_result(step1_cat, geo_check):
    """Determine pipeline outcome for a single run.

    Off-brand + geo FAIL  -> GEO_CONFLICT (do NOT negate)
    Off-brand + geo PASS  -> NEGATE
    Off-brand + no geo run -> NEGATE (geo stage is optional)
    Anything else         -> the original category (not a negate candidate)
    """
    if step1_cat != 'off-brand':
        return step1_cat
    if geo_check == 'FAIL':
        return 'GEO_CONFLICT'
    return 'NEGATE'


def build_pipeline_data(data_dir: Path, expected_batches: int):
    """Build step1_map, step2_maps, pipeline_map from all runs."""
    print("\nLoading Step 1 results...")
    step1_runs = []
    for run in range(1, NUM_RUNS + 1):
        results, missing = load_step1_results(data_dir, run, expected_batches)
        print(f"  Run {run}: {len(results)} results, missing batches: {missing or 'none'}")
        step1_runs.append(results)

    print("Loading Step 2 (geo) results, if any...")
    step2_runs = []
    for run in range(1, NUM_RUNS + 1):
        results = load_step2_results(data_dir, run)
        print(f"  Run {run}: {len(results)} geo results")
        step2_runs.append(results)

    # Build Step 1 lookup: (CID, Query) -> [cat_run1, cat_run2, cat_run3]
    step1_map = {}
    for run_idx, run_results in enumerate(step1_runs):
        for r in run_results:
            key = (r['CID'], r['Query'])
            if key not in step1_map:
                step1_map[key] = [None] * NUM_RUNS
            step1_map[key][run_idx] = r.get('Category', '').lower()

    # Build Step 2 lookups
    step2_maps = []
    for run_results in step2_runs:
        m = {}
        for r in run_results:
            key = (r['CID'], r['Query'])
            m[key] = {
                'Geo_Check': r.get('Geo_Check', ''),
                'Conflicting_Geo': r.get('Conflicting_Geo', ''),
                'Confidence': r.get('Confidence', '')
            }
        step2_maps.append(m)

    # Filter to queries with all 3 Step 1 runs complete
    complete = {k: v for k, v in step1_map.items() if all(v)}
    incomplete = len(step1_map) - len(complete)
    print(f"\n  Queries with all 3 Step 1 runs: {len(complete)}")
    if incomplete:
        print(f"  Queries missing runs (excluded): {incomplete}")

    # Compute pipeline result per query per run
    pipeline_map = {}
    for key, cats in complete.items():
        pipeline = []
        for run_idx in range(NUM_RUNS):
            cat = cats[run_idx]
            if cat == 'off-brand':
                geo = step2_maps[run_idx].get(key, {})
                geo_check = geo.get('Geo_Check', '')
                pipeline.append(compute_pipeline_result(cat, geo_check))
            else:
                pipeline.append(cat)
        pipeline_map[key] = pipeline

    return complete, step2_maps, pipeline_map


def get_negate_sets(pipeline_map):
    """Return sets of 3-3 and 2-3 NEGATE keys."""
    agree_3_3 = set()
    agree_2_3 = set()
    for key, pipelines in pipeline_map.items():
        negate_count = sum(1 for p in pipelines if p == 'NEGATE')
        if negate_count == 3:
            agree_3_3.add(key)
        elif negate_count == 2:
            agree_2_3.add(key)
    return agree_3_3, agree_2_3


def format_cid(cid):
    """Format a CID with dashes (e.g., '1234567890' -> '123-456-7890')."""
    digits = re.sub(r'\D', '', str(cid))
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return str(cid)


def build_tab_rows(keys, complete, step2_maps, account_lookup, brand_lookup):
    """Build row data for a tab from a set of query keys.

    Column Schema (A-N):
      A: CID, B: Query, C: Account, D: Brand Names,
      E: R1 Cat, F: R2 Cat, G: R3 Cat,
      H: R1 Geo, I: R2 Geo, J: R3 Geo,
      K: R1 Conflict, L: R2 Conflict,
      M: Include?, N: Count
    """
    rows = []
    for key in sorted(keys):
        cid, query = key
        cats = complete[key]
        row = [
            format_cid(cid),
            query,
            account_lookup.get(cid, ''),
            brand_lookup.get(cid, ''),
            cats[0], cats[1], cats[2],  # R1-R3 Category
        ]
        # R1-R3 Geo Check
        for run_idx in range(NUM_RUNS):
            geo = step2_maps[run_idx].get(key, {})
            geo_check = geo.get('Geo_Check', '') if cats[run_idx] == 'off-brand' else ''
            row.append(geo_check)
        # R1-R2 Conflicting Geo (R3 dropped to keep M as Include?)
        for run_idx in range(2):
            geo = step2_maps[run_idx].get(key, {})
            conflict = geo.get('Conflicting_Geo', '') if cats[run_idx] == 'off-brand' else ''
            row.append(conflict)
        # Column M: Include? (empty for human review)
        row.append('')
        # Column N: Count (handy for an Uploader QUERY/SUM formula)
        row.append(1)
        rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser(description='SQR Pipeline Compare & Write')
    parser.add_argument('--sheet-id', required=True,
                        help='Google Sheet ID to write "3-3 Agree" and "2-3 Agree" tabs')
    parser.add_argument('--data-dir', type=Path, default=DEFAULT_DATA_DIR,
                        help=f'Data directory (default: {DEFAULT_DATA_DIR})')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show stats without writing to sheet')
    args = parser.parse_args()

    print("=" * 60)
    print("SQR Pipeline Compare: Merge 3-Run Results")
    print("=" * 60)

    manifest_file = args.data_dir / "manifest.json"
    if not manifest_file.exists():
        print(f"\nERROR: No manifest found at {manifest_file}")
        print("Run sqr_prep.py first.")
        return
    with open(manifest_file, 'r') as f:
        manifest = json.load(f)

    expected_batches = manifest['num_batches']
    total_queries = manifest['total_queries']
    print(f"\nExpected: {total_queries} queries in {expected_batches} batches x {NUM_RUNS} runs")

    account_lookup, brand_lookup = load_lookups(args.data_dir)
    print(f"Lookups: {len(account_lookup)} accounts, {len(brand_lookup)} brands")

    complete, step2_maps, pipeline_map = build_pipeline_data(args.data_dir, expected_batches)

    if not complete:
        print("\nERROR: No complete results found. Run classification first.")
        return

    n = len(complete)

    negate_33, negate_23 = get_negate_sets(pipeline_map)
    print(f"\n3-3 Unanimous NEGATE: {len(negate_33)}")
    print(f"2-3 Majority NEGATE:  {len(negate_23)}")
    print(f"Combined NEGATE:      {len(negate_33) + len(negate_23)}")

    s1_all_agree = sum(1 for cats in complete.values() if cats[0] == cats[1] == cats[2])
    s1_two_agree = sum(1 for cats in complete.values()
                       if not (cats[0] == cats[1] == cats[2])
                       and (cats[0] == cats[1] or cats[0] == cats[2] or cats[1] == cats[2]))
    s1_none_agree = n - s1_all_agree - s1_two_agree

    print(f"\n{'=' * 60}")
    print("CLASSIFICATION CONSISTENCY")
    print(f"{'=' * 60}")
    print(f"  All 3 agree:   {s1_all_agree} ({s1_all_agree/n*100:.1f}%)")
    print(f"  2 of 3 agree:  {s1_two_agree} ({s1_two_agree/n*100:.1f}%)")
    print(f"  All disagree:  {s1_none_agree} ({s1_none_agree/n*100:.1f}%)")
    print(f"  Total:         {n}")

    HEADER = [
        "CID", "Query", "Account", "Brand Names",
        "R1 Category", "R2 Category", "R3 Category",
        "R1 Geo Check", "R2 Geo Check", "R3 Geo Check",
        "R1 Conflicting Geo", "R2 Conflicting Geo",
        "Include?", "Count"
    ]

    rows_33 = build_tab_rows(negate_33, complete, step2_maps, account_lookup, brand_lookup)
    rows_23 = build_tab_rows(negate_23, complete, step2_maps, account_lookup, brand_lookup)

    print(f"\n3-3 Agree tab: {len(rows_33)} rows")
    print(f"2-3 Agree tab: {len(rows_23)} rows")

    if args.dry_run:
        print(f"\n{'=' * 60}")
        print("DRY RUN - No sheet writes")
        print(f"{'=' * 60}")
        if rows_33:
            print(f"\nSample 3-3 row: {rows_33[0][:5]}...")
        if rows_23:
            print(f"Sample 2-3 row: {rows_23[0][:5]}...")
        return

    print(f"\nWriting to Google Sheet...")
    service = load_sheets_service()

    tab1 = "3-3 Agree"
    ensure_tab_exists(service, args.sheet_id, tab1, NUM_COLS)
    clear_tab(service, args.sheet_id, tab1)
    t1 = write_batch(service, args.sheet_id, tab1, [HEADER] + rows_33, NUM_COLS)
    print(f"  '{tab1}': {t1} rows written ({len(rows_33)} data rows)")

    tab2 = "2-3 Agree"
    ensure_tab_exists(service, args.sheet_id, tab2, NUM_COLS)
    clear_tab(service, args.sheet_id, tab2)
    t2 = write_batch(service, args.sheet_id, tab2, [HEADER] + rows_23, NUM_COLS)
    print(f"  '{tab2}': {t2} rows written ({len(rows_23)} data rows)")

    print(f"\n{'=' * 60}")
    print("RESULTS WRITTEN")
    print(f"{'=' * 60}")
    print(f"  3-3 Agree: {len(rows_33)} queries (unanimous NEGATE)")
    print(f"  2-3 Agree: {len(rows_23)} queries (majority NEGATE)")
    print(f"  Total:     {len(rows_33) + len(rows_23)} NEGATE candidates")
    print(f"\n  Sheet: https://docs.google.com/spreadsheets/d/{args.sheet_id}")
    print(f"\nNEXT STEPS:")
    print(f"  1. Review queries in '3-3 Agree' and '2-3 Agree' tabs")
    print(f"  2. Mark 'x' in Column M (Include?) for approved negatives")
    print(f"  3. Upload (two-step dry-run -> approval code -> execute):")
    print(f"     python scripts/sqr_upload_negatives.py --sheet-id {args.sheet_id}")


if __name__ == '__main__':
    main()
