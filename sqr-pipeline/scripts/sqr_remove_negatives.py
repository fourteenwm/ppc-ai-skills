#!/usr/bin/env python3
"""SQR Remove Negatives — remove a keyword from a shared negative keyword list.

Maintenance branch of the sqr-pipeline: un-negate a keyword that was added by
mistake. Progressive discovery — each flag narrows the target:

  1. List the account's shared negative keyword lists
  2. List the keywords in one list
  3. Preview the removal (prints a deterministic APPROVAL CODE)
  4. Execute with the approval code

Two-step mutation safety (see mutation-safety skill): the dry-run prints an
approval code derived from the hash of the exact criterion to remove. Re-running
with that code re-computes it from current state; if the target changed, the
code won't match and execution is refused. Never skip the dry-run. Never
auto-approve.

Usage:
    # 1. List shared negative lists for the account
    python sqr_remove_negatives.py --customer-id 1234567890

    # 2. List keywords in a list (by name or ID)
    python sqr_remove_negatives.py --customer-id 1234567890 --list-name "Brand Terms"
    python sqr_remove_negatives.py --customer-id 1234567890 --list-id 9876543210

    # 3. Preview the removal (prints APPROVAL CODE)
    python sqr_remove_negatives.py --customer-id 1234567890 --list-name "Brand" --keyword "apartments near me"

    # 4. Execute with the approval code
    python sqr_remove_negatives.py --customer-id 1234567890 --list-name "Brand" --keyword "apartments near me" APPROVE-XXXXXXXX

Prerequisites:
    - google-ads.yaml at project root (Google Ads API credentials; login_customer_id
      set to your MCC) — see google-ads-api-setup skill
    - pip install google-ads
"""

import sys
import io
import os
import hashlib
import argparse

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def query_shared_sets(ads_client, customer_id):
    """Query all enabled shared negative keyword lists for an account."""
    ga_service = ads_client.get_service("GoogleAdsService")
    query = """
        SELECT
            shared_set.id,
            shared_set.name,
            shared_set.member_count,
            shared_set.status
        FROM shared_set
        WHERE shared_set.type = NEGATIVE_KEYWORDS
            AND shared_set.status = ENABLED
        ORDER BY shared_set.name
    """
    results = []
    try:
        response = ga_service.search(customer_id=customer_id, query=query)
        for row in response:
            results.append({
                "id": row.shared_set.id,
                "name": row.shared_set.name,
                "member_count": row.shared_set.member_count,
            })
    except GoogleAdsException as ex:
        print(f"  ERROR querying shared sets: {ex.failure.errors[0].message}")
    return results


def query_shared_criteria(ads_client, customer_id, shared_set_id):
    """Query all keywords in a shared negative keyword list."""
    ga_service = ads_client.get_service("GoogleAdsService")
    query = f"""
        SELECT
            shared_criterion.criterion_id,
            shared_criterion.keyword.text,
            shared_criterion.keyword.match_type,
            shared_criterion.resource_name
        FROM shared_criterion
        WHERE shared_set.id = {shared_set_id}
        ORDER BY shared_criterion.keyword.text
    """
    results = []
    try:
        response = ga_service.search(customer_id=customer_id, query=query)
        for row in response:
            results.append({
                "criterion_id": row.shared_criterion.criterion_id,
                "keyword_text": row.shared_criterion.keyword.text,
                "match_type": row.shared_criterion.keyword.match_type.name,
                "resource_name": row.shared_criterion.resource_name,
            })
    except GoogleAdsException as ex:
        print(f"  ERROR querying shared criteria: {ex.failure.errors[0].message}")
    return results


def search_keywords_in_list(criteria, keyword_query):
    """Find a keyword in the criteria list (exact match first, then partial)."""
    keyword_lower = keyword_query.lower().strip()
    exact = [c for c in criteria if c["keyword_text"].lower() == keyword_lower]
    if exact:
        return exact
    return [c for c in criteria if keyword_lower in c["keyword_text"].lower()]


def compute_approval_code(customer_id, shared_set_id, criterion) -> str:
    """Deterministic APPROVAL CODE from the hash of the exact removal target."""
    key = f"{customer_id}|{shared_set_id}|{criterion['criterion_id']}|{criterion['keyword_text']}"
    digest = hashlib.sha256(key.encode('utf-8')).hexdigest()[:8].upper()
    return f"APPROVE-{digest}"


def remove_shared_criterion(ads_client, customer_id, resource_name):
    """Remove a single shared criterion (negative keyword) from a shared set."""
    shared_criterion_service = ads_client.get_service("SharedCriterionService")
    operation = ads_client.get_type("SharedCriterionOperation")
    operation.remove = resource_name
    response = shared_criterion_service.mutate_shared_criteria(
        customer_id=customer_id,
        operations=[operation],
    )
    return [r.resource_name for r in response.results]


def run(args):
    print("=" * 80)
    print("SQR — REMOVE NEGATIVE FROM SHARED KEYWORD LIST")
    print("=" * 80)
    print()

    if not os.path.exists(args.config):
        print(f"ERROR: Google Ads credentials not found at {args.config}")
        print("See google-ads-api-setup skill for setup.")
        sys.exit(1)

    customer_id = args.customer_id.replace('-', '').strip()
    ads_client = GoogleAdsClient.load_from_storage(args.config)
    print(f"Account CID: {customer_id}\n")

    # Step 1: shared sets
    shared_sets = query_shared_sets(ads_client, customer_id)
    if not shared_sets:
        print("No shared negative keyword lists found for this account.")
        return

    # Step 2: select the target list
    target_set = None
    if args.list_id:
        for ss in shared_sets:
            if str(ss["id"]) == str(args.list_id):
                target_set = ss
                break
        if not target_set:
            print(f"ERROR: No shared set with ID {args.list_id} found.\n")
            print("Available shared sets:")
            for ss in shared_sets:
                print(f"  [{ss['id']}] {ss['name']} ({ss['member_count']} keywords)")
            return
    elif args.list_name:
        list_lower = args.list_name.lower()
        matches = [ss for ss in shared_sets if list_lower in ss["name"].lower()]
        if len(matches) == 1:
            target_set = matches[0]
        elif len(matches) > 1:
            print(f"Multiple lists match '{args.list_name}':")
            for ss in matches:
                print(f"  [{ss['id']}] {ss['name']} ({ss['member_count']} keywords)")
            print("\nUse --list-id to specify the exact list.")
            return
        else:
            print(f"ERROR: No shared set matching '{args.list_name}'.\n")
            print("Available shared sets:")
            for ss in shared_sets:
                print(f"  [{ss['id']}] {ss['name']} ({ss['member_count']} keywords)")
            return
    else:
        print("Shared Negative Keyword Lists:")
        print("-" * 60)
        for ss in shared_sets:
            print(f"  [{ss['id']}] {ss['name']} ({ss['member_count']} keywords)")
        print("\nRe-run with --list-name or --list-id to select a list.")
        return

    print(f"Target List: {target_set['name']} (ID: {target_set['id']}, "
          f"{target_set['member_count']} keywords)\n")

    # Step 3: select the keyword
    criteria = query_shared_criteria(ads_client, customer_id, target_set["id"])
    if not args.keyword:
        if not criteria:
            print("No keywords found in this list.")
            return
        print(f"Keywords in '{target_set['name']}' ({len(criteria)} total):")
        print("-" * 60)
        for c in criteria:
            print(f"  [{c['criterion_id']}] \"{c['keyword_text']}\" ({c['match_type']})")
        print("\nRe-run with --keyword to select a keyword to remove.")
        return

    matches = search_keywords_in_list(criteria, args.keyword)
    if not matches:
        print(f"ERROR: Keyword '{args.keyword}' not found in list '{target_set['name']}'.")
        print("Search the list with --keyword (partial match supported).")
        return
    if len(matches) > 1:
        print(f"Multiple keywords match '{args.keyword}':")
        for c in matches:
            print(f"  [{c['criterion_id']}] \"{c['keyword_text']}\" ({c['match_type']})")
        print("\nProvide a more specific --keyword to narrow down.")
        return

    target = matches[0]
    expected_code = compute_approval_code(customer_id, target_set["id"], target)

    print(f"Keyword to remove: \"{target['keyword_text']}\" ({target['match_type']})")
    print(f"Criterion ID: {target['criterion_id']}")
    print(f"Resource: {target['resource_name']}")
    print()

    # Step 4: dry-run vs execute
    if args.approval_code is None:
        print("=" * 80)
        print(f"APPROVAL CODE: {expected_code}")
        print("=" * 80)
        print("\nTo remove this keyword, re-run with the code above appended:")
        print(f"  python sqr_remove_negatives.py --customer-id {customer_id} "
              f"--list-id {target_set['id']} --keyword \"{target['keyword_text']}\" {expected_code}")
        print("\nThe code is a hash of the exact target. If the list changes before you")
        print("execute, the code will no longer match and the removal will be refused.")
        return

    if args.approval_code != expected_code:
        print("=" * 80)
        print("ERROR: Approval code mismatch.")
        print("=" * 80)
        print(f"  Provided: {args.approval_code}")
        print(f"  Expected: {expected_code}")
        print("\nRe-run without a code to get a fresh approval code.")
        sys.exit(1)

    try:
        remove_shared_criterion(ads_client, customer_id, target["resource_name"])
        print("=" * 80)
        print(f"REMOVED: \"{target['keyword_text']}\" from \"{target_set['name']}\"")
        print("=" * 80)
    except GoogleAdsException as ex:
        msg = str(ex.failure.errors[0].message) if ex.failure.errors else str(ex)
        print(f"ERROR: {msg}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Remove negative keywords from shared negative keyword lists.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  python sqr_remove_negatives.py --customer-id 1234567890\n"
               "  python sqr_remove_negatives.py --customer-id 1234567890 --list-name \"Brand Terms\"\n"
               "  python sqr_remove_negatives.py --customer-id 1234567890 --list-name \"Brand\" --keyword \"apartments near me\"\n"
               "  python sqr_remove_negatives.py --customer-id 1234567890 --list-name \"Brand\" --keyword \"apartments near me\" APPROVE-XXXXXXXX\n",
    )
    parser.add_argument("--customer-id", "-c", required=True,
                        help="Numeric Google Ads customer ID (digits, dashes ok)")
    parser.add_argument("--list-name", "-l", default=None,
                        help="Shared negative keyword list name (partial match supported)")
    parser.add_argument("--list-id", default=None,
                        help="Shared negative keyword list ID (exact match)")
    parser.add_argument("--keyword", "-k", default=None,
                        help="Keyword text to remove (exact or partial match)")
    parser.add_argument("--config", default="google-ads.yaml",
                        help="Google Ads credentials YAML (default: ./google-ads.yaml)")
    parser.add_argument("approval_code", nargs="?", default=None,
                        help="APPROVE-XXXXXXXX code from dry-run (omit for preview)")
    args = parser.parse_args()
    run(args)
