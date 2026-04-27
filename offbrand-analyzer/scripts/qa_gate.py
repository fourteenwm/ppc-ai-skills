#!/usr/bin/env python3
"""Unified QA Gate for Search Query Analysis Pipeline.

Runs QA validation on the Off-Brand Analyzer results, and optionally on
GEO Conflict Analyzer results if the sibling skill's qa_results.py is
installed. Calculates a combined success rate and determines if the
pipeline passes QA.

Usage:
    python qa_gate.py --sheet-id YOUR_SHEET_ID
    python qa_gate.py --sheet-id YOUR_SHEET_ID --json
    python qa_gate.py --sheet-id YOUR_SHEET_ID --threshold 90

Prerequisites:
    - token.json at project root with Google Sheets scope (or set
      SHEETS_TOKEN_PATH env var)
    - Off-brand QA module at ./qa_results.py (beside this file)
    - Optional: GEO QA module at ../../geo-conflict-analyzer/scripts/qa_results.py
      (if the geo-conflict-analyzer skill is installed as a sibling)
    - pip install google-auth google-api-python-client
"""

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
SKILLS_ROOT = SKILL_DIR.parent  # sibling skills live here (e.g. geo-conflict-analyzer/)

# Defaults - override via CLI args
DEFAULT_OFFBRAND_OUTPUT_TAB = "Have Cost Result"
DEFAULT_GEO_OUTPUT_TAB = "Review 2: Have Cost Result - GEO"
DEFAULT_LOG_DIR = Path(os.getenv("QA_LOG_DIR", "./logs"))

SHEETS_TOKEN_PATH = Path(os.getenv("SHEETS_TOKEN_PATH", "./token.json"))


def load_module(name: str, path: Path):
    """Dynamically load a Python module from path."""
    spec = spec_from_file_location(name, path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def clear_results_tabs(sheet_id: str,
                       offbrand_tab: str = DEFAULT_OFFBRAND_OUTPUT_TAB,
                       geo_tab: str = DEFAULT_GEO_OUTPUT_TAB,
                       verbose: bool = True) -> bool:
    """Clear the output tabs to prepare for a fresh run.

    Clears both the offbrand output tab and (if it exists) the GEO output tab.
    Input tabs typically have formula-driven status columns that auto-reset
    when output is cleared.

    Returns True if clearing succeeded.
    """
    if verbose:
        print("\n" + "-" * 70)
        print("CLEARING OUTPUT TABS")
        print("-" * 70)

    try:
        service = load_sheets_service()

        if verbose:
            print(f"  Clearing '{offbrand_tab}'...")
        service.spreadsheets().values().clear(
            spreadsheetId=sheet_id,
            range=f"'{offbrand_tab}'!A2:Z"
        ).execute()
        if verbose:
            print(f"    Cleared.")

        if verbose:
            print(f"  Clearing '{geo_tab}'...")
        try:
            service.spreadsheets().values().clear(
                spreadsheetId=sheet_id,
                range=f"'{geo_tab}'!A2:Z"
            ).execute()
            if verbose:
                print(f"    Cleared.")
        except Exception as geo_err:
            # GEO tab may not exist; that's fine
            if verbose:
                print(f"    Skipped ({geo_err})")

        if verbose:
            print("\n  Output tabs cleared.")
        return True

    except Exception as e:
        if verbose:
            print(f"\n  ERROR clearing tabs: {e}")
        return False


def identify_error_patterns(errors: list, error_type: str) -> list:
    """Analyze errors to identify common patterns."""
    patterns = []
    if not errors:
        return patterns

    reason_counts = Counter(e.get('reason', 'unknown') for e in errors)
    for reason, count in reason_counts.most_common(5):
        examples = [e for e in errors if e.get('reason') == reason][:3]
        patterns.append({
            "pattern": reason,
            "count": count,
            "examples": examples
        })

    return patterns


def generate_error_analysis(qa_result: dict, log_dir: Path, attempt: int = 3) -> str:
    """Generate a detailed error analysis report after QA failures.

    Returns path to generated report file.
    """
    timestamp = datetime.now()
    filename = f"qa-failure-{timestamp.strftime('%Y%m%d-%H%M%S')}.md"
    filepath = log_dir / filename

    log_dir.mkdir(parents=True, exist_ok=True)

    offbrand = qa_result.get("off_brand", {})
    geo = qa_result.get("geo", {})
    combined_rate = qa_result.get("combined_rate", 0)

    offbrand_patterns = identify_error_patterns(
        offbrand.get("sample_errors", []), "offbrand"
    )
    geo_patterns = identify_error_patterns(
        geo.get("sample_errors", []), "geo"
    )

    report = f"""# QA Failure Analysis

**Date:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**Attempts:** {attempt}
**Final Combined Success Rate:** {combined_rate:.1f}%
**Threshold:** {qa_result.get('threshold', 95)}%

---

## Summary

The QA gate failed after {attempt} attempts. This report analyzes the error patterns to help improve the analysis prompts.

| Step | Success Rate | Status |
|------|-------------|--------|
| Off-Brand Analyzer | {offbrand.get('precision', 0):.1f}% | {'PASS' if offbrand.get('precision', 0) >= 95 else 'FAIL'} |
| GEO Conflict Analyzer | {geo.get('success_rate', 0):.1f}% | {'PASS' if geo.get('success_rate', 0) >= 95 else 'FAIL'} |
| **Combined** | **{combined_rate:.1f}%** | **FAIL** |

---

## Off-Brand Analysis (Step 1)

**Precision:** {offbrand.get('precision', 0):.1f}%
**False Positive Rate:** {offbrand.get('false_positive_rate', 0):.1f}%

"""

    if offbrand_patterns:
        report += "### Error Patterns Identified\n\n"
        for i, pattern in enumerate(offbrand_patterns, 1):
            report += f"**{i}. {pattern['pattern']}** ({pattern['count']} errors)\n\n"
            for ex in pattern['examples']:
                if isinstance(ex, dict):
                    report += f"- Query: \"{ex.get('query', 'N/A')}\"\n"
                    report += f"  - CID: {ex.get('cid', 'N/A')}\n"
                    report += f"  - Brand Names: {ex.get('brand_names', 'N/A')}\n\n"
    else:
        report += "*No specific patterns identified in off-brand errors.*\n\n"

    report += """### Sample Errors

| CID | Query | Category | Should Be | Brand Names |
|-----|-------|----------|-----------|-------------|
"""

    for error in offbrand.get("sample_errors", [])[:10]:
        if isinstance(error, dict):
            report += f"| {error.get('cid', '')} | {error.get('query', '')} | {error.get('category', 'off-brand')} | high intent | {error.get('brand_names', '')} |\n"

    report += f"""

---

## GEO Conflict Analysis (Step 2)

**Success Rate:** {geo.get('success_rate', 0):.1f}%
**False Positives (FAIL -> should be PASS):** {geo.get('false_positives', 0)}
**False Negatives (PASS -> should be FAIL):** {geo.get('false_negatives', 0)}

"""

    if geo_patterns:
        report += "### Error Patterns Identified\n\n"
        for i, pattern in enumerate(geo_patterns, 1):
            report += f"**{i}. {pattern['pattern']}** ({pattern['count']} errors)\n\n"
            for ex in pattern['examples']:
                if isinstance(ex, dict):
                    report += f"- Query: \"{ex.get('query', 'N/A')}\"\n"
                    report += f"  - CID: {ex.get('cid', 'N/A')}\n"
                    report += f"  - Result: {ex.get('result', 'N/A')} -> Should be: {ex.get('should_be', 'N/A')}\n"
                    report += f"  - Geo Targets: {ex.get('geo_targets', 'N/A')}\n\n"
    else:
        report += "*No specific patterns identified in GEO errors.*\n\n"

    report += """### Sample Errors

| CID | Query | Result | Should Be | Geo Targets |
|-----|-------|--------|-----------|-------------|
"""

    for error in geo.get("sample_errors", [])[:10]:
        if isinstance(error, dict):
            geo_targets = error.get('geo_targets', [])
            if isinstance(geo_targets, list):
                geo_targets = ', '.join(geo_targets[:3])
            report += f"| {error.get('cid', '')} | {error.get('query', '')} | {error.get('result', '')} | {error.get('should_be', '')} | {geo_targets} |\n"

    report += f"""

---

## Recommendations

### High Priority
1. Review the most common error patterns above
2. Update prompts to handle these edge cases
3. Consider adding more examples to the few-shot prompts

### Medium Priority
1. Expand fuzzy matching rules if abbreviations are causing issues
2. Add more geo variations to the GEO conflict prompt
3. Review directional specificity logic

---

## Next Steps

1. Review this report and identify root causes
2. Update the relevant prompt files:
   - Off-Brand: `offbrand-analyzer/prompt.md`
   - GEO: `geo-conflict-analyzer/prompt.md`
3. Re-run the analysis with `--with-qa` flag
4. Monitor success rate improvements

---

*Generated by QA Gate - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}*
"""

    filepath.write_text(report, encoding='utf-8')

    print(f"\n{'=' * 70}")
    print("ERROR ANALYSIS REPORT GENERATED")
    print("=" * 70)
    print(f"\nReport saved to: {filepath}")
    print("\nReview this report to identify patterns and improve the analysis prompts.")

    return str(filepath)


def run_offbrand_qa(sheet_id: str, input_tab: str, output_tab: str) -> dict:
    """Run Off-Brand QA analysis."""
    qa_script = SCRIPT_DIR / "qa_results.py"

    if not qa_script.exists():
        return {
            "success_rate": 0,
            "total_checked": 0,
            "false_positives": 0,
            "sample_errors": [],
            "error": f"QA script not found: {qa_script}"
        }

    try:
        qa_module = load_module("offbrand_qa", qa_script)
        precision, false_positive_rate = qa_module.run_qa(
            sheet_id=sheet_id,
            input_tab=input_tab,
            output_tab=output_tab,
            verbose=False,
        )

        return {
            "success_rate": precision,
            "total_checked": -1,
            "false_positives": -1,
            "false_positive_rate": false_positive_rate,
            "sample_errors": []
        }
    except Exception as e:
        return {
            "success_rate": 0,
            "total_checked": 0,
            "false_positives": 0,
            "sample_errors": [],
            "error": str(e)
        }


def run_geo_qa(sheet_id: str) -> dict:
    """Run GEO Conflict QA analysis if the sibling skill is installed.

    Expects geo-conflict-analyzer/scripts/qa_results.py alongside this skill.
    Returns a skip result if the module isn't found.
    """
    qa_script = SKILLS_ROOT / "geo-conflict-analyzer" / "scripts" / "qa_results.py"

    if not qa_script.exists():
        return {
            "success_rate": None,
            "skipped": True,
            "total_checked": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "sample_errors": [],
            "note": (
                f"GEO QA skipped: {qa_script} not found. "
                "Install the geo-conflict-analyzer skill as a sibling to "
                "enable unified QA."
            ),
        }

    try:
        qa_module = load_module("geo_qa", qa_script)
        # GEO qa_results.py is expected to provide run_qa(return_dict=True).
        # If it's an older interface, caller will need to adapt.
        if hasattr(qa_module, 'run_qa'):
            try:
                return qa_module.run_qa(return_dict=True)
            except TypeError:
                return qa_module.run_qa(sheet_id=sheet_id)
        return {
            "success_rate": 0,
            "skipped": True,
            "note": "GEO qa_results.py has no run_qa() function.",
        }
    except Exception as e:
        return {
            "success_rate": 0,
            "total_checked": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "sample_errors": [],
            "error": str(e)
        }


def run_qa_gate(sheet_id: str,
                threshold: float = 95.0,
                input_tab: str = "Have Cost",
                offbrand_output_tab: str = DEFAULT_OFFBRAND_OUTPUT_TAB,
                verbose: bool = True) -> dict:
    """Run full QA gate validation.

    Args:
        sheet_id: Google Sheet ID containing the pipeline tabs
        threshold: Minimum combined success rate to pass (default: 95%)
        input_tab: Input tab name for offbrand QA
        offbrand_output_tab: Output tab name for offbrand results
        verbose: Print detailed output

    Returns:
        dict with pass/fail status and detailed metrics
    """
    if verbose:
        print("=" * 70)
        print("QA GATE - Search Query Analysis Pipeline")
        print("=" * 70)
        print(f"\nThreshold: {threshold}%")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Off-Brand QA
    if verbose:
        print("\n" + "-" * 70)
        print("STEP 1: Off-Brand Analyzer QA")
        print("-" * 70)

    offbrand_result = run_offbrand_qa(sheet_id, input_tab, offbrand_output_tab)
    offbrand_rate = offbrand_result.get("success_rate", 0) or 0

    if verbose:
        print(f"\nOff-Brand Precision: {offbrand_rate:.1f}%")
        if "error" in offbrand_result:
            print(f"Error: {offbrand_result['error']}")

    # GEO QA (optional)
    if verbose:
        print("\n" + "-" * 70)
        print("STEP 2: GEO Conflict Analyzer QA (optional)")
        print("-" * 70)

    geo_result = run_geo_qa(sheet_id)
    geo_skipped = geo_result.get("skipped", False)
    geo_rate = geo_result.get("success_rate", 0) or 0

    if verbose:
        if geo_skipped:
            print(f"\nSkipped. {geo_result.get('note', '')}")
        else:
            print(f"\nGEO Success Rate: {geo_rate:.1f}%")
            if "error" in geo_result:
                print(f"Error: {geo_result['error']}")

    # Combined rate: if GEO was skipped, use offbrand only
    if geo_skipped:
        combined_rate = offbrand_rate
    else:
        combined_rate = (offbrand_rate + geo_rate) / 2
    passed = combined_rate >= threshold

    result = {
        "passed": passed,
        "combined_rate": combined_rate,
        "threshold": threshold,
        "timestamp": datetime.now().isoformat(),
        "off_brand": {
            "precision": offbrand_rate,
            "false_positive_rate": offbrand_result.get("false_positive_rate", 0),
            "total_checked": offbrand_result.get("total_checked", -1),
            "sample_errors": offbrand_result.get("sample_errors", [])
        },
        "geo": {
            "skipped": geo_skipped,
            "success_rate": geo_rate,
            "total_checked": geo_result.get("total_checked", 0),
            "false_positives": geo_result.get("false_positives", 0),
            "false_negatives": geo_result.get("false_negatives", 0),
            "sample_errors": geo_result.get("sample_errors", [])
        }
    }

    if verbose:
        print("\n" + "=" * 70)
        print("QA GATE SUMMARY")
        print("=" * 70)

        print(f"\nOff-Brand Precision:  {offbrand_rate:.1f}%")
        if geo_skipped:
            print(f"GEO Success Rate:     SKIPPED")
        else:
            print(f"GEO Success Rate:     {geo_rate:.1f}%")
        print(f"Combined Rate:        {combined_rate:.1f}%")
        print(f"Threshold:            {threshold:.1f}%")

        print("\n" + "-" * 70)
        if passed:
            print("RESULT: PASSED")
        else:
            print("RESULT: FAILED")
        print("-" * 70)

        if not passed:
            if offbrand_rate < threshold:
                print(f"  - Off-Brand: {offbrand_rate:.1f}% (below threshold)")
            if not geo_skipped and geo_rate < threshold:
                print(f"  - GEO: {geo_rate:.1f}% (below threshold)")

    return result


def main():
    parser = argparse.ArgumentParser(description='QA Gate for Search Query Analysis Pipeline')
    parser.add_argument('--sheet-id', required=True,
                        help='Google Sheet ID containing the SQR pipeline tabs')
    parser.add_argument('--threshold', type=float, default=95.0,
                        help='Minimum combined success rate to pass (default: 95)')
    parser.add_argument('--input-tab', default='Have Cost',
                        help='Input tab name (default: "Have Cost")')
    parser.add_argument('--offbrand-output-tab', default=DEFAULT_OFFBRAND_OUTPUT_TAB,
                        help=f'Offbrand output tab (default: "{DEFAULT_OFFBRAND_OUTPUT_TAB}")')
    parser.add_argument('--log-dir', type=Path, default=DEFAULT_LOG_DIR,
                        help=f'Directory for error analysis reports (default: {DEFAULT_LOG_DIR})')
    parser.add_argument('--generate-report-on-fail', action='store_true',
                        help='Generate error analysis markdown if QA fails')
    parser.add_argument('--json', action='store_true',
                        help='Output JSON format instead of human-readable')
    parser.add_argument('--quiet', action='store_true',
                        help='Suppress detailed output, only show result')
    args = parser.parse_args()

    result = run_qa_gate(
        sheet_id=args.sheet_id,
        threshold=args.threshold,
        input_tab=args.input_tab,
        offbrand_output_tab=args.offbrand_output_tab,
        verbose=not args.json and not args.quiet,
    )

    if not result["passed"] and args.generate_report_on_fail:
        generate_error_analysis(result, args.log_dir)

    if args.json:
        print(json.dumps(result, indent=2))
    elif args.quiet:
        if result["passed"]:
            print(f"PASSED ({result['combined_rate']:.1f}%)")
        else:
            print(f"FAILED ({result['combined_rate']:.1f}%)")

    sys.exit(0 if result["passed"] else 1)


if __name__ == '__main__':
    main()
