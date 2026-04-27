#!/usr/bin/env python3
"""
Test your Google Ads API connection.

Usage:
    python test_connection.py --config google-ads.yaml

Connects to the API and lists all accounts under your MCC.
If this works, your credentials are set up correctly.

Requirements:
    pip install google-ads pyyaml
"""

import argparse
import sys

import yaml
from google.ads.googleads.client import GoogleAdsClient


def main():
    parser = argparse.ArgumentParser(
        description="Test Google Ads API connection"
    )
    parser.add_argument(
        "--config",
        default="google-ads.yaml",
        help="Path to google-ads.yaml (default: google-ads.yaml)",
    )
    args = parser.parse_args()

    # Load and validate the config file
    try:
        with open(args.config, "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Config file not found: {args.config}")
        print("Copy google-ads.example.yaml to google-ads.yaml and fill in your values.")
        sys.exit(1)

    # Check for placeholder values
    placeholders = ["YOUR_CLIENT_ID", "YOUR_CLIENT_SECRET", "YOUR_REFRESH_TOKEN",
                     "YOUR_DEVELOPER_TOKEN", "YOUR_MCC_ID"]
    for key, value in config.items():
        if isinstance(value, str) and any(p in value for p in placeholders):
            print(f"Error: {key} still has a placeholder value.")
            print("Edit your google-ads.yaml and replace all YOUR_* values with real credentials.")
            sys.exit(1)

    # Try to connect
    print("Connecting to Google Ads API...")

    try:
        client = GoogleAdsClient.load_from_dict(config)
        service = client.get_service("GoogleAdsService")
        customer_service = client.get_service("CustomerService")

        # List accessible accounts
        mcc_id = config.get("login_customer_id", "").replace("-", "")
        query = """
            SELECT
                customer_client.id,
                customer_client.descriptive_name,
                customer_client.manager,
                customer_client.status
            FROM customer_client
            WHERE customer_client.status = 'ENABLED'
                AND customer_client.manager = false
            ORDER BY customer_client.descriptive_name
        """

        response = service.search(customer_id=mcc_id, query=query)

        accounts = []
        for row in response:
            accounts.append({
                "name": row.customer_client.descriptive_name,
                "id": row.customer_client.id,
            })

        print(f"\nSuccess! Found {len(accounts)} accounts under your MCC.\n")
        print("Accounts:")
        for acct in accounts[:20]:
            print(f"  - {acct['name']} (ID: {acct['id']})")

        if len(accounts) > 20:
            print(f"  ... and {len(accounts) - 20} more")

        print(f"\nYour API connection is working. You're all set!")

    except Exception as e:
        error_msg = str(e)
        print(f"\nConnection failed: {error_msg}\n")

        # Provide helpful error messages
        if "invalid_grant" in error_msg.lower():
            print("Your refresh token has expired or been revoked.")
            print("Re-run: python generate_credentials.py --client-secrets client_secret.json")
        elif "developer_token" in error_msg.lower():
            print("Your developer token may not be approved yet.")
            print("Check: Google Ads → Tools & Settings → API Center")
        elif "authentication" in error_msg.lower():
            print("Check that client_id, client_secret, and refresh_token are correct in your YAML.")
        elif "permission" in error_msg.lower():
            print("Your Google account may not have access to this MCC.")
            print("Check your MCC account access in Google Ads.")
        else:
            print("See the troubleshooting section in README.md for common fixes.")

        sys.exit(1)


if __name__ == "__main__":
    main()
