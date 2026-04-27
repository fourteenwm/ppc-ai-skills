#!/usr/bin/env python3
"""
Create a Google Spreadsheet for your workspace reports.

Two modes:
1. Simple (default): Creates sheet in Drive root using Sheets API
 - Works with existing 'spreadsheets' scope
 - No folder organization

2. Folder mode: Creates sheet in specific Drive folder using Drive API
 - Requires 'drive.file' scope
 - Use --folder or --client flags

Usage:
 python create_spreadsheet.py "Report Name"
 python create_spreadsheet.py "Report Name" --folder FOLDER_ID
 python create_spreadsheet.py "Report Name" --client example-client
"""

import sys
import json
import argparse
import os
from pathlib import Path

# Resolve paths relative to your workspace root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
AUTH_DIR = PROJECT_ROOT / 'auth' / 'google'
TOKEN_PATH = AUTH_DIR / 'sheets_token.json'
CREDS_PATH = AUTH_DIR / 'credentials.json'
CLIENT_FOLDERS_PATH = AUTH_DIR / 'client_folders.json'


def get_credentials():
    """Load OAuth credentials from token file."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except ImportError:
        print("Error: google-auth library not installed", file=sys.stderr)
        print("Run: pip install google-auth google-auth-oauthlib google-api-python-client", file=sys.stderr)
        sys.exit(1)

    if not TOKEN_PATH.exists():
        print(f"Error: Token file not found at {TOKEN_PATH}", file=sys.stderr)
        print("\nRun: python auth/google/setup_sheets_auth.py", file=sys.stderr)
        sys.exit(1)

    with open(TOKEN_PATH, 'r') as f:
        token_data = json.load(f)

    creds = Credentials(
        token=token_data.get('token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
        client_id=token_data.get('client_id'),
        client_secret=token_data.get('client_secret'),
        scopes=token_data.get('scopes', ['https://www.googleapis.com/auth/spreadsheets'])
    )

    # Refresh if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Save refreshed token
        with open(TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())

    return creds


def has_drive_scope(creds) -> bool:
    """Check if credentials have Drive scope for folder operations."""
    scopes = creds.scopes or []
    drive_scopes = ['https://www.googleapis.com/auth/drive',
                    'https://www.googleapis.com/auth/drive.file']
    return any(scope in scopes for scope in drive_scopes)


def create_spreadsheet_simple(name: str) -> dict:
    """Create spreadsheet in Drive root using Sheets API (works with existing scope)."""
    try:
        from googleapiclient.discovery import build
    except ImportError:
        print("Error: google-api-python-client not installed", file=sys.stderr)
        sys.exit(1)

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    spreadsheet = {
        'properties': {
            'title': name
        },
        'sheets': [{
            'properties': {
                'title': 'Data',
                'gridProperties': {
                    'frozenRowCount': 1
                }
            }
        }]
    }

    result = service.spreadsheets().create(
        body=spreadsheet,
        fields='spreadsheetId,spreadsheetUrl,properties,sheets.properties'
    ).execute()

    # Get the actual sheet ID from the response
    sheet_id = 0
    if result.get('sheets'):
        sheet_id = result['sheets'][0]['properties'].get('sheetId', 0)

    return {
        'id': result['spreadsheetId'],
        'name': result['properties']['title'],
        'webViewLink': result['spreadsheetUrl'],
        'sheetId': sheet_id
    }


def create_spreadsheet_in_folder(name: str, folder_id: str) -> dict:
    """Create spreadsheet in specific folder using Drive API (requires drive.file scope)."""
    try:
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
    except ImportError:
        print("Error: google-api-python-client not installed", file=sys.stderr)
        sys.exit(1)

    creds = get_credentials()

    if not has_drive_scope(creds):
        print("Error: Drive scope not available in current credentials", file=sys.stderr)
        print("\nYour current token only has 'spreadsheets' scope.", file=sys.stderr)
        print("To create sheets in folders, you need to re-authenticate with Drive scope.", file=sys.stderr)
        print("\nTo add Drive scope, update auth/google/setup_sheets_auth.py SCOPES to:", file=sys.stderr)
        print("  SCOPES = ['https://www.googleapis.com/auth/spreadsheets',", file=sys.stderr)
        print("            'https://www.googleapis.com/auth/drive.file']", file=sys.stderr)
        print("\nThen delete sheets_token.json and re-run setup_sheets_auth.py", file=sys.stderr)
        print("\nFor now, creating in Drive root instead...", file=sys.stderr)
        return create_spreadsheet_simple(name)

    drive_service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.spreadsheet',
        'parents': [folder_id]
    }

    try:
        file = drive_service.files().create(
            body=file_metadata,
            fields='id,name,webViewLink,parents',
            supportsAllDrives=True
        ).execute()
        return file
    except HttpError as e:
        if 'insufficientPermissions' in str(e):
            print("Error: Insufficient permissions for Drive operations", file=sys.stderr)
            print("Falling back to simple creation...", file=sys.stderr)
            return create_spreadsheet_simple(name)
        raise


def get_client_folder(client_name: str) -> str:
    """Get folder ID for a client from config."""
    if not CLIENT_FOLDERS_PATH.exists():
        return None

    with open(CLIENT_FOLDERS_PATH, 'r') as f:
        config = json.load(f)

    clients = config.get('clients', {})
    return clients.get(client_name) or clients.get(client_name.lower())


def apply_header_formatting(spreadsheet_id: str, sheet_id: int = 0):
    """Apply professional blue formatting to header row."""
    try:
        from googleapiclient.discovery import build
    except ImportError:
        return

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    requests = [
        # Format header row - Google Blue background, white text, bold
        {
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 0,
                    'endRowIndex': 1,
                    'startColumnIndex': 0,
                    'endColumnIndex': 26
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {
                            'red': 0.102,
                            'green': 0.451,
                            'blue': 0.91
                        },
                        'textFormat': {
                            'foregroundColor': {
                                'red': 1,
                                'green': 1,
                                'blue': 1
                            },
                            'bold': True,
                            'fontSize': 11
                        },
                        'horizontalAlignment': 'CENTER',
                        'verticalAlignment': 'MIDDLE'
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)'
            }
        }
    ]

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()


def auto_resize_columns(spreadsheet_id: str, sheet_id: int = 0):
    """Auto-resize all columns to fit content."""
    try:
        from googleapiclient.discovery import build
    except ImportError:
        return

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    request = {
        'requests': [{
            'autoResizeDimensions': {
                'dimensions': {
                    'sheetId': sheet_id,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': 26
                }
            }
        }]
    }

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=request
    ).execute()


def list_available_clients():
    """List all configured client folders."""
    if not CLIENT_FOLDERS_PATH.exists():
        print("No client folders configured.", file=sys.stderr)
        print(f"\nTo add clients, create {CLIENT_FOLDERS_PATH}:", file=sys.stderr)
        print(json.dumps({
            "clients": {
                "example-client": "FOLDER_ID_HERE",
                "client-name": "FOLDER_ID_HERE"
            }
        }, indent=2), file=sys.stderr)
        return

    with open(CLIENT_FOLDERS_PATH, 'r') as f:
        config = json.load(f)

    print("\nConfigured clients:")
    for client in config.get('clients', {}).keys():
        print(f"  --client {client}")


def main():
    parser = argparse.ArgumentParser(
        description='Create a Google Spreadsheet for your workspace reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Competitive Analysis - Example Client"
  %(prog)s "Report" --folder 1ABC123xyz
  %(prog)s "Report" --client example-client
  %(prog)s --list-clients

Note: Without --folder or --client, creates in Drive root (works with current auth).
      Folder placement requires 'drive.file' scope (see error message for setup).
        """
    )
    parser.add_argument('name', nargs='?', help='Spreadsheet name')
    parser.add_argument('--folder', '-f', help='Google Drive folder ID')
    parser.add_argument('--client', '-c', help='Client name (looks up folder from config)')
    parser.add_argument('--list-clients', '-l', action='store_true', help='List available clients')
    parser.add_argument('--no-format', action='store_true', help='Skip header formatting')

    args = parser.parse_args()

    if args.list_clients:
        list_available_clients()
        return

    if not args.name:
        parser.error("Spreadsheet name is required")

    # Determine if we need folder placement
    folder_id = None
    if args.folder:
        folder_id = args.folder
    elif args.client:
        folder_id = get_client_folder(args.client)
        if not folder_id:
            print(f"Warning: Client '{args.client}' not found in config", file=sys.stderr)
            print("Creating in Drive root instead", file=sys.stderr)

    # Create the spreadsheet
    print(f"Creating spreadsheet: {args.name}", file=sys.stderr)

    if folder_id:
        print(f"Target folder: {folder_id}", file=sys.stderr)
        result = create_spreadsheet_in_folder(args.name, folder_id)
    else:
        print("Location: Drive root (no folder specified)", file=sys.stderr)
        result = create_spreadsheet_simple(args.name)

    # Apply formatting unless disabled
    if not args.no_format:
        sheet_id = result.get('sheetId', 0)
        apply_header_formatting(result['id'], sheet_id)

    # Output result as JSON (remove internal sheetId from output)
    output = {k: v for k, v in result.items() if k != 'sheetId'}
    print(json.dumps(output, indent=2))
    print(f"\nSheet URL: {result.get('webViewLink')}", file=sys.stderr)


if __name__ == '__main__':
    main()
