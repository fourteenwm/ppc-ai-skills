"""Google Sheets OAuth helper for GitHub Actions.

Loads user-OAuth credentials from a JSON file pointed to by GOOGLE_TOKEN_PATH
and returns an authenticated Sheets API service. Refreshes the token if expired.
"""

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_sheets_service():
    """Build authenticated Sheets service from GOOGLE_TOKEN_PATH env var."""
    token_path = os.environ.get("GOOGLE_TOKEN_PATH")
    if not token_path:
        raise RuntimeError("GOOGLE_TOKEN_PATH environment variable not set")

    creds = Credentials.from_authorized_user_file(token_path, scopes=SCOPES)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return build("sheets", "v4", credentials=creds)
