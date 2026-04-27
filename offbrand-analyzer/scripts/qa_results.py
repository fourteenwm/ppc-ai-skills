#!/usr/bin/env python3
"""QA script for Off-Brand Analyzer results.

Analyzes the categorization results to identify potential misclassifications,
particularly brand queries incorrectly marked as off-brand.

Reads:
  - "Have Cost" tab (to get brand names per CID)
  - "Have Cost Result" tab (to get classifications)

Reports off-brand precision and lists sample false positives.

Usage:
    python qa_results.py --sheet-id YOUR_SHEET_ID
    python qa_results.py --sheet-id YOUR_SHEET_ID --input-tab "Have Cost" \
        --output-tab "Have Cost Result"

Prerequisites:
    - token.json at project root with Google Sheets scope (or set
      SHEETS_TOKEN_PATH env var)
    - pip install google-auth google-api-python-client
"""

import argparse
import os
import re
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


# Defaults - override via CLI args
DEFAULT_INPUT_TAB = "Have Cost"
DEFAULT_OUTPUT_TAB = "Have Cost Result"

SHEETS_TOKEN_PATH = Path(os.getenv("SHEETS_TOKEN_PATH", "./token.json"))


def load_sheets_service():
    """Load Google Sheets API service."""
    if not SHEETS_TOKEN_PATH.exists():
        raise FileNotFoundError(
            f"Sheets token not found at {SHEETS_TOKEN_PATH.absolute()}\n"
            "Set up OAuth credentials first or set SHEETS_TOKEN_PATH env var."
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


def normalize(text: str) -> str:
    """Normalize text for comparison."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def extract_core_words(brand: str) -> set:
    """Extract core identifying words from a brand name."""
    normalized = normalize(brand)
    # Remove common generic words
    stopwords = {'the', 'at', 'of', 'on', 'in', 'near', 'by', 'apartments', 'apts',
                 'apartment', 'homes', 'home', 'living', 'residences', 'place', 'park'}
    words = set(normalized.split())
    core = words - stopwords
    return core if core else words


def brand_matches_query(brand_names: str, query: str) -> tuple:
    """Check if query matches any variation of the brand names.

    Returns (is_match, reason).
    """
    if not brand_names or not query:
        return False, "no brand names"

    query_norm = normalize(query)
    query_words = set(query_norm.split())

    brands = [b.strip() for b in brand_names.split(',')]

    for brand in brands:
        brand_norm = normalize(brand)
        brand_words = set(brand_norm.split())
        core_words = extract_core_words(brand)

        # Check 1: Direct substring match
        if brand_norm in query_norm or query_norm in brand_norm:
            return True, f"substring match: '{brand}'"

        # Check 2: Core words overlap
        overlap = core_words & query_words
        min_overlap = min(2, len(core_words))
        if len(overlap) >= min_overlap:
            return True, f"core words match: {overlap} from '{brand}'"

        # Check 3: Domain format (brand words concatenated)
        brand_concat = ''.join(brand_norm.split())
        query_concat = ''.join(query_norm.split())
        if brand_concat in query_concat or query_concat in brand_concat:
            return True, f"domain format match: '{brand}'"

        # Check 4: Fuzzy single word brand
        if len(core_words) == 1:
            core_word = list(core_words)[0]
            if core_word in query_words:
                return True, f"single-word brand match: '{core_word}'"

    return False, "no match"


def run_qa(sheet_id: str,
           input_tab: str = DEFAULT_INPUT_TAB,
           output_tab: str = DEFAULT_OUTPUT_TAB,
           verbose: bool = True) -> tuple:
    """Run the off-brand QA analysis.

    Returns (precision, false_positive_rate) as percentages.
    """
    if verbose:
        print("=" * 70)
        print("Off-Brand Analyzer QA Report")
        print("=" * 70)

    service = load_sheets_service()

    # Step 1: Load brand names mapping from input tab
    if verbose:
        print(f"\nLoading brand names from '{input_tab}' tab...")
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"'{input_tab}'!A:H"
    ).execute()

    input_rows = result.get('values', [])[1:]  # Skip header

    # Build CID -> Brand Names mapping
    cid_to_brand = {}
    for row in input_rows:
        if len(row) >= 8:
            cid = row[0] if row[0] else ''
            brand_names = row[7] if len(row) > 7 else ''
            if cid and brand_names and cid not in cid_to_brand:
                cid_to_brand[cid] = brand_names

    if verbose:
        print(f"  Loaded brand names for {len(cid_to_brand)} unique CIDs")

    # Step 2: Load results from output tab
    if verbose:
        print(f"\nLoading results from '{output_tab}' tab...")
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"'{output_tab}'!A:C"
    ).execute()

    result_rows = result.get('values', [])
    if verbose:
        print(f"  Loaded {len(result_rows)} result rows")

    # Step 3: Analyze off-brand classifications
    if verbose:
        print("\nAnalyzing off-brand classifications...")

    off_brand_results = []
    false_positives = []
    true_positives = []
    unknown = []

    for row in result_rows:
        if len(row) < 3:
            continue

        cid, query, category = row[0], row[1], row[2].lower().strip()

        if category != 'off-brand' or cid == 'CID':
            continue

        off_brand_results.append((cid, query, category))

        if cid not in cid_to_brand:
            unknown.append((cid, query, "CID not in brand mapping"))
            continue

        brand_names = cid_to_brand[cid]
        is_match, reason = brand_matches_query(brand_names, query)

        if is_match:
            false_positives.append((cid, query, brand_names, reason))
        else:
            true_positives.append((cid, query, brand_names))

    total_off_brand = len(off_brand_results)
    total_false_positives = len(false_positives)
    total_true_positives = len(true_positives)
    total_unknown = len(unknown)

    if total_off_brand > 0:
        denominator = total_off_brand - total_unknown
        precision = (total_true_positives / denominator) * 100 if denominator > 0 else 0
        false_positive_rate = (total_false_positives / denominator) * 100 if denominator > 0 else 0
    else:
        precision = 100
        false_positive_rate = 0

    if verbose:
        print("\n" + "=" * 70)
        print("QA RESULTS")
        print("=" * 70)

        print(f"\nTotal results marked 'off-brand': {total_off_brand}")
        print(f"  - True positives (correctly off-brand): {total_true_positives}")
        print(f"  - FALSE POSITIVES (should be high intent): {total_false_positives}")
        print(f"  - Unknown (CID not in brand mapping): {total_unknown}")

        print(f"\n" + "-" * 70)
        print(f"OFF-BRAND CLASSIFICATION ACCURACY: {precision:.1f}%")
        print(f"FALSE POSITIVE RATE: {false_positive_rate:.1f}%")
        print("-" * 70)

        if false_positives:
            print(f"\n{'=' * 70}")
            print(f"SAMPLE FALSE POSITIVES (brand queries marked as off-brand)")
            print(f"{'=' * 70}")

            by_cid = {}
            for cid, query, brands, reason in false_positives:
                if cid not in by_cid:
                    by_cid[cid] = {'brands': brands, 'queries': []}
                by_cid[cid]['queries'].append((query, reason))

            for cid, data in list(by_cid.items())[:10]:
                print(f"\nCID: {cid}")
                print(f"Brand Names: {data['brands']}")
                print("Queries incorrectly marked off-brand:")
                for query, reason in data['queries'][:5]:
                    print(f"  - \"{query}\" ({reason})")
                if len(data['queries']) > 5:
                    print(f"  ... and {len(data['queries']) - 5} more")

            if len(by_cid) > 10:
                print(f"\n... and {len(by_cid) - 10} more CIDs with false positives")

        print(f"\n{'=' * 70}")
        print("OVERALL ASSESSMENT")
        print("=" * 70)

        if precision >= 95:
            grade = "EXCELLENT"
        elif precision >= 90:
            grade = "VERY GOOD"
        elif precision >= 85:
            grade = "GOOD"
        elif precision >= 80:
            grade = "ACCEPTABLE"
        elif precision >= 70:
            grade = "NEEDS IMPROVEMENT"
        else:
            grade = "POOR"

        print(f"\nGrade: {grade}")
        print(f"Off-brand precision: {precision:.1f}%")
        print(f"False positives: {total_false_positives} out of {total_off_brand - total_unknown} ({false_positive_rate:.1f}%)")

        if false_positive_rate > 5:
            print("\nRecommendation: Consider further prompt tuning to reduce false positives.")
        elif false_positive_rate > 0:
            print("\nRecommendation: Minor false positives detected. Manual review recommended for edge cases.")
        else:
            print("\nRecommendation: No false positives detected. Prompt is performing well.")

    return precision, false_positive_rate


def main():
    parser = argparse.ArgumentParser(description='Off-Brand Analyzer QA Report')
    parser.add_argument('--sheet-id', required=True,
                        help='Google Sheet ID containing the SQR pipeline tabs')
    parser.add_argument('--input-tab', default=DEFAULT_INPUT_TAB,
                        help=f'Input tab name (default: "{DEFAULT_INPUT_TAB}")')
    parser.add_argument('--output-tab', default=DEFAULT_OUTPUT_TAB,
                        help=f'Output tab name (default: "{DEFAULT_OUTPUT_TAB}")')
    parser.add_argument('--quiet', action='store_true',
                        help='Suppress detailed output, return metrics only')
    args = parser.parse_args()

    run_qa(
        sheet_id=args.sheet_id,
        input_tab=args.input_tab,
        output_tab=args.output_tab,
        verbose=not args.quiet,
    )


# Backward-compat entry point for qa_gate.py which invokes main() expecting
# a (precision, false_positive_rate) return value.
def _legacy_main():
    """Legacy entry point kept for import compatibility."""
    # Only works if SHEET_ID env var is set
    sheet_id = os.getenv("SHEET_ID")
    if not sheet_id:
        raise ValueError(
            "SHEET_ID env var not set. When importing qa_results.py, call "
            "run_qa(sheet_id=...) directly instead of main()."
        )
    return run_qa(sheet_id=sheet_id)


if __name__ == '__main__':
    main()
