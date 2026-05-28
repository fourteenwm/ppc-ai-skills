#!/usr/bin/env python3
"""Add Account-Level Negative Keywords - 3-Step SharedSet Approach

Adds account-level negative keywords (Admin > Account Settings > Negative Keywords)
to one or more Google Ads accounts using the confirmed 3-step API path:

  Step 1: Create SharedSet (type=ACCOUNT_LEVEL_NEGATIVE_KEYWORDS)
  Step 2: Add keywords as SharedCriterion entries (PHRASE match, batched)
  Step 3: Create CustomerNegativeCriterion linking the set to the account

Per-account state routing (idempotent):
  - NO_SET:                    full 3-step setup
  - PARTIAL (set exists):      Step 2 only (add missing SharedCriteria)
  - COMPLIANT:                 skip

Usage:
    # Dry-run preview (default)
    python scripts/add_account_negative_keywords.py "Example Account"

    # Multiple accounts
    python scripts/add_account_negative_keywords.py "Account A, Account B"

    # Whole portfolio
    python scripts/add_account_negative_keywords.py --portfolio my-portfolio

    # Generate approval code
    python scripts/add_account_negative_keywords.py "Example Account" --execute

    # Execute after approval
    python scripts/add_account_negative_keywords.py "Example Account" --execute \\
        --approval-code APPROVE-XXXXXXXX

Requires:
    - google-ads.yaml with API credentials
    - accounts.json mapping account names -> CIDs (or pass CIDs directly)
    - A baseline keyword list (one keyword per line)

Optional:
    - --log-sheet-id YOUR_SHEET_ID for central mutation logging
"""

import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import argparse
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import yaml


# =============================================================================
# CONFIG
# =============================================================================

DEFAULT_KEYWORDS_FILE = "sample_baseline_keywords.txt"
DEFAULT_SET_NAME = "Account Negative Keywords"
DEFAULT_MATCH_TYPE = "PHRASE"
SHARED_CRITERION_BATCH_SIZE = 1000
ACTION_TYPE = "ADD_ACCOUNT_NEGATIVE_KEYWORDS"

SCRIPT_DIR = Path(__file__).parent
DEFAULT_LOG_DIR = SCRIPT_DIR.parent / 'logs'
DEFAULT_SESSION_DIR = SCRIPT_DIR.parent / 'sessions'


# =============================================================================
# ACCOUNT RESOLUTION
# =============================================================================

def load_accounts_json(accounts_json_path: Path) -> Dict:
    with open(accounts_json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def resolve_accounts(
    input_text: str,
    accounts_json_path: Path,
    portfolio_filter: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Resolve comma-separated names/CIDs (and optional portfolio) to account list."""
    accounts_data = load_accounts_json(accounts_json_path)
    accounts = accounts_data.get('accounts', {})
    resolved = []

    if portfolio_filter:
        for key, account in accounts.items():
            if account.get('portfolio', '').lower() == portfolio_filter.lower():
                resolved.append({
                    'name': account['name'],
                    'id': account['id'],
                    'portfolio': account.get('portfolio', 'unknown'),
                })

    if input_text:
        not_found = []
        for raw in [s.strip() for s in input_text.split(',') if s.strip()]:
            found = False
            normalized = raw.replace('-', '')

            # Try direct CID match
            if normalized.isdigit():
                for key, account in accounts.items():
                    if account['id'] == normalized:
                        resolved.append({
                            'name': account['name'],
                            'id': account['id'],
                            'portfolio': account.get('portfolio', 'unknown'),
                        })
                        found = True
                        break
                if not found:
                    # CID not in accounts.json — accept as raw CID
                    resolved.append({
                        'name': f"CID {raw}",
                        'id': normalized,
                        'portfolio': 'unknown',
                    })
                    found = True

            if not found:
                raw_lower = raw.lower()
                for key, account in accounts.items():
                    if raw_lower == account['name'].lower():
                        resolved.append({
                            'name': account['name'],
                            'id': account['id'],
                            'portfolio': account.get('portfolio', 'unknown'),
                        })
                        found = True
                        break
                    aliases = account.get('aliases', [])
                    if any(raw_lower == alias.lower() for alias in aliases):
                        resolved.append({
                            'name': account['name'],
                            'id': account['id'],
                            'portfolio': account.get('portfolio', 'unknown'),
                        })
                        found = True
                        break
                    if raw_lower in account['name'].lower():
                        resolved.append({
                            'name': account['name'],
                            'id': account['id'],
                            'portfolio': account.get('portfolio', 'unknown'),
                        })
                        found = True
                        break

            if not found:
                not_found.append(raw)

        if not_found:
            print(f"WARNING: Could not resolve: {', '.join(not_found)}")

    # Dedupe by CID, preserve order
    seen = set()
    deduped = []
    for a in resolved:
        if a['id'] not in seen:
            seen.add(a['id'])
            deduped.append(a)
    return deduped


def format_cid(cid: str) -> str:
    cid = cid.replace('-', '')
    if len(cid) == 10:
        return f"{cid[:3]}-{cid[3:6]}-{cid[6:]}"
    return cid


# =============================================================================
# STATE QUERIES (per account)
# =============================================================================

def query_existing_state(client: GoogleAdsClient, customer_id: str) -> Dict:
    """Query all 3 layers for an account. Returns categorization + IDs."""
    ga = client.get_service("GoogleAdsService")

    # Layer 1: SharedSet
    ss_query = """
        SELECT shared_set.id, shared_set.name, shared_set.status
        FROM shared_set
        WHERE shared_set.type = 'ACCOUNT_LEVEL_NEGATIVE_KEYWORDS'
          AND shared_set.status = 'ENABLED'
    """
    shared_set = None
    try:
        response = ga.search(customer_id=customer_id, query=ss_query)
        for row in response:
            shared_set = {
                'id': row.shared_set.id,
                'name': row.shared_set.name,
                'resource_name': f"customers/{customer_id}/sharedSets/{row.shared_set.id}",
            }
            break  # take first ENABLED set
    except GoogleAdsException as ex:
        print(f"    Layer 1 query error: {ex.failure.errors[0].message}")

    # Layer 2: SharedCriteria (existing keywords)
    existing_keywords = set()
    if shared_set:
        sc_query = f"""
            SELECT shared_criterion.keyword.text
            FROM shared_criterion
            WHERE shared_set.id = {shared_set['id']}
        """
        try:
            response = ga.search(customer_id=customer_id, query=sc_query)
            for row in response:
                kw = row.shared_criterion.keyword.text
                if kw:
                    existing_keywords.add(kw)
        except GoogleAdsException as ex:
            print(f"    Layer 2 query error: {ex.failure.errors[0].message}")

    # Layer 3: CustomerNegativeCriterion (attachment)
    # Note: negative_keyword_list.shared_set reads back empty (API quirk).
    # We can only confirm a NEGATIVE_KEYWORD_LIST CNC exists; can't verify it points to OUR set.
    cnc_attached = False
    cnc_query = """
        SELECT customer_negative_criterion.id, customer_negative_criterion.type
        FROM customer_negative_criterion
        WHERE customer_negative_criterion.type = 'NEGATIVE_KEYWORD_LIST'
    """
    try:
        response = ga.search(customer_id=customer_id, query=cnc_query)
        for row in response:
            cnc_attached = True
            break
    except GoogleAdsException as ex:
        print(f"    Layer 3 query error: {ex.failure.errors[0].message}")

    return {
        'shared_set': shared_set,
        'existing_keywords': existing_keywords,
        'cnc_attached': cnc_attached,
    }


def categorize_account(state: Dict, target_keywords: List[str]) -> Dict:
    """Determine path and what mutations are needed."""
    if not state['shared_set']:
        return {
            'status': 'NO_SET',
            'missing_keywords': target_keywords,
            'reason': 'No ACCOUNT_LEVEL_NEGATIVE_KEYWORDS SharedSet exists',
        }

    missing = [kw for kw in target_keywords if kw not in state['existing_keywords']]

    if not missing:
        return {
            'status': 'COMPLIANT',
            'missing_keywords': [],
            'reason': f"All {len(target_keywords)} baseline keywords present in SharedSet {state['shared_set']['id']}",
        }

    return {
        'status': 'PARTIAL',
        'missing_keywords': missing,
        'reason': f"SharedSet {state['shared_set']['id']} exists, missing {len(missing)} of {len(target_keywords)} keywords",
    }


# =============================================================================
# MUTATIONS
# =============================================================================

def execute_full_3_step(client, customer_id: str, set_name: str, keywords: List[str]) -> Dict:
    """Full 3-step setup: SharedSet + SharedCriteria + CustomerNegativeCriterion."""
    # Step 1
    ss_service = client.get_service("SharedSetService")
    ss_op = client.get_type("SharedSetOperation")
    ss = ss_op.create
    ss.name = set_name
    ss.type_ = client.enums.SharedSetTypeEnum.ACCOUNT_LEVEL_NEGATIVE_KEYWORDS
    ss_response = ss_service.mutate_shared_sets(
        customer_id=customer_id, operations=[ss_op]
    )
    shared_set_resource = ss_response.results[0].resource_name
    shared_set_id = shared_set_resource.split('/')[-1]

    # Step 2
    keywords_added = add_keywords_to_set(client, customer_id, shared_set_resource, keywords)

    # Step 3
    cnc_service = client.get_service("CustomerNegativeCriterionService")
    cnc_op = client.get_type("CustomerNegativeCriterionOperation")
    cnc = cnc_op.create
    cnc.negative_keyword_list.shared_set = shared_set_resource
    cnc_response = cnc_service.mutate_customer_negative_criteria(
        customer_id=customer_id, operations=[cnc_op]
    )
    cnc_resource = cnc_response.results[0].resource_name

    return {
        'path': 'full_3_step',
        'shared_set_id': shared_set_id,
        'shared_set_resource': shared_set_resource,
        'keywords_added': keywords_added,
        'cnc_resource': cnc_resource,
    }


def execute_step_2_only(client, customer_id: str, shared_set_resource: str, missing_keywords: List[str]) -> Dict:
    """Add missing SharedCriteria to an existing SharedSet."""
    keywords_added = add_keywords_to_set(client, customer_id, shared_set_resource, missing_keywords)
    return {
        'path': 'step_2_only',
        'shared_set_resource': shared_set_resource,
        'keywords_added': keywords_added,
    }


def add_keywords_to_set(client, customer_id: str, shared_set_resource: str, keywords: List[str]) -> int:
    """Add a batch of keywords as SharedCriteria. Returns count added."""
    if not keywords:
        return 0

    sc_service = client.get_service("SharedCriterionService")
    total_added = 0

    for i in range(0, len(keywords), SHARED_CRITERION_BATCH_SIZE):
        batch = keywords[i:i + SHARED_CRITERION_BATCH_SIZE]
        ops = []
        for kw in batch:
            op = client.get_type("SharedCriterionOperation")
            sc = op.create
            sc.shared_set = shared_set_resource
            sc.keyword.text = kw
            sc.keyword.match_type = client.enums.KeywordMatchTypeEnum.PHRASE
            ops.append(op)
        response = sc_service.mutate_shared_criteria(
            customer_id=customer_id, operations=ops
        )
        total_added += len(response.results)

    return total_added


# =============================================================================
# LOGGING
# =============================================================================

def log_local(log_dir: Path, account_name, cid, details, success, error, approval_code):
    """Append a row to the local JSONL log."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'account_negs_mutations.jsonl'
    record = {
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'approval_code': approval_code,
        'account_cid': cid,
        'account_name': account_name,
        'action_type': ACTION_TYPE,
        'details': details,
        'success': success,
        'error': error,
    }
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record) + '\n')


def log_sheet(sheet_id: str, credentials_path: str, account_name, cid, details, success, error, approval_code):
    """Append a row to the optional central Google Sheet log."""
    with open(credentials_path, 'r') as f:
        config = yaml.safe_load(f)

    creds = Credentials(
        token=None,
        refresh_token=config['refresh_token'],
        token_uri='https://oauth2.googleapis.com/token',
        client_id=config['client_id'],
        client_secret=config['client_secret'],
        scopes=['https://www.googleapis.com/auth/spreadsheets'],
    )
    creds.refresh(Request())
    service = build('sheets', 'v4', credentials=creds)

    row = [[
        datetime.now(timezone.utc).isoformat(),
        account_name,
        cid,
        ACTION_TYPE,
        details,
        'YES' if success else 'NO',
        error or '',
        approval_code,
    ]]
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range='A:H',
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body={'values': row},
    ).execute()


# =============================================================================
# APPROVAL CODE + SESSION
# =============================================================================

def generate_approval_code() -> str:
    return f"APPROVE-{secrets.token_hex(4).upper()}"


def save_session(session_dir: Path, approval_code: str, payload: Dict) -> Path:
    session_dir.mkdir(parents=True, exist_ok=True)
    session_file = session_dir / f"account_negs_{approval_code}.json"
    with open(session_file, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
    return session_file


def load_session(session_dir: Path, approval_code: str) -> Dict:
    session_file = session_dir / f"account_negs_{approval_code}.json"
    if not session_file.exists():
        raise FileNotFoundError(f"Session file not found: {session_file}")
    with open(session_file, 'r', encoding='utf-8') as f:
        return json.load(f)


# =============================================================================
# PREVIEW + EXECUTION ORCHESTRATION
# =============================================================================

def build_preview(client, accounts: List[Dict], target_keywords: List[str]) -> Dict:
    """Query state for every account and build per-account plan."""
    plan = {}
    for acc in accounts:
        cid = acc['id']
        print(f"\n  Querying state: {acc['name']} (CID: {format_cid(cid)})...")
        state = query_existing_state(client, cid)
        category = categorize_account(state, target_keywords)
        plan[cid] = {
            'account': acc,
            'state': {
                'shared_set_id': state['shared_set']['id'] if state['shared_set'] else None,
                'shared_set_resource': state['shared_set']['resource_name'] if state['shared_set'] else None,
                'existing_kw_count': len(state['existing_keywords']),
                'cnc_attached': state['cnc_attached'],
            },
            'category': category,
        }
        print(f"    -> {category['status']}: {category['reason']}")
    return plan


def print_preview_table(plan: Dict, target_count: int, set_name: str):
    print("\n" + "=" * 80)
    print("DRY-RUN PREVIEW - ACCOUNT-LEVEL NEGATIVE KEYWORDS")
    print("=" * 80)
    print(f"  Target baseline: {target_count} keywords (PHRASE match)")
    print(f"  SharedSet name: \"{set_name}\"")
    print()

    no_set_count = 0
    partial_count = 0
    compliant_count = 0
    total_keywords_to_add = 0
    total_operations = 0

    print(f"{'Account':<40} {'CID':<16} {'Status':<12} {'Add':>5}")
    print("-" * 80)
    for cid, entry in plan.items():
        status = entry['category']['status']
        missing = len(entry['category']['missing_keywords'])
        name = entry['account']['name'][:38]
        print(f"{name:<40} {format_cid(cid):<16} {status:<12} {missing:>5}")

        if status == 'NO_SET':
            no_set_count += 1
            total_keywords_to_add += missing
            total_operations += 1 + missing + 1  # SS + N SC + CNC
        elif status == 'PARTIAL':
            partial_count += 1
            total_keywords_to_add += missing
            total_operations += missing
        else:
            compliant_count += 1

    print("-" * 80)
    print(f"  NO_SET (full 3-step setup):       {no_set_count}")
    print(f"  PARTIAL (Step 2 only):            {partial_count}")
    print(f"  COMPLIANT (skip):                 {compliant_count}")
    print(f"  Total keywords to add:            {total_keywords_to_add}")
    print(f"  Total API mutations:              {total_operations}")
    print("=" * 80)


def execute_plan(client, plan: Dict, set_name: str, approval_code: str,
                 log_dir: Path, log_sheet_id: Optional[str], credentials_path: str) -> List[Dict]:
    """Execute mutations for all non-COMPLIANT accounts. Logs each."""
    results = []
    for cid, entry in plan.items():
        category = entry['category']
        acc = entry['account']
        if category['status'] == 'COMPLIANT':
            continue

        print(f"\n  {acc['name']} (CID: {format_cid(cid)}) - {category['status']}")
        try:
            if category['status'] == 'NO_SET':
                result = execute_full_3_step(
                    client, cid, set_name, category['missing_keywords']
                )
                details = (
                    f"Full 3-step: created SharedSet {result['shared_set_id']}, "
                    f"added {result['keywords_added']} keywords, "
                    f"CNC {result['cnc_resource']}"
                )
            else:  # PARTIAL
                result = execute_step_2_only(
                    client, cid,
                    entry['state']['shared_set_resource'],
                    category['missing_keywords'],
                )
                details = (
                    f"Step 2 only: added {result['keywords_added']} missing keywords "
                    f"to existing SharedSet {entry['state']['shared_set_id']}"
                )
            print(f"    OK - {details}")
            log_local(log_dir, acc['name'], cid, details, True, None, approval_code)
            if log_sheet_id:
                try:
                    log_sheet(log_sheet_id, credentials_path, acc['name'], cid, details, True, None, approval_code)
                except Exception as ex:
                    print(f"    WARNING: Sheet log failed: {ex}")
            results.append({'cid': cid, 'name': acc['name'], 'status': 'success', 'details': details})
        except GoogleAdsException as ex:
            errs = "; ".join(e.message for e in ex.failure.errors)
            details = f"FAILED: {errs}"
            print(f"    {details}")
            log_local(log_dir, acc['name'], cid, details, False, errs, approval_code)
            if log_sheet_id:
                try:
                    log_sheet(log_sheet_id, credentials_path, acc['name'], cid, details, False, errs, approval_code)
                except Exception:
                    pass
            results.append({'cid': cid, 'name': acc['name'], 'status': 'failed', 'error': errs})
        except Exception as ex:
            details = f"FAILED: {ex}"
            print(f"    {details}")
            log_local(log_dir, acc['name'], cid, details, False, str(ex), approval_code)
            results.append({'cid': cid, 'name': acc['name'], 'status': 'failed', 'error': str(ex)})

    return results


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Add account-level negative keywords (3-step SharedSet approach)"
    )
    parser.add_argument(
        'accounts',
        type=str,
        nargs='?',
        default='',
        help='Comma-separated account names or CIDs (omit if using --portfolio)',
    )
    parser.add_argument(
        '--portfolio',
        type=str,
        default=None,
        help='Resolve all accounts in a portfolio from accounts.json',
    )
    parser.add_argument(
        '--keywords-file',
        type=str,
        default=DEFAULT_KEYWORDS_FILE,
        help=f'Path to baseline keywords file (default: {DEFAULT_KEYWORDS_FILE})',
    )
    parser.add_argument(
        '--set-name',
        type=str,
        default=DEFAULT_SET_NAME,
        help=f'SharedSet name to create (default: "{DEFAULT_SET_NAME}")',
    )
    parser.add_argument(
        '--exclude-cid',
        action='append',
        default=[],
        help='Exclude a specific CID (can repeat)',
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute mutations (default is dry-run preview)',
    )
    parser.add_argument(
        '--approval-code',
        type=str,
        default=None,
        help='Approval code to confirm execution',
    )
    parser.add_argument(
        '--accounts-json',
        type=str,
        default='accounts.json',
        help='Path to accounts.json (default: accounts.json in current dir)',
    )
    parser.add_argument(
        '--credentials',
        type=str,
        default='google-ads.yaml',
        help='Path to Google Ads credentials YAML (default: google-ads.yaml)',
    )
    parser.add_argument(
        '--log-sheet-id',
        type=str,
        default=None,
        help='Optional Google Sheet ID for central mutation logging',
    )
    parser.add_argument(
        '--log-dir',
        type=str,
        default=str(DEFAULT_LOG_DIR),
        help=f'Local log directory (default: {DEFAULT_LOG_DIR})',
    )
    parser.add_argument(
        '--session-dir',
        type=str,
        default=str(DEFAULT_SESSION_DIR),
        help=f'Session JSON directory (default: {DEFAULT_SESSION_DIR})',
    )

    args = parser.parse_args()

    if not args.accounts and not args.portfolio:
        parser.error('Must provide accounts or --portfolio')

    accounts_json_path = Path(args.accounts_json)
    if not accounts_json_path.exists():
        print(f"ERROR: accounts.json not found at {accounts_json_path}")
        sys.exit(1)

    # Resolve accounts
    accounts = resolve_accounts(args.accounts, accounts_json_path, portfolio_filter=args.portfolio)
    if args.exclude_cid:
        excluded = {cid.replace('-', '') for cid in args.exclude_cid}
        accounts = [a for a in accounts if a['id'] not in excluded]

    if not accounts:
        print("ERROR: No accounts resolved.")
        sys.exit(1)

    # Load keywords
    keywords_path = Path(args.keywords_file)
    if not keywords_path.is_absolute() and not keywords_path.exists():
        # Try alongside the script
        candidate = SCRIPT_DIR / args.keywords_file
        if candidate.exists():
            keywords_path = candidate
    if not keywords_path.exists():
        print(f"ERROR: Keywords file not found: {keywords_path}")
        sys.exit(1)
    with open(keywords_path, 'r', encoding='utf-8') as f:
        target_keywords = [line.strip() for line in f if line.strip()]
    print(f"Loaded {len(target_keywords)} baseline keywords from {keywords_path.name}")

    # Initialize client
    client = GoogleAdsClient.load_from_storage(args.credentials)

    log_dir = Path(args.log_dir)
    session_dir = Path(args.session_dir)

    # ── DRY-RUN ──────────────────────────────────────────────────────────────
    if not args.execute:
        print(f"\nDRY-RUN: querying state for {len(accounts)} account(s)...")
        plan = build_preview(client, accounts, target_keywords)
        print_preview_table(plan, len(target_keywords), args.set_name)
        print(f"\nTo execute, run with --execute (a fresh approval code will be generated).")
        return

    # ── EXECUTE (with or without approval code) ──────────────────────────────
    if not args.approval_code:
        print(f"\nEXECUTE (pending approval): querying state for {len(accounts)} account(s)...")
        plan = build_preview(client, accounts, target_keywords)
        print_preview_table(plan, len(target_keywords), args.set_name)

        approval_code = generate_approval_code()
        session_payload = {
            'approval_code': approval_code,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'set_name': args.set_name,
            'keywords_file': str(keywords_path),
            'target_keywords': target_keywords,
            'plan': plan,
        }
        session_file = save_session(session_dir, approval_code, session_payload)

        print(f"\nApproval code: {approval_code}")
        print(f"Session saved: {session_file}")
        print(f"\nTo execute the saved plan, re-run with --approval-code {approval_code}")
        return

    # Second pass: load session, execute
    try:
        session = load_session(session_dir, args.approval_code)
    except FileNotFoundError as ex:
        print(f"ERROR: {ex}")
        sys.exit(1)

    plan = session['plan']
    set_name = session['set_name']

    print(f"\nEXECUTING (approval code: {args.approval_code})")
    non_compliant = sum(1 for e in plan.values() if e['category']['status'] != 'COMPLIANT')
    print(f"Accounts to mutate: {non_compliant}")

    results = execute_plan(
        client, plan, set_name, args.approval_code,
        log_dir, args.log_sheet_id, args.credentials,
    )

    success_count = sum(1 for r in results if r['status'] == 'success')
    fail_count = sum(1 for r in results if r['status'] == 'failed')

    print("\n" + "=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)
    print(f"  Accounts mutated successfully: {success_count}")
    print(f"  Accounts failed:               {fail_count}")
    print(f"  Local log:                     {log_dir / 'account_negs_mutations.jsonl'}")
    if args.log_sheet_id:
        print(f"  Sheet log:                     https://docs.google.com/spreadsheets/d/{args.log_sheet_id}")
    print("=" * 80)
    print("\nVerify in UI: Admin -> Account Settings -> Negative Keywords")


if __name__ == "__main__":
    main()
