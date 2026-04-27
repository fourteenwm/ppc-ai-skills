"""
PMax Campaign Builder - Google Ads Editor CSV Generator

Generates a 115-column UTF-16LE tab-delimited CSV importable to Google Ads Editor.
Produces one PMax campaign with one asset group, search themes, positive location,
and 238 negative country exclusions.



Usage (with Google Sheet for ad copy - PREFERRED):
    python build_pmax_csv.py \
        --campaign-name "Pmax: Acme Plumbing" \
        --business-name "Acme Plumbing" \
        --final-url "https://www.acmeplumbing.com/" \
        --city "Dallas" --state "TX" \
        --lat 32.7767 --lon -96.7970 --radius 40 \
        --sheet-id "[SHEET_ID]" \
        --video-ids "XAT3n5wXV1o|UJnLVhDRc54" \
        --remarketing-segments "Account;All visitors (AdWords);All Users of GA" \
        --output "data/pmax-builds/acme-plumbing-pmax.csv"

Usage (with manual pipe-delimited ad copy - FALLBACK ONLY):
    python build_pmax_csv.py \
        --campaign-name "Pmax: Acme Plumbing" \
        --business-name "Acme Plumbing" \
        --final-url "https://www.acmeplumbing.com/" \
        --city "Dallas" --state "TX" \
        --lat 32.7767 --lon -96.7970 --radius 40 \
        --headlines "H1|H2|H3|..." \
        --long-headlines "LH1|LH2|..." \
        --descriptions "D1|D2|..." \
        --video-ids "XAT3n5wXV1o|UJnLVhDRc54" \
        --remarketing-segments "Account;All visitors (AdWords);All Users of GA" \
        --output "data/pmax-builds/acme-plumbing-pmax.csv"
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

TOTAL_COLUMNS = 115
SCRIPT_DIR = Path(__file__).parent
TEMPLATES_DIR = SCRIPT_DIR.parent / "templates"
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent

# 115 column headers matching Google Ads Editor PMax export format
HEADER = [
    "Campaign", "Labels", "Campaign Type", "Networks", "Budget", "Budget type",
    "EU political ads", "Standard conversion goals", "Customer acquisition",
    "Languages", "Bid Strategy Type", "Bid Strategy Name", "Start Date", "End Date",
    "Ad Schedule", "Ad rotation", "Content exclusions", "Targeting method",
    "Exclusion method", "Google Merchant Center feed", "Merchant Identifier",
    "Country of Sale", "Feed label", "Campaign Priority", "Local Inventory Ads",
    "Shopping ads on excluded brands", "Inventory filter", "Audience targeting",
    "Flexible Reach", "Text customization", "Final URL expansion",
    "Image enhancement", "Image generation", "Landing page images",
    "Video enhancement", "Brand guidelines", "Brand business name", "Asset Group",
    "Headline 1", "Headline 2", "Headline 3", "Headline 4", "Headline 5",
    "Headline 6", "Headline 7", "Headline 8", "Headline 9", "Headline 10",
    "Headline 11", "Headline 12", "Headline 13", "Headline 14", "Headline 15",
    "Long headline 1", "Long headline 2", "Long headline 3", "Long headline 4",
    "Long headline 5", "Description 1", "Description 2", "Description 3",
    "Description 4", "Description 5", "Call to action", "Business name",
    "Video ID 1", "Video ID 2", "Video ID 3", "Video ID 4", "Video ID 5",
    "Video ID 6", "Video ID 7", "Video ID 8", "Video ID 9", "Video ID 10",
    "Video ID 11", "Video ID 12", "Video ID 13", "Video ID 14", "Video ID 15",
    "Path 1", "Path 2", "Final URL", "Final mobile URL", "Audience signal",
    "Age demographic", "Gender demographic", "Income demographic",
    "Parental status demographic", "Remarketing audience segments",
    "Interest categories", "Life events", "Custom audience segments",
    "Detailed demographics", "Tracking template", "Final URL suffix",
    "Custom parameters", "Ad Group", "ID", "Location", "Reach", "Location groups",
    "Radius", "Unit", "Bid Modifier", "Criterion Type", "Search theme",
    "Incremental", "Campaign Status", "Ad Group Status", "Asset Group Status",
    "Status", "Approval Status", "Ad strength", "Comment"
]


def empty_row():
    return [""] * TOTAL_COLUMNS


def load_template(name):
    path = TEMPLATES_DIR / name
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_start_date(from_date=None):
    """3 business days from given date (skip weekends)."""
    d = from_date or datetime.now()
    biz_days = 0
    while biz_days < 3:
        d += timedelta(days=1)
        if d.weekday() < 5:  # Mon-Fri
            biz_days += 1
    return d.strftime("%Y-%m-%d")


def compute_end_date():
    """June 30 of current fiscal year."""
    now = datetime.now()
    fy_end = datetime(now.year, 6, 30)
    if now > fy_end:
        fy_end = datetime(now.year + 1, 6, 30)
    return fy_end.strftime("%Y-%m-%d")


def extract_video_id(url_or_id):
    """Extract YouTube video ID from URL or return as-is if already an ID."""
    patterns = [
        r"(?:youtu\.be/|youtube\.com/watch\?v=|youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for pat in patterns:
        m = re.search(pat, url_or_id.strip())
        if m:
            return m.group(1)
    return url_or_id.strip()


def read_ad_copy_from_sheet(sheet_id):
    """Read headlines, long headlines, and descriptions directly from Google Sheet.

    Sheet format (confirmed):
        Row 1: Business name
        Row 2: "PMax Ad Copy"
        Row 3: "Headlines..." label
        Rows 4-18: 15 headlines
        Row 19: "Short Headline..." label (ignored)
        Row 20: Short headline (ignored)
        Row 21: "Long Headline..." label
        Rows 22-26: 5 long headlines
        Row 27: "Descriptions..." label
        Rows 28-32: 5 descriptions

    Returns dict with headlines, long_headlines, descriptions lists.
    """
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    token_path = PROJECT_ROOT / "credentials" / "token.json"
    oauth_path = PROJECT_ROOT / "credentials" / "oauth-client.json"

    with open(token_path) as f:
        token_data = json.load(f)
    with open(oauth_path) as f:
        installed = json.load(f)["installed"]

    creds = Credentials(
        token=token_data.get("access_token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=installed["client_id"],
        client_secret=installed["client_secret"],
        scopes=token_data.get("scope", "").split(),
    )
    if creds.expired:
        creds.refresh(Request())

    sheets = build("sheets", "v4", credentials=creds)

    # Read column A rows 1-35 — full cell content, no truncation
    result = (
        sheets.spreadsheets()
        .values()
        .get(spreadsheetId=sheet_id, range="A1:A35")
        .execute()
    )
    values = result.get("values", [])

    def cell(row_num):
        """Get cell value by 1-based row number."""
        idx = row_num - 1
        if idx < len(values) and values[idx]:
            return values[idx][0].strip()
        return ""

    headlines = [cell(r) for r in range(4, 19) if cell(r)]
    long_headlines = [cell(r) for r in range(22, 27) if cell(r)]
    descriptions = [cell(r) for r in range(28, 33) if cell(r)]

    print(f"  Ad copy from sheet {sheet_id}:")
    print(f"    Headlines: {len(headlines)}")
    print(f"    Long Headlines: {len(long_headlines)}")
    print(f"    Descriptions: {len(descriptions)}")

    return {
        "headlines": headlines,
        "long_headlines": long_headlines,
        "descriptions": descriptions,
    }


def build_campaign_row(args, settings):
    row = empty_row()
    row[0] = args.campaign_name
    row[2] = settings["campaign_type"]
    row[3] = settings["networks"]
    row[4] = str(args.budget_daily)
    row[5] = settings["budget_type"]
    row[6] = settings["eu_political_ads"]
    row[7] = settings["standard_conversion_goals"]
    row[8] = settings["customer_acquisition"]
    row[9] = settings["languages"]
    row[10] = settings["bid_strategy_type"]
    row[12] = args.start_date
    row[13] = args.end_date
    row[14] = settings["ad_schedule"]
    row[15] = settings["ad_rotation"]
    row[16] = settings["content_exclusions"]
    row[17] = settings["targeting_method"]
    row[18] = settings["exclusion_method"]
    row[19] = settings["google_merchant_center_feed"]
    row[23] = settings["campaign_priority"]
    row[24] = settings["local_inventory_ads"]
    row[25] = settings["shopping_ads_excluded_brands"]
    row[26] = settings["inventory_filter"]
    row[27] = settings["audience_targeting"]
    row[28] = settings["flexible_reach"]
    row[29] = settings["text_customization"]
    row[30] = settings["final_url_expansion"]
    row[31] = settings["image_enhancement"]
    row[32] = settings["image_generation"]
    row[33] = settings["landing_page_images"]
    row[34] = settings["video_enhancement"]
    row[35] = settings["brand_guidelines"]
    row[36] = args.business_name
    row[108] = "Enabled"
    return row


def build_asset_group_row(args, audiences, ad_copy):
    row = empty_row()
    row[0] = args.campaign_name
    row[37] = args.asset_group_name

    # Headlines (cols 38-52, up to 15)
    for i, h in enumerate(ad_copy["headlines"][:15]):
        row[38 + i] = h

    # Long headlines (cols 53-57, up to 5)
    for i, lh in enumerate(ad_copy["long_headlines"][:5]):
        row[53 + i] = lh

    # Descriptions (cols 58-62, up to 5)
    for i, d in enumerate(ad_copy["descriptions"][:5]):
        row[58 + i] = d

    # CTA (col 63) - leave empty, Google auto-selects

    # Video IDs (cols 65-79, up to 15)
    video_ids = args.video_ids.split("|") if args.video_ids else []
    for i, vid in enumerate(video_ids[:15]):
        row[65 + i] = extract_video_id(vid)

    # Final URL (col 82)
    row[82] = args.final_url

    # Audience signals
    if args.remarketing_segments:
        row[89] = args.remarketing_segments
    row[90] = audiences["interest_categories"]
    row[91] = audiences["life_events"]
    # Col 92: Custom audience segments - leave empty
    row[93] = audiences["detailed_demographics"]

    row[108] = "Enabled"
    row[110] = "Enabled"  # Asset Group Status
    return row


def build_search_theme_rows(args, themes_config):
    rows = []
    all_themes = list(themes_config["generic"])
    for tmpl in themes_config["location_specific"]:
        theme = tmpl.replace("{city}", args.city).replace("{state}", args.state)
        all_themes.append(theme)

    for theme in all_themes:
        row = empty_row()
        row[0] = args.campaign_name
        row[37] = args.asset_group_name
        row[106] = theme
        row[108] = "Enabled"
        row[110] = "Enabled"
        row[111] = "Enabled"
        rows.append(row)
    return rows


def build_positive_location_row(args):
    row = empty_row()
    row[0] = args.campaign_name
    row[99] = f"({args.radius}mi:{args.lat}:{args.lon})"
    row[102] = str(float(args.radius))
    row[103] = "mi"
    row[108] = "Enabled"
    row[111] = "Enabled"
    return row


def build_negative_location_rows(args, neg_locs):
    rows = []
    for loc in neg_locs:
        row = empty_row()
        row[0] = args.campaign_name
        row[98] = loc["id"]
        row[99] = loc["name"]
        row[100] = loc["reach"]
        row[105] = "Campaign Negative"
        row[108] = "Enabled"
        row[111] = "Enabled"
        rows.append(row)
    return rows


def write_csv(rows, output_path):
    """Write UTF-16LE tab-delimited CSV with BOM."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    lines = []
    lines.append("\t".join(HEADER))
    for row in rows:
        padded = row + [""] * (TOTAL_COLUMNS - len(row))
        lines.append("\t".join(padded[:TOTAL_COLUMNS]))

    content = "\r\n".join(lines) + "\r\n"
    with open(output_path, "w", encoding="utf-16-le", newline="") as f:
        f.write("\ufeff")  # BOM
        f.write(content)

    return output_path


def main():
    parser = argparse.ArgumentParser(description="PMax Campaign Builder CSV Generator")
    parser.add_argument("--campaign-name", required=True, help='e.g., Pmax: Acme Plumbing')
    parser.add_argument("--asset-group-name", default="General")
    parser.add_argument("--business-name", required=True, help="Business name")
    parser.add_argument("--final-url", required=True, help="Business website URL")
    parser.add_argument("--city", required=True)
    parser.add_argument("--state", required=True, help="State abbreviation (e.g., TX)")
    parser.add_argument("--lat", required=True, type=float)
    parser.add_argument("--lon", required=True, type=float)
    parser.add_argument("--radius", default=40, type=float, help="Radius in miles (default: 40)")
    parser.add_argument("--budget-daily", default=10.00, type=float)

    # Ad copy: either --sheet-id OR manual --headlines/--long-headlines/--descriptions
    parser.add_argument("--sheet-id", default=None, help="Google Sheet ID for ad copy (reads rows directly)")
    parser.add_argument("--headlines", default=None, help="Pipe-delimited headlines (up to 15) -- fallback if no --sheet-id")
    parser.add_argument("--long-headlines", default=None, help="Pipe-delimited long headlines (up to 5)")
    parser.add_argument("--descriptions", default=None, help="Pipe-delimited descriptions (up to 5)")

    parser.add_argument("--video-ids", default="", help="Pipe-delimited YouTube video IDs or URLs")
    parser.add_argument("--remarketing-segments", default="", help="Semicolon-delimited remarketing list names")
    parser.add_argument("--start-date", default=None, help="YYYY-MM-DD (default: 3 biz days from now)")
    parser.add_argument("--end-date", default=None, help="YYYY-MM-DD (default: June 30 current FY)")
    parser.add_argument("--output", required=True, help="Output CSV file path")

    args = parser.parse_args()

    # Defaults for dates
    if not args.start_date:
        args.start_date = compute_start_date()
    if not args.end_date:
        args.end_date = compute_end_date()

    # Load ad copy -- prefer sheet, fall back to CLI args
    if args.sheet_id:
        ad_copy = read_ad_copy_from_sheet(args.sheet_id)
    elif args.headlines and args.long_headlines and args.descriptions:
        ad_copy = {
            "headlines": [h.strip() for h in args.headlines.split("|")],
            "long_headlines": [h.strip() for h in args.long_headlines.split("|")],
            "descriptions": [d.strip() for d in args.descriptions.split("|")],
        }
    else:
        print("ERROR: Provide either --sheet-id or all three of --headlines, --long-headlines, --descriptions")
        sys.exit(1)

    # Load templates
    settings = load_template("campaign_settings.json")
    themes = load_template("search_themes.json")
    audiences = load_template("audience_signals.json")
    neg_locs = load_template("negative_locations.json")

    # Build all rows
    all_rows = []
    all_rows.append(build_campaign_row(args, settings))
    all_rows.append(build_asset_group_row(args, audiences, ad_copy))
    all_rows.extend(build_search_theme_rows(args, themes))
    all_rows.append(build_positive_location_row(args))
    all_rows.extend(build_negative_location_rows(args, neg_locs))

    # Write CSV
    output_path = write_csv(all_rows, args.output)

    # Summary
    theme_count = len(themes["generic"]) + len(themes["location_specific"])
    print(f"PMax CSV generated: {output_path}")
    print(f"  Campaign: {args.campaign_name}")
    print(f"  Asset Group: {args.asset_group_name}")
    print(f"  Business: {args.business_name}")
    print(f"  URL: {args.final_url}")
    print(f"  Location: {args.city}, {args.state} ({args.radius}mi radius)")
    print(f"  Budget: ${args.budget_daily}/day")
    print(f"  Dates: {args.start_date} to {args.end_date}")
    print(f"  Headlines: {len(ad_copy['headlines'])}")
    print(f"  Long Headlines: {len(ad_copy['long_headlines'])}")
    print(f"  Descriptions: {len(ad_copy['descriptions'])}")
    video_count = len([v for v in args.video_ids.split("|") if v.strip()]) if args.video_ids else 0
    print(f"  Videos: {video_count}")
    print(f"  Search Themes: {theme_count}")
    print(f"  Negative Locations: {len(neg_locs)}")
    print(f"  Total rows: {len(all_rows)} (+ header)")
    print(f"  Columns: {TOTAL_COLUMNS}")
    print(f"  Encoding: UTF-16LE with BOM")
    print(f"  Ad copy source: {'Google Sheet' if args.sheet_id else 'CLI arguments'}")


if __name__ == "__main__":
    main()
