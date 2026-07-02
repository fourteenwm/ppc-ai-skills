"""Google Ads OAuth helper for GitHub Actions.

Loads OAuth credentials from a YAML file (pointed to by GOOGLE_ADS_YAML_PATH)
and returns a fresh access token plus the developer_token and login_customer_id
needed for REST API headers.

Expected YAML structure:
    developer_token: "..."
    client_id: "..."
    client_secret: "..."
    refresh_token: "..."
    login_customer_id: "1234567890"
"""

import os

import yaml
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

TOKEN_URI = "https://oauth2.googleapis.com/token"


def get_ads_credentials(yaml_path: str | None = None) -> dict:
    """Load Google Ads credentials from YAML and return auth dict.

    Returns:
        {
            "access_token": str,
            "developer_token": str,
            "login_customer_id": str,
        }
    """
    yaml_path = yaml_path or os.environ.get("GOOGLE_ADS_YAML_PATH")
    if not yaml_path:
        raise RuntimeError("GOOGLE_ADS_YAML_PATH environment variable not set")

    with open(yaml_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    creds = Credentials(
        token=None,
        refresh_token=config["refresh_token"],
        token_uri=TOKEN_URI,
        client_id=config["client_id"],
        client_secret=config["client_secret"],
    )

    creds.refresh(Request())

    return {
        "access_token": creds.token,
        "developer_token": config["developer_token"],
        "login_customer_id": str(config["login_customer_id"]),
    }
