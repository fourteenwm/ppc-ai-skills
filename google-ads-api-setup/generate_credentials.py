#!/usr/bin/env python3
"""
Generate OAuth2 refresh token for Google Ads API access.

Usage:
    python generate_credentials.py --client-secrets client_secret.json

This script opens a browser for Google OAuth authentication and outputs
a refresh token that you'll add to your google-ads.yaml file.

Requirements:
    pip install google-auth google-auth-oauthlib
"""

import argparse
import json
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

# Google Ads API requires this scope
SCOPES = ["https://www.googleapis.com/auth/adwords"]


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
    print("Sign in with the Google account that has Google Ads access.\n")

    flow = InstalledAppFlow.from_client_secrets_file(args.client_secrets, scopes=SCOPES)
    credentials = flow.run_local_server(port=0)

    print("\n" + "=" * 60)
    print("SUCCESS! Here are your credentials:\n")
    print(f"Your refresh token is: {credentials.refresh_token}")
    print(f"\nCopy this token into your google-ads.yaml file.")
    print("=" * 60)


if __name__ == "__main__":
    main()
