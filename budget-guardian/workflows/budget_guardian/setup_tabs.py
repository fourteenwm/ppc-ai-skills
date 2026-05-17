"""One-time setup: create the Guardian Config and Guardian State tabs.

Run locally before the first GitHub Actions run:

    pip install -r requirements.txt
    export GOOGLE_TOKEN_PATH=/path/to/your/sheets-token.json
    export GUARDIAN_SHEET_ID=your_sheet_id
    python -m workflows.budget_guardian.setup_tabs

This will:
  1. Create the "Guardian Config" tab if it doesn't exist, with Kill Switch = ENABLED
  2. Create the "Guardian State" tab if it doesn't exist, with the right headers

It will NOT touch your "Budgets" tab — that's yours to create and maintain.
"""

import os
import sys

from workflows._shared.google_auth import get_sheets_service


def main():
    sheet_id = os.environ.get("GUARDIAN_SHEET_ID", "")
    if not sheet_id:
        print("ERROR: GUARDIAN_SHEET_ID environment variable not set")
        sys.exit(1)

    service = get_sheets_service()

    meta = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    existing_tabs = {s["properties"]["title"] for s in meta["sheets"]}

    requests_list = []

    if "Guardian Config" not in existing_tabs:
        requests_list.append({
            "addSheet": {
                "properties": {
                    "title": "Guardian Config",
                    "gridProperties": {"rowCount": 5, "columnCount": 2},
                }
            }
        })
        print("Will create: Guardian Config")
    else:
        print("Already exists: Guardian Config")

    if "Guardian State" not in existing_tabs:
        requests_list.append({
            "addSheet": {
                "properties": {
                    "title": "Guardian State",
                    "gridProperties": {"rowCount": 100, "columnCount": 6},
                }
            }
        })
        print("Will create: Guardian State")
    else:
        print("Already exists: Guardian State")

    if requests_list:
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={"requests": requests_list},
        ).execute()
        print("Tabs created.")

    batch_data = [
        {
            "range": "'Guardian Config'!A1:B2",
            "values": [
                ["Kill Switch", ""],
                ["ENABLED", ""],
            ],
        },
        {
            "range": "'Guardian State'!A1:F1",
            "values": [
                ["Month", "CID", "Account Name", "Threshold", "Action", "Timestamp"],
            ],
        },
    ]

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=sheet_id,
        body={"valueInputOption": "RAW", "data": batch_data},
    ).execute()
    print("Headers and defaults written.")
    print("Done! Guardian Config kill switch set to ENABLED.")


if __name__ == "__main__":
    main()
