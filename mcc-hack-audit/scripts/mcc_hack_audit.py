#!/usr/bin/env python3
"""MCC Hack Audit — single-file portfolio-wide manager-link scan.

Walks your full Google Ads MCC tree from `login_customer_id`, pulls
`customer_manager_link` for every account using a parallel ThreadPool, and
classifies each (account, manager) pair as INTERNAL, HOSTILE, EXTERNAL, or
TRUSTED.

Outputs two CSVs by default:
  output/mcc_link_scan_YYYYMMDD.csv             — every (account, manager) pair
  output/mcc_link_scan_YYYYMMDD_SUSPICIOUS.csv  — HOSTILE + EXTERNAL only

Optional Google Sheets upload with --sheet-id (requires gspread).

Runtime: ~2-5 min for 1,000 accounts at 20 workers; ~10 min for 10,000.

Usage:
    python mcc_hack_audit.py
    python mcc_hack_audit.py --sheet-id YOUR_SHEET_ID
    python mcc_hack_audit.py --hostile-list hostile.json
    python mcc_hack_audit.py --trusted-cids 1234567890,0987654321
    python mcc_hack_audit.py --workers 10 --output-dir my-audit
"""

import argparse
import csv
import json
import os
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from threading import Lock

import yaml
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


def load_client(config_path):
    return GoogleAdsClient.load_from_storage(config_path)


def load_login_cid(config_path):
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    cid = str(cfg.get("login_customer_id", "")).replace("-", "").strip()
    if not cid:
        sys.exit("ERROR: login_customer_id not set in your google-ads.yaml")
    return cid


def load_hostile_list(path):
    """Load a JSON dict of {cid: context_string}. Returns {} if not provided."""
    if not path:
        return {}
    if not os.path.exists(path):
        sys.exit(f"ERROR: --hostile-list path not found: {path}")
    with open(path) as f:
        raw = json.load(f)
    return {str(k).replace("-", ""): str(v) for k, v in raw.items()}


def parse_trusted_cids(cids_arg):
    """Parse a comma-separated list of CIDs into a set."""
    if not cids_arg:
        return set()
    return {c.strip().replace("-", "") for c in cids_arg.split(",") if c.strip()}


def walk_mcc_tree(client, login_cid):
    """Walk customer_client from the login MCC. Returns (accounts, internal_managers).

    accounts: list of dicts for every node in the tree (managers + clients)
    internal_managers: list of dicts where cc.manager == True (these are YOUR tree)
    """
    print(f"Walking MCC tree from {login_cid}...")
    ga = client.get_service("GoogleAdsService")
    query = """
        SELECT
            customer_client.id,
            customer_client.descriptive_name,
            customer_client.status,
            customer_client.manager,
            customer_client.level,
            customer_client.hidden,
            customer_client.test_account
        FROM customer_client
    """
    rows = list(ga.search(customer_id=login_cid, query=query))
    accounts = []
    managers = []
    for row in rows:
        cc = row.customer_client
        rec = {
            "cid": str(cc.id),
            "name": cc.descriptive_name,
            "status": cc.status.name,
            "level": cc.level,
            "is_manager": cc.manager,
        }
        if cc.manager:
            managers.append(rec)
        accounts.append(rec)
    print(f"  Found {len(accounts)} total accounts ({len(managers)} are internal managers)")
    return accounts, managers


def query_one_account(client, account):
    """Query customer_manager_link for one account. Returns (cid, links, err)."""
    ga = client.get_service("GoogleAdsService")
    query = """
        SELECT
            customer_manager_link.manager_customer,
            customer_manager_link.manager_link_id,
            customer_manager_link.status
        FROM customer_manager_link
    """
    try:
        rows = list(ga.search(customer_id=account["cid"], query=query))
        out = []
        for row in rows:
            ml = row.customer_manager_link
            mcid = ml.manager_customer.split("/")[-1] if ml.manager_customer else ""
            out.append({
                "manager_cid": mcid,
                "link_id": ml.manager_link_id,
                "status": ml.status.name,
            })
        return account["cid"], out, None
    except GoogleAdsException as e:
        msg = str(e).split("\n")[0][:120]
        return account["cid"], [], msg
    except Exception as e:
        return account["cid"], [], f"UNEXPECTED: {type(e).__name__}: {str(e)[:100]}"


def scan_parallel(client, accounts, workers):
    """Run query_one_account across all accounts in parallel."""
    name_by_cid = {a["cid"]: a["name"] for a in accounts}
    status_by_cid = {a["cid"]: a["status"] for a in accounts}

    total = len(accounts)
    print(f"\nScanning {total} accounts with {workers} parallel workers...")

    all_rows = []
    errors = []
    completed = [0]
    lock = Lock()
    start = time.time()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(query_one_account, client, a): a for a in accounts}
        for fut in as_completed(futures):
            cid, links, err = fut.result()
            with lock:
                completed[0] += 1
                n = completed[0]
                if err:
                    errors.append({"cid": cid, "name": name_by_cid.get(cid, ""), "error": err})
                for link in links:
                    all_rows.append({
                        "account_cid": cid,
                        "account_name": name_by_cid.get(cid, ""),
                        "account_status": status_by_cid.get(cid, ""),
                        "manager_cid": link["manager_cid"],
                        "manager_link_id": link["link_id"],
                        "link_status": link["status"],
                    })
                if n % 250 == 0 or n == total:
                    elapsed = time.time() - start
                    rate = n / elapsed if elapsed > 0 else 0
                    eta = (total - n) / rate if rate > 0 else 0
                    print(f"  [{n}/{total}] {elapsed:.0f}s elapsed  rate: {rate:.1f}/s  ETA: {eta:.0f}s  errors: {len(errors)}")

    elapsed = time.time() - start
    print(f"\nScan finished in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print(f"Total links found: {len(all_rows)}")
    print(f"Errors (expected for CANCELED/CLOSED accounts): {len(errors)}")
    return all_rows, errors


def classify(rows, internal_cids, hostile_dict, trusted_cids):
    """Classify each row as INTERNAL / HOSTILE / EXTERNAL / TRUSTED."""
    for r in rows:
        mcid = r["manager_cid"]
        if mcid in hostile_dict:
            r["classification"] = "HOSTILE"
            r["label"] = hostile_dict[mcid]
        elif mcid in internal_cids:
            r["classification"] = "INTERNAL"
            r["label"] = ""
        elif mcid in trusted_cids:
            r["classification"] = "TRUSTED"
            r["label"] = "user-marked trusted (re-audit on a cadence)"
        else:
            r["classification"] = "EXTERNAL"
            r["label"] = ""
    return rows


def write_csvs(all_rows, output_dir):
    """Write the full CSV and the suspicious-only CSV. Returns (all_path, susp_path)."""
    os.makedirs(output_dir, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    all_path = os.path.join(output_dir, f"mcc_link_scan_{today}.csv")
    susp_path = os.path.join(output_dir, f"mcc_link_scan_{today}_SUSPICIOUS.csv")

    fieldnames = [
        "account_cid", "account_name", "account_status",
        "manager_cid", "manager_link_id", "link_status",
        "classification", "label",
    ]

    # Sort full list by account, then link_id desc
    all_rows_sorted = sorted(all_rows, key=lambda r: (r["account_cid"], -r["manager_link_id"]))

    # Suspicious = HOSTILE + EXTERNAL. HOSTILE first, then EXTERNAL by link_id desc (newest first).
    susp = [r for r in all_rows if r["classification"] in ("HOSTILE", "EXTERNAL")]
    susp_sorted = sorted(
        susp,
        key=lambda r: (0 if r["classification"] == "HOSTILE" else 1, -r["manager_link_id"]),
    )

    for path, data in [(all_path, all_rows_sorted), (susp_path, susp_sorted)]:
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(data)

    return all_path, susp_path


def maybe_upload_to_sheets(all_rows, internal_managers, sheet_id):
    """Optional Google Sheets upload. Requires gspread + google-auth."""
    try:
        import gspread
    except ImportError:
        print("WARNING: gspread not installed. Skipping Sheets upload. Run: pip install gspread google-auth")
        return

    print(f"\nUploading to Google Sheet {sheet_id}...")
    gc = gspread.service_account()
    sh = gc.open_by_key(sheet_id)

    fieldnames = [
        "account_cid", "account_name", "account_status",
        "manager_cid", "manager_link_id", "link_status",
        "classification", "label",
    ]

    # Tab 1: All Manager Links
    all_sorted = sorted(all_rows, key=lambda r: (r["account_cid"], -r["manager_link_id"]))
    _write_tab(sh, "All Manager Links", fieldnames, all_sorted)

    # Tab 2: Suspicious Links (HOSTILE + EXTERNAL)
    susp = [r for r in all_rows if r["classification"] in ("HOSTILE", "EXTERNAL")]
    susp_sorted = sorted(
        susp,
        key=lambda r: (0 if r["classification"] == "HOSTILE" else 1, -r["manager_link_id"]),
    )
    _write_tab(sh, "Suspicious Links", fieldnames, susp_sorted)

    # Tab 3: Managers and Their Accounts (pivoted)
    pivot_fields = ["manager_cid", "classification", "label", "account_count"]
    counts = Counter(r["manager_cid"] for r in all_rows)
    sample_by_mcid = {r["manager_cid"]: r for r in all_rows}
    pivoted = [
        {
            "manager_cid": mcid,
            "classification": sample_by_mcid[mcid]["classification"],
            "label": sample_by_mcid[mcid]["label"],
            "account_count": n,
        }
        for mcid, n in counts.most_common()
    ]
    pivoted.sort(key=lambda r: (
        0 if r["classification"] == "HOSTILE" else 1 if r["classification"] == "EXTERNAL" else 2,
        -r["account_count"],
    ))
    _write_tab(sh, "Managers and Their Accounts", pivot_fields, pivoted)

    # Tab 4: Internal Managers (your tree's MCCs)
    int_fields = ["cid", "name", "status", "level"]
    int_rows = [
        {"cid": m["cid"], "name": m["name"], "status": m["status"], "level": m["level"]}
        for m in internal_managers
    ]
    int_rows.sort(key=lambda r: (r["level"], r["name"]))
    _write_tab(sh, "Internal Managers", int_fields, int_rows)

    print(f"  Done: https://docs.google.com/spreadsheets/d/{sheet_id}")


def _write_tab(sh, title, fieldnames, rows):
    """Clear + overwrite a Sheets tab."""
    try:
        ws = sh.worksheet(title)
        ws.clear()
    except Exception:
        ws = sh.add_worksheet(title=title, rows=max(len(rows) + 10, 100), cols=len(fieldnames))
    data = [fieldnames] + [[str(r.get(f, "")) for f in fieldnames] for r in rows]
    ws.update("A1", data)


def report_summary(all_rows, errors):
    """Print final classification summary."""
    counts = Counter(r["classification"] for r in all_rows)
    print("\n" + "=" * 70)
    print("MCC HACK AUDIT — SUMMARY")
    print("=" * 70)
    print(f"Total manager links: {len(all_rows)}")
    print(f"Errors (CANCELED/CLOSED accounts): {len(errors)} (expected)")
    print(f"Distinct managers seen: {len(set(r['manager_cid'] for r in all_rows))}")
    print("")
    print("Classification breakdown:")
    for cls in ("HOSTILE", "EXTERNAL", "TRUSTED", "INTERNAL"):
        print(f"  {cls:10s} {counts.get(cls, 0)}")

    hostile_rows = [r for r in all_rows if r["classification"] == "HOSTILE"]
    if hostile_rows:
        print("\n  WARNING: HOSTILE MCCs ACTIVELY LINKED")
        for r in hostile_rows:
            print(f"    {r['manager_cid']}  -> {r['account_cid']} ({r['account_name']})")
            print(f"      {r['label']}")


def main():
    ap = argparse.ArgumentParser(description="MCC Hack Audit — portfolio-wide manager-link scan")
    ap.add_argument("--config", default="google-ads.yaml", help="Path to google-ads.yaml (default: ./google-ads.yaml)")
    ap.add_argument("--output-dir", default="output", help="Where to write CSVs (default: ./output)")
    ap.add_argument("--workers", type=int, default=20, help="Parallel workers (default: 20)")
    ap.add_argument("--hostile-list", help="Path to JSON file of {cid: context}")
    ap.add_argument("--trusted-cids", help="Comma-separated CIDs to classify as TRUSTED instead of EXTERNAL")
    ap.add_argument("--sheet-id", help="Optional Google Sheet ID for upload (requires gspread)")
    args = ap.parse_args()

    if not os.path.exists(args.config):
        sys.exit(f"ERROR: credentials file not found: {args.config}")

    client = load_client(args.config)
    login_cid = load_login_cid(args.config)
    hostile_dict = load_hostile_list(args.hostile_list)
    trusted_cids = parse_trusted_cids(args.trusted_cids)

    print(f"Logged in via MCC: {login_cid}")
    print(f"Workers: {args.workers}")
    print(f"Hostile list entries: {len(hostile_dict)}")
    print(f"User-marked trusted CIDs: {len(trusted_cids)}\n")

    accounts, internal_managers = walk_mcc_tree(client, login_cid)
    internal_cids = {m["cid"] for m in internal_managers}
    internal_cids.add(login_cid)

    all_rows, errors = scan_parallel(client, accounts, args.workers)
    all_rows = classify(all_rows, internal_cids, hostile_dict, trusted_cids)

    all_path, susp_path = write_csvs(all_rows, args.output_dir)
    print(f"\nCSV outputs:")
    print(f"  All links:       {all_path}")
    print(f"  Suspicious only: {susp_path}")

    if args.sheet_id:
        maybe_upload_to_sheets(all_rows, internal_managers, args.sheet_id)

    report_summary(all_rows, errors)


if __name__ == "__main__":
    main()
