#!/usr/bin/env python3
"""RSA Baseline Performance Snapshot - Capture pre-refresh metrics for before/after measurement.

Runs 3 GAQL queries to capture IWQS, Quality Score component breakdown,
ad-level CTR/conversion rate, ad strength distribution, impression share,
and asset performance label counts. Writes one row to an "RSA Baseline" tab
on the provided Google Sheet.

Can be imported by rsa_refresh_generator.py as Step 0 (before any ad copy
work) or run standalone for ad-hoc baseline captures.

Usage (standalone):
    python rsa_baseline_snapshot.py --cid 1234567890 \
        --account-name "Acme Apartments" --sheet-id YOUR_SHEET_ID

Usage (imported):
    from rsa_baseline_snapshot import capture_baseline, write_baseline_to_sheet

Prerequisites:
    - google-ads.yaml at project root (Google Ads API credentials)
    - token-sheets.json at project root OR a refresh token in google-ads.yaml
      with the spreadsheets scope
    - pip install google-ads gspread google-auth pyyaml
"""

import argparse
import io
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
import gspread
from google.oauth2.credentials import Credentials
import yaml


# Fix encoding for Windows console
if sys.platform == 'win32' and sys.stdout is not None:
    try:
        if hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass


# GAQL Queries
IWQS_COMPONENTS_QUERY = """
    SELECT
        ad_group_criterion.quality_info.quality_score,
        ad_group_criterion.quality_info.creative_quality_score,
        ad_group_criterion.quality_info.post_click_quality_score,
        ad_group_criterion.quality_info.search_predicted_ctr,
        metrics.impressions
    FROM keyword_view
    WHERE segments.date DURING LAST_30_DAYS
        AND ad_group_criterion.status = 'ENABLED'
        AND campaign.status = 'ENABLED'
        AND ad_group.status = 'ENABLED'
"""

AD_LEVEL_QUERY = """
    SELECT
        ad_group_ad.ad.id,
        ad_group_ad.ad.responsive_search_ad.path1,
        metrics.impressions,
        metrics.clicks,
        metrics.conversions
    FROM ad_group_ad
    WHERE segments.date DURING LAST_30_DAYS
        AND ad_group_ad.ad.type = RESPONSIVE_SEARCH_AD
        AND ad_group_ad.status = ENABLED
        AND campaign.status = ENABLED
"""

# Ad strength is an attribute, not a metric — no date segment allowed
AD_STRENGTH_QUERY = """
    SELECT
        ad_group_ad.ad.id,
        ad_group_ad.ad_strength
    FROM ad_group_ad
    WHERE ad_group_ad.ad.type = RESPONSIVE_SEARCH_AD
        AND ad_group_ad.status = ENABLED
        AND campaign.status = ENABLED
"""

IMPRESSION_SHARE_QUERY = """
    SELECT
        campaign.name,
        metrics.search_impression_share,
        metrics.search_budget_lost_impression_share,
        metrics.search_rank_lost_impression_share,
        metrics.impressions
    FROM campaign
    WHERE segments.date DURING LAST_30_DAYS
        AND campaign.advertising_channel_type IN ('SEARCH', 'PERFORMANCE_MAX')
        AND campaign.status = ENABLED
"""

# QS component enum mappings
QS_COMPONENT_MAP = {
    0: "UNSPECIFIED",
    1: "UNKNOWN",
    2: "BELOW_AVERAGE",
    3: "AVERAGE",
    4: "ABOVE_AVERAGE",
}


def classify_iwqs(iwqs: float) -> str:
    """Classify impression-weighted Quality Score against standard benchmarks."""
    if iwqs < 5:
        return "NEEDS WORK"
    elif iwqs < 7:
        return "AVERAGE"
    else:
        return "HEALTHY"


def _component_name(enum_val) -> str:
    """Convert QS component enum to bucket name."""
    if hasattr(enum_val, 'name'):
        return enum_val.name
    val = int(enum_val) if enum_val else 0
    return QS_COMPONENT_MAP.get(val, "UNKNOWN")


def count_asset_labels(performance_data: dict) -> dict:
    """Count BEST / GOOD / LOW / LEARNING / PENDING from asset performance data.

    Args:
        performance_data: Dict keyed by ad_id -> list of asset dicts with a
            'performance_label' key.
    """
    counts = {"BEST": 0, "GOOD": 0, "LOW": 0, "LEARNING": 0, "PENDING": 0}
    for ad_id, assets in performance_data.items():
        for asset in assets:
            label = asset.get("performance_label", "UNKNOWN")
            if label in counts:
                counts[label] += 1
    return counts


def _query_iwqs_components(client: GoogleAdsClient, cid: str) -> dict:
    """Query IWQS and QS component breakdown."""
    ga_service = client.get_service("GoogleAdsService")

    keywords = []  # (qs, impressions) for IWQS
    component_buckets = {
        "ctr": {"ABOVE_AVERAGE": 0, "AVERAGE": 0, "BELOW_AVERAGE": 0},
        "relevance": {"ABOVE_AVERAGE": 0, "AVERAGE": 0, "BELOW_AVERAGE": 0},
        "lp": {"ABOVE_AVERAGE": 0, "AVERAGE": 0, "BELOW_AVERAGE": 0},
    }
    total_kw_impressions = 0
    scored_keywords = 0

    try:
        response = ga_service.search_stream(customer_id=cid, query=IWQS_COMPONENTS_QUERY)
        for batch in response:
            for row in batch.results:
                impr = row.metrics.impressions
                if impr <= 0:
                    continue

                total_kw_impressions += impr
                qs = row.ad_group_criterion.quality_info.quality_score

                if qs and qs > 0:
                    keywords.append((qs, impr))
                    scored_keywords += 1

                # QS components (impression-weighted)
                ctr_label = _component_name(row.ad_group_criterion.quality_info.search_predicted_ctr)
                rel_label = _component_name(row.ad_group_criterion.quality_info.creative_quality_score)
                lp_label = _component_name(row.ad_group_criterion.quality_info.post_click_quality_score)

                for label, bucket in [
                    (ctr_label, "ctr"),
                    (rel_label, "relevance"),
                    (lp_label, "lp"),
                ]:
                    if label in component_buckets[bucket]:
                        component_buckets[bucket][label] += impr

    except GoogleAdsException as ex:
        print(f"  Warning: IWQS query failed: {ex}")
        return {
            "iwqs": None, "iwqs_rating": None, "scored_keywords": 0,
            "total_kw_impressions": 0, "components": component_buckets,
        }

    if keywords:
        total_weighted = sum(qs * impr for qs, impr in keywords)
        total_impr = sum(impr for _, impr in keywords)
        iwqs = total_weighted / total_impr if total_impr > 0 else 0.0
    else:
        iwqs = 0.0

    return {
        "iwqs": round(iwqs, 2),
        "iwqs_rating": classify_iwqs(iwqs) if keywords else "NO DATA",
        "scored_keywords": scored_keywords,
        "total_kw_impressions": total_kw_impressions,
        "components": component_buckets,
    }


def _query_ad_metrics(client: GoogleAdsClient, cid: str) -> dict:
    """Query ad-level CTR, conversion rate, and ad strength distribution."""
    ga_service = client.get_service("GoogleAdsService")

    total_impressions = 0
    total_clicks = 0
    total_conversions = 0.0
    strength_counts = {"EXCELLENT": 0, "GOOD": 0, "AVERAGE": 0, "POOR": 0}

    # Query 1: Ad-level metrics (with date segment)
    try:
        response = ga_service.search_stream(customer_id=cid, query=AD_LEVEL_QUERY)
        for batch in response:
            for row in batch.results:
                total_impressions += row.metrics.impressions
                total_clicks += row.metrics.clicks
                total_conversions += row.metrics.conversions

    except GoogleAdsException as ex:
        print(f"  Warning: Ad metrics query failed: {ex}")
        return {
            "ad_ctr": None, "conversion_rate": None,
            "total_ad_impressions": 0, "total_clicks": 0,
            "total_conversions": 0, "strength_counts": strength_counts,
        }

    # Query 2: Ad strength (no date segment — attribute, not metric)
    try:
        response = ga_service.search_stream(customer_id=cid, query=AD_STRENGTH_QUERY)
        for batch in response:
            for row in batch.results:
                strength = row.ad_group_ad.ad_strength.name if row.ad_group_ad.ad_strength else "UNSPECIFIED"
                if strength in strength_counts:
                    strength_counts[strength] += 1

    except GoogleAdsException as ex:
        print(f"  Warning: Ad strength query failed: {ex}")

    ad_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0.0
    conv_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0.0

    return {
        "ad_ctr": round(ad_ctr, 2),
        "conversion_rate": round(conv_rate, 2),
        "total_ad_impressions": total_impressions,
        "total_clicks": total_clicks,
        "total_conversions": round(total_conversions, 1),
        "strength_counts": strength_counts,
    }


def _query_impression_share(client: GoogleAdsClient, cid: str) -> dict:
    """Query impression share metrics (impression-weighted across campaigns)."""
    ga_service = client.get_service("GoogleAdsService")

    weighted_is = 0.0
    weighted_rank_lost = 0.0
    weighted_budget_lost = 0.0
    total_impressions = 0

    try:
        response = ga_service.search_stream(customer_id=cid, query=IMPRESSION_SHARE_QUERY)
        for batch in response:
            for row in batch.results:
                impr = row.metrics.impressions
                if impr <= 0:
                    continue

                total_impressions += impr

                search_is = row.metrics.search_impression_share
                rank_lost = row.metrics.search_rank_lost_impression_share
                budget_lost = row.metrics.search_budget_lost_impression_share

                if search_is and search_is > 0:
                    weighted_is += search_is * impr
                if rank_lost and rank_lost > 0:
                    weighted_rank_lost += rank_lost * impr
                if budget_lost and budget_lost > 0:
                    weighted_budget_lost += budget_lost * impr

    except GoogleAdsException as ex:
        print(f"  Warning: Impression share query failed: {ex}")
        return {
            "search_is": None, "lost_to_rank": None, "lost_to_budget": None,
        }

    if total_impressions > 0:
        search_is = round(weighted_is / total_impressions * 100, 1)
        lost_to_rank = round(weighted_rank_lost / total_impressions * 100, 1)
        lost_to_budget = round(weighted_budget_lost / total_impressions * 100, 1)
    else:
        search_is = 0.0
        lost_to_rank = 0.0
        lost_to_budget = 0.0

    return {
        "search_is": search_is,
        "lost_to_rank": lost_to_rank,
        "lost_to_budget": lost_to_budget,
    }


def _pct(bucket: dict, key: str) -> str:
    """Calculate impression-weighted percentage for a QS component bucket."""
    total = sum(bucket.values())
    if total == 0:
        return "N/A"
    return str(round(bucket.get(key, 0) / total * 100, 1))


def capture_baseline(
    client: GoogleAdsClient,
    cid: str,
    performance_data: dict,
    account_name: str,
) -> dict:
    """Run all queries, calculate metrics, return baseline dict.

    Args:
        client: Initialized GoogleAdsClient
        cid: Customer ID (no dashes)
        performance_data: Dict from asset performance query (asset labels)
        account_name: Display name for the account
    """
    now = datetime.now()
    cid_clean = cid.replace("-", "")
    cid_formatted = f"{cid_clean[:3]}-{cid_clean[3:6]}-{cid_clean[6:]}"

    print(f"\n  [Baseline] Capturing pre-refresh metrics for {account_name}...")

    print(f"  [Baseline] Query 1/3: IWQS + QS components...")
    iwqs_data = _query_iwqs_components(client, cid_clean)

    print(f"  [Baseline] Query 2/3: Ad CTR, conversion rate, ad strength...")
    ad_data = _query_ad_metrics(client, cid_clean)

    print(f"  [Baseline] Query 3/3: Impression share...")
    is_data = _query_impression_share(client, cid_clean)

    asset_counts = count_asset_labels(performance_data)
    comps = iwqs_data["components"]

    baseline = {
        "account_name": account_name,
        "cid": cid_formatted,
        "capture_date": now.strftime("%Y-%m-%d"),
        "capture_time": now.strftime("%H:%M"),
        "iwqs": iwqs_data["iwqs"],
        "iwqs_rating": iwqs_data["iwqs_rating"],
        "scored_keywords": iwqs_data["scored_keywords"],
        "total_kw_impressions": iwqs_data["total_kw_impressions"],
        "ctr_above": _pct(comps["ctr"], "ABOVE_AVERAGE"),
        "ctr_avg": _pct(comps["ctr"], "AVERAGE"),
        "ctr_below": _pct(comps["ctr"], "BELOW_AVERAGE"),
        "relevance_above": _pct(comps["relevance"], "ABOVE_AVERAGE"),
        "relevance_avg": _pct(comps["relevance"], "AVERAGE"),
        "relevance_below": _pct(comps["relevance"], "BELOW_AVERAGE"),
        "lp_above": _pct(comps["lp"], "ABOVE_AVERAGE"),
        "lp_avg": _pct(comps["lp"], "AVERAGE"),
        "lp_below": _pct(comps["lp"], "BELOW_AVERAGE"),
        "ad_ctr": ad_data["ad_ctr"],
        "conversion_rate": ad_data["conversion_rate"],
        "total_ad_impressions": ad_data["total_ad_impressions"],
        "total_clicks": ad_data["total_clicks"],
        "total_conversions": ad_data["total_conversions"],
        "strength_excellent": ad_data["strength_counts"]["EXCELLENT"],
        "strength_good": ad_data["strength_counts"]["GOOD"],
        "strength_average": ad_data["strength_counts"]["AVERAGE"],
        "strength_poor": ad_data["strength_counts"]["POOR"],
        "assets_best": asset_counts["BEST"],
        "assets_good": asset_counts["GOOD"],
        "assets_low": asset_counts["LOW"],
        "assets_learning": asset_counts["LEARNING"],
        "search_is": is_data["search_is"],
        "lost_to_rank": is_data["lost_to_rank"],
        "lost_to_budget": is_data["lost_to_budget"],
    }

    _print_baseline_summary(baseline)
    return baseline


def _print_baseline_summary(b: dict):
    """Print a compact console summary of baseline metrics."""
    print(f"\n  [Baseline] === {b['account_name']} ({b['cid']}) ===")
    print(f"  IWQS: {_fmt(b['iwqs'])} ({b['iwqs_rating']})")
    print(f"  Scored Keywords: {b['scored_keywords']}  |  KW Impressions: {b['total_kw_impressions']:,}")
    print(f"  Exp CTR:      Above {b['ctr_above']}%  Avg {b['ctr_avg']}%  Below {b['ctr_below']}%")
    print(f"  Ad Relevance: Above {b['relevance_above']}%  Avg {b['relevance_avg']}%  Below {b['relevance_below']}%")
    print(f"  LP Experience: Above {b['lp_above']}%  Avg {b['lp_avg']}%  Below {b['lp_below']}%")
    print(f"  Ad CTR: {_fmt(b['ad_ctr'])}%  |  Conv Rate: {_fmt(b['conversion_rate'])}%")
    print(f"  Ad Impressions: {b['total_ad_impressions']:,}  Clicks: {b['total_clicks']:,}  Conv: {b['total_conversions']}")
    print(f"  Ad Strength: Exc={b['strength_excellent']} Good={b['strength_good']} Avg={b['strength_average']} Poor={b['strength_poor']}")
    print(f"  Assets: Best={b['assets_best']} Good={b['assets_good']} Low={b['assets_low']} Learning={b['assets_learning']}")
    print(f"  Search IS: {_fmt(b['search_is'])}%  Lost Rank: {_fmt(b['lost_to_rank'])}%  Lost Budget: {_fmt(b['lost_to_budget'])}%")


def _fmt(val) -> str:
    """Format a value, returning 'N/A' for None."""
    if val is None:
        return "N/A"
    return str(val)


def _get_sheets_client(
    sheets_token_path: str = "token-sheets.json",
    ads_config_path: str = "google-ads.yaml",
) -> gspread.Client:
    """Create gspread client.

    Prefers a dedicated token-sheets.json (OAuth with spreadsheets scope).
    Falls back to the refresh token in google-ads.yaml if present with
    the spreadsheets scope.
    """
    token_data = None
    if sheets_token_path and os.path.exists(sheets_token_path):
        with open(sheets_token_path, 'r') as f:
            token_data = json.load(f)

    if not token_data:
        # Fallback to google-ads.yaml
        if not os.path.exists(ads_config_path):
            raise FileNotFoundError(
                f"Could not find OAuth credentials.\n"
                f"  Looked for: {sheets_token_path}\n"
                f"  Fell back to: {ads_config_path} (also not found)\n"
                f"Provide --sheets-token or --config with a refresh token "
                f"that has the spreadsheets scope."
            )
        with open(ads_config_path, 'r', encoding='utf-8') as f:
            ads_config = yaml.safe_load(f)

        credentials = Credentials(
            token=None,
            refresh_token=ads_config.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=ads_config.get("client_id"),
            client_secret=ads_config.get("client_secret"),
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.readonly",
            ],
        )
        return gspread.authorize(credentials)

    client_id = token_data.get('client_id')
    client_secret = token_data.get('client_secret')

    if (not client_id or not client_secret) and os.path.exists(ads_config_path):
        with open(ads_config_path, 'r') as f:
            ads_config = yaml.safe_load(f)
            client_id = client_id or ads_config.get('client_id')
            client_secret = client_secret or ads_config.get('client_secret')

    credentials = Credentials(
        token=token_data.get('token') or token_data.get('access_token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri=token_data.get('token_uri', "https://oauth2.googleapis.com/token"),
        client_id=client_id,
        client_secret=client_secret,
        scopes=token_data.get('scopes', ["https://www.googleapis.com/auth/spreadsheets"]),
    )
    return gspread.authorize(credentials)


def write_baseline_to_sheet(
    baseline_data: dict,
    sheet_id: str,
    sheets_token_path: str = "token-sheets.json",
    ads_config_path: str = "google-ads.yaml",
) -> str:
    """Write one baseline row to an 'RSA Baseline' tab. Appends if tab exists.

    Returns the sheet URL.
    """
    if not sheet_id:
        raise ValueError("sheet_id is required")

    tab_name = "RSA Baseline"

    gc = _get_sheets_client(sheets_token_path, ads_config_path)
    spreadsheet = gc.open_by_key(sheet_id)

    headers = [
        "Account Name", "CID", "Capture Date", "Capture Time",
        "IWQS", "IWQS Rating", "Scored Keywords", "Total KW Impressions",
        "Exp CTR Above %", "Exp CTR Avg %", "Exp CTR Below %",
        "Ad Relevance Above %", "Ad Relevance Avg %", "Ad Relevance Below %",
        "LP Experience Above %", "LP Experience Avg %", "LP Experience Below %",
        "Ad CTR %", "Conversion Rate %",
        "Total Ad Impressions", "Total Clicks", "Total Conversions",
        "Strength Excellent", "Strength Good", "Strength Average", "Strength Poor",
        "Assets Best", "Assets Good", "Assets Low", "Assets Learning",
        "Search IS %", "Lost to Rank %", "Lost to Budget %",
    ]

    row = [
        baseline_data["account_name"],
        baseline_data["cid"],
        baseline_data["capture_date"],
        baseline_data["capture_time"],
        _fmt(baseline_data["iwqs"]),
        baseline_data["iwqs_rating"] or "N/A",
        baseline_data["scored_keywords"],
        baseline_data["total_kw_impressions"],
        baseline_data["ctr_above"],
        baseline_data["ctr_avg"],
        baseline_data["ctr_below"],
        baseline_data["relevance_above"],
        baseline_data["relevance_avg"],
        baseline_data["relevance_below"],
        baseline_data["lp_above"],
        baseline_data["lp_avg"],
        baseline_data["lp_below"],
        _fmt(baseline_data["ad_ctr"]),
        _fmt(baseline_data["conversion_rate"]),
        baseline_data["total_ad_impressions"],
        baseline_data["total_clicks"],
        baseline_data["total_conversions"],
        baseline_data["strength_excellent"],
        baseline_data["strength_good"],
        baseline_data["strength_average"],
        baseline_data["strength_poor"],
        baseline_data["assets_best"],
        baseline_data["assets_good"],
        baseline_data["assets_low"],
        baseline_data["assets_learning"],
        _fmt(baseline_data["search_is"]),
        _fmt(baseline_data["lost_to_rank"]),
        _fmt(baseline_data["lost_to_budget"]),
    ]

    try:
        ws = spreadsheet.worksheet(tab_name)
        existing = ws.get_all_values()
        next_row = len(existing) + 1
        ws.update(values=[row], range_name=f"A{next_row}:AG{next_row}")
        print(f"  [Baseline] Appended row {next_row} to '{tab_name}'")
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=tab_name, rows=200, cols=33)
        ws.update(values=[headers], range_name="A1:AG1")
        ws.update(values=[row], range_name="A2:AG2")
        print(f"  [Baseline] Created tab '{tab_name}' with header + 1 row")

    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    print(f"  [Baseline] Sheet: {url}")
    return url


def main():
    """Standalone baseline capture."""
    parser = argparse.ArgumentParser(description="RSA Baseline Performance Snapshot")
    parser.add_argument('--cid', required=True, help='Customer ID (no dashes)')
    parser.add_argument('--account-name', required=True, help='Account display name')
    parser.add_argument('--sheet-id', required=True,
                        help='Google Sheet ID for output (creates "RSA Baseline" tab)')
    parser.add_argument('--config', default='google-ads.yaml',
                        help='Path to google-ads.yaml (default: ./google-ads.yaml)')
    parser.add_argument('--sheets-token', default='token-sheets.json',
                        help='Path to OAuth token with sheets scope (default: ./token-sheets.json)')
    parser.add_argument('--dry-run', action='store_true', help='Preview only, no sheet write')

    args = parser.parse_args()
    cid = args.cid.replace('-', '')

    print("=" * 70)
    print("RSA BASELINE PERFORMANCE SNAPSHOT")
    print("=" * 70)

    client = GoogleAdsClient.load_from_storage(args.config)

    # No performance_data in standalone mode — pass empty dict
    baseline = capture_baseline(client, cid, {}, args.account_name)

    if not args.dry_run:
        write_baseline_to_sheet(baseline, args.sheet_id, args.sheets_token, args.config)
    else:
        print("\n  [DRY RUN] Would write baseline to sheet")

    print("\nDone.")


if __name__ == "__main__":
    main()
