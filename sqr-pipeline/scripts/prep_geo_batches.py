#!/usr/bin/env python3
"""SQR Pipeline (optional geo step): build geo batches from Step 1 results.

For each of the 3 runs:
  1. Load all Step 1 classification results from data/sqr-pipeline/run{R}/step1/
  2. Filter to off-brand queries only
  3. Look up geo targets from data/sqr-pipeline/geo_targets.json
     (written by sqr_prep.py when you pass --geo-tab; CIDs are keyed digits-only)
  4. Create geo check batches at data/sqr-pipeline/run{R}/step2_batches/geo_NNN.json

Run this between the classification step (step 2) and the consensus step (step 4),
ONLY if you want the optional geo conflict stage. The classification agents then
read each geo batch, apply references/geo-prompt.md, and write their verdicts to
data/sqr-pipeline/run{R}/step2/geo_NNN.json. sqr_compare.py merges step1 + step2.

Usage:
    python prep_geo_batches.py                  # all 3 runs
    python prep_geo_batches.py --run 1          # run 1 only
    python prep_geo_batches.py --data-dir ./data/sqr-pipeline
"""

import argparse
import json
import math
import os
import re
from pathlib import Path

DEFAULT_DATA_DIR = Path(os.getenv("SQR_DATA_DIR", "./data/sqr-pipeline"))
GEO_BATCH_SIZE = 50
NUM_RUNS = 3


def _norm(cid):
    """Normalize a CID to digits-only for format-proof matching."""
    return re.sub(r'\D', '', str(cid))


def prep_geo_batches(data_dir, run_num):
    """Prepare geo batches for a single run from its Step 1 results."""
    step1_dir = data_dir / f"run{run_num}" / "step1"
    step2_batch_dir = data_dir / f"run{run_num}" / "step2_batches"
    step2_batch_dir.mkdir(parents=True, exist_ok=True)

    # Load geo targets (keyed digits-only by sqr_prep.py)
    with open(data_dir / "geo_targets.json", 'r', encoding='utf-8') as f:
        geo_targets = json.load(f)

    # Load manifest for expected batch count
    with open(data_dir / "manifest.json", 'r') as f:
        manifest = json.load(f)
    expected_batches = manifest['num_batches']

    # Collect all off-brand queries from Step 1
    offbrand = []
    total_loaded = 0
    missing = []
    for batch_num in range(1, expected_batches + 1):
        f_path = step1_dir / f"ob_{batch_num:03d}.json"
        if not f_path.exists():
            missing.append(batch_num)
            continue
        with open(f_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
        total_loaded += len(results)
        for r in results:
            # Handle both dict and array formats
            if isinstance(r, dict):
                cat = r.get('Category', '').lower()
                cid = r['CID']
                query = r['Query']
            elif isinstance(r, list) and len(r) >= 3:
                cid, query, cat = r[0], r[1], r[2].lower()
            else:
                continue
            if cat == 'off-brand':
                offbrand.append({'CID': cid, 'Query': query})

    print(f"\nRun {run_num}:")
    print(f"  Step 1 results loaded: {total_loaded}")
    if missing:
        print(f"  WARNING: Missing batches: {missing}")
    if total_loaded > 0:
        print(f"  Off-brand queries: {len(offbrand)} ({len(offbrand)/total_loaded*100:.1f}%)")
    else:
        print(f"  Off-brand: 0")

    # Filter to only queries whose CID has geo targets (match digits-only)
    offbrand_with_geo = [q for q in offbrand if geo_targets.get(_norm(q['CID']))]
    offbrand_no_geo = len(offbrand) - len(offbrand_with_geo)
    print(f"  Off-brand with geo targets: {len(offbrand_with_geo)}")
    if offbrand_no_geo > 0:
        print(f"  Off-brand WITHOUT geo targets (skipped): {offbrand_no_geo}")

    # Create geo batches
    num_batches = math.ceil(len(offbrand_with_geo) / GEO_BATCH_SIZE) if offbrand_with_geo else 0
    print(f"  Creating {num_batches} geo batches of up to {GEO_BATCH_SIZE}")

    for i in range(num_batches):
        start = i * GEO_BATCH_SIZE
        end = min(start + GEO_BATCH_SIZE, len(offbrand_with_geo))
        batch = offbrand_with_geo[start:end]

        # Key geo targets by the query CID as it appears, resolved via digits-only
        batch_geo = {}
        for q in batch:
            cn = _norm(q['CID'])
            if geo_targets.get(cn):
                batch_geo[q['CID']] = geo_targets[cn]

        batch_data = {
            'type': 'geo',
            'run': run_num,
            'batch_num': i + 1,
            'total_batches': num_batches,
            'query_count': len(batch),
            'queries': batch,
            'geo_targets': batch_geo
        }

        out_file = step2_batch_dir / f"geo_{i+1:03d}.json"
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, indent=2, ensure_ascii=False)

    # Save summary
    summary = {
        'run': run_num,
        'step1_total_loaded': total_loaded,
        'step1_missing_batches': missing,
        'total_offbrand': len(offbrand),
        'offbrand_with_geo': len(offbrand_with_geo),
        'offbrand_no_geo': offbrand_no_geo,
        'geo_batches': num_batches,
        'batch_size': GEO_BATCH_SIZE
    }
    with open(step2_batch_dir / "summary.json", 'w') as f:
        json.dump(summary, f, indent=2)

    return len(offbrand), len(offbrand_with_geo), num_batches, missing


def main():
    parser = argparse.ArgumentParser(
        description='SQR Pipeline (optional geo step): build geo batches from Step 1 results')
    parser.add_argument('--data-dir', type=Path, default=DEFAULT_DATA_DIR,
                        help=f'Data directory (default: {DEFAULT_DATA_DIR})')
    parser.add_argument('--run', type=int, choices=[1, 2, 3], default=None,
                        help='Process a single run only (default: all 3)')
    args = parser.parse_args()

    print("=" * 60)
    print("SQR Pipeline: Preparing geo batches from Step 1 results")
    print("=" * 60)

    geo_targets_file = args.data_dir / "geo_targets.json"
    if not geo_targets_file.exists():
        print(f"\nERROR: {geo_targets_file} not found.")
        print("Run sqr_prep.py with --geo-tab to enable the optional geo step.")
        return

    runs = [args.run] if args.run else list(range(1, NUM_RUNS + 1))

    total_geo_batches = 0
    all_missing = {}
    for run_num in runs:
        ob_count, ob_with_geo, num_batches, missing = prep_geo_batches(args.data_dir, run_num)
        total_geo_batches += num_batches
        if missing:
            all_missing[run_num] = missing

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Runs processed: {runs}")
    print(f"  Total geo batches created: {total_geo_batches}")

    if all_missing:
        print(f"\n  WARNING: Missing Step 1 batches detected!")
        for run, batches in all_missing.items():
            print(f"    Run {run}: {len(batches)} missing")
        print(f"  Re-run missing Step 1 batches before the geo step.")

    print(f"\n{'=' * 60}")
    print("READY FOR GEO CHECK")
    print(f"  {total_geo_batches} geo batches across {len(runs)} run(s)")
    print(f"  Classify each with references/geo-prompt.md -> write to run{{R}}/step2/")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
