#!/usr/bin/env python3
"""
Generate OAuth2 refresh token for Google Ads API access — plus the Google
Sheets access the rest of this skill catalog expects from the same token.

Usage:
    python generate_credentials.py --client-secrets client_secret.json

This script opens a browser for Google OAuth authentication and outputs
a refresh token that you'll add to your google-ads.yaml file.

Requirements:
    pip install google-auth google-auth-oauthlib
"""

import argparse
import json
import os
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

# One token, three scopes — this repo's house pattern.
#
# Skills that write their reports to Google Sheets (non-serving-keyword-scanner,
# ads-checker, rsa-refresh, rsa-single-account, sqr-pipeline, and others) reuse
# the refresh_token from google-ads.yaml for the Sheets API / gspread instead of
# running a second OAuth setup. A refresh token's scopes are fixed at consent
# time — they can't be added later — so the Sheets scopes must be granted HERE,
# or every Sheets step in the catalog 403s while Ads queries work fine.
SCOPES = [
    "https://www.googleapis.com/auth/adwords",         # Google Ads API
    "https://www.googleapis.com/auth/spreadsheets",    # read/write report sheets
    "https://www.googleapis.com/auth/drive.readonly",  # locate sheets (gspread)
]


def main():
    parser = argparse.ArgumentParser(
        description="Generate OAuth2 refresh token for Google Ads API"
    )
    parser.add_argument(
        "--client-secrets",
        required=True,
        help="Path to client_secret.json downloaded from Google Cloud Console",
    )
    args = parser.parse_args()

    # Verify the file exists and is valid JSON
    try:
        with open(args.client_secrets, "r") as f:
            secrets = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {args.client_secrets}")
        print("Download this from Google Cloud Console → APIs & Services → Credentials")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: {args.client_secrets} is not valid JSON")
        sys.exit(1)

    # Check it has the expected structure
    if "installed" not in secrets and "web" not in secrets:
        print("Error: client_secret.json doesn't look right.")
        print("Make sure you downloaded the OAuth client ID JSON (not a service account key).")
        sys.exit(1)

    print("Opening browser for Google authentication...")
    print("Sign in with the Google account that has Google Ads access.")
    print("If Google shows individual permission checkboxes, tick ALL of them\n"
          "(Google Ads, Google Sheets, Drive read-only).\n")

    # Google's consent screen can grant a subset of the requested scopes
    # (granular consent). Without this, oauthlib hard-fails on the mismatch;
    # with it, we finish the flow and warn about what's missing below.
    os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

    flow = InstalledAppFlow.from_client_secrets_file(args.client_secrets, scopes=SCOPES)
    credentials = flow.run_local_server(port=0)

    granted = set(credentials.scopes or [])
    missing = [s for s in SCOPES if s not in granted]

    print("\n" + "=" * 60)
    print("SUCCESS! Here are your credentials:\n")
    print(f"Your refresh token is: {credentials.refresh_token}")
    print(f"\nCopy this token into your google-ads.yaml file.")
    print(
        "\nThis one token covers Google Ads AND Google Sheets/Drive-read —\n"
        "the skills in this catalog that write reports to Sheets reuse it\n"
        "straight from google-ads.yaml (no second OAuth setup)."
    )
    if missing:
        print("\nWARNING: Google did not grant these requested permissions:")
        for scope in missing:
            print(f"  - {scope}")
        print(
            "Skills that write to Google Sheets will fail with 403 errors.\n"
            "Re-run this script and tick every checkbox on the consent screen."
        )
    print("=" * 60)
    print(
        "\nIMPORTANT: If your OAuth consent screen is External and still in\n"
        '"Testing" status, Google expires this token after 7 DAYS.\n'
        "Fix it permanently: Cloud Console -> OAuth consent screen ->\n"
        "Publish App (push to production), then re-run this script once.\n"
        "Internal apps are not affected."
    )


if __name__ == "__main__":
    main()
