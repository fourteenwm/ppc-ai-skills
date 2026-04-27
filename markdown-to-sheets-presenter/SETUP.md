# Markdown to Sheets Presenter - Setup Guide

## Status: Ready to Use

An existing `./token.json` (or `sheets_token.json`) with the Sheets scope works with this skill.

**Simple mode (default):** Creates sheets in Drive root — works now
**Folder mode (optional):** Creates in specific folders — requires Drive scope upgrade

---

## Quick Test

```bash
cd "."
python .claude/skills/markdown-to-sheets-presenter/scripts/create_spreadsheet.py "Test Report"
```

---

## Usage

### From Claude Code

```
"Make this competitive analysis presentable for the client"
"Export this ad recon to Google Sheets"
"Create a Google Sheet from this report"
```

### From Command Line

```bash
# Simple (creates in Drive root)
python .claude/skills/markdown-to-sheets-presenter/scripts/create_spreadsheet.py "Report Name"

# With folder (requires Drive scope - see below)
python .claude/skills/markdown-to-sheets-presenter/scripts/create_spreadsheet.py "Report Name" --client example-client
```

---

## Optional: Add Folder Support

To create sheets in specific Drive folders (by client), you need Drive scope.

### Step 1: Update your OAuth scopes

In your OAuth setup script, update the scopes from:
```python
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
```

To:
```python
SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive.file']
```

### Step 2: Re-authenticate

```bash
# Delete old token
rm ./token.json

# Re-run your OAuth setup script
python setup_sheets_auth.py
```

### Step 3: Configure client folders

Create `./client_folders.json` at project root:

```json
{
 "clients": {
 "example-client": "FOLDER_ID_FROM_DRIVE_URL",
 "client-name": "FOLDER_ID_FROM_DRIVE_URL"
 }
}
```

**To get folder IDs:**
1. Open Google Drive
2. Navigate to the target folder
3. Copy the ID from the URL: `drive.google.com/drive/folders/THIS_IS_THE_ID`

### Step 4: Test folder creation

```bash
python .claude/skills/markdown-to-sheets-presenter/scripts/create_spreadsheet.py "Test" --client example-client
```

---

## Troubleshooting

### "Drive scope not available"
- Follow the "Add Folder Support" steps above
- Delete sheets_token.json and re-authenticate

### "Client not found"
- Add client to `./client_folders.json`
- Check for typos in client name

### "Token expired"
- The script auto-refreshes tokens
- If still failing, delete `./token.json` and re-run your OAuth setup script
