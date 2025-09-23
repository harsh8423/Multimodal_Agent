import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def google_sheet_reader(document_id: str, sheet_id: str, filters: dict[str, str] | None = None, api_key: str = None):
    """
    Read a Google Sheet (optionally filter rows by column values).

    Parameters:
        document_id (str): Spreadsheet ID (from the URL)
        sheet_id (str): Sheet/tab name (e.g., 'Sheet1')
        filters (dict[str, str] | None): Optional filters {column_name: value}
        api_key (str): Google Sheets API key (optional, will use env var if not provided)

    Returns:
        list[dict]: List of rows as dicts (column_name -> value)
    """
    if api_key is None:
        api_key = os.getenv("GOOGLE_SHEETS_API_KEY")
        if not api_key:
            raise ValueError("Google Sheets API key not provided and GOOGLE_SHEETS_API_KEY environment variable not set")
    
    # Endpoint for reading sheet values
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{document_id}/values/{sheet_id}?key={api_key}"

    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Request failed: {response.status_code}, {response.text}")

    data = response.json()
    values = data.get("values", [])

    if not values:
        return []

    # First row is assumed to be headers
    headers = values[0]
    rows = [dict(zip(headers, row)) for row in values[1:]]

    # If no filters, return all
    if not filters:
        return rows

    # Apply filters (all conditions must match)
    filtered_rows = []
    for row in rows:
        match = all(str(row.get(col, "")).strip() == str(val).strip() for col, val in filters.items())
        if match:
            filtered_rows.append(row)

    return filtered_rows



############################################ APPEND AND UPDATE TO GOOGLE SHEET ############################################

from google.oauth2 import service_account
from googleapiclient.discovery import build

# ====== CONFIG ======
SERVICE_ACCOUNT_FILE = "./backend/tools/service_account.json"  # Path to your service account JSON
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Authenticate once and reuse
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build("sheets", "v4", credentials=creds)
sheet_service = service.spreadsheets()


# ======================
# 1. Append Row Tool
# ======================
def google_sheet_append(spreadsheet_id, sheet_name, row_data: dict):
    """
    Append a row to the Google Sheet.
    - If new columns are provided in row_data, they will be auto-created.
    - row_data: dict where keys=column names, values=cell values
    """

    # Fetch the current header row
    result = sheet_service.values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!1:1"
    ).execute()

    header = result.get("values", [[]])[0]
    existing_cols = list(header)

    # Ensure all columns exist
    for col in row_data.keys():
        if col not in existing_cols:
            existing_cols.append(col)

    # Map row_data to full row
    new_row = []
    for col in existing_cols:
        new_row.append(row_data.get(col, ""))

    # Update header row if new columns were added
    if existing_cols != header:
        sheet_service.values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!1:1",
            valueInputOption="USER_ENTERED",
            body={"values": [existing_cols]}
        ).execute()

    # Append new row
    response = sheet_service.values().append(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A1",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": [new_row]}
    ).execute()

    return response


# ======================
# 2. Update Cell Tool
# ======================



def google_sheet_update(spreadsheet_id, sheet_name, match_column, match_value, update_column, new_value):
    """
    Update a cell based on matching a value in a column.
    Example:
      update_cell(spreadsheet_id, "Sheet1", "Name", "Harsh", "Status", "Active")
    """

    # Get all data
    result = sheet_service.values().get(
        spreadsheetId=spreadsheet_id,
        range=sheet_name
    ).execute()

    values = result.get("values", [])
    if not values:
        return {"error": "Sheet is empty"}

    header = values[0]
    if match_column not in header or update_column not in header:
        return {"error": "Invalid column name"}

    match_idx = header.index(match_column)
    update_idx = header.index(update_column)

    # Find row to update
    row_index = None
    for i, row in enumerate(values[1:], start=2):  # start=2 for 1-based index + header row
        if len(row) > match_idx and row[match_idx] == match_value:
            row_index = i
            break

    if not row_index:
        return {"error": f"No row found with {match_column}={match_value}"}

    # Update the cell
    cell_range = f"{sheet_name}!{chr(65 + update_idx)}{row_index}"
    response = sheet_service.values().update(
        spreadsheetId=spreadsheet_id,
        range=cell_range,
        valueInputOption="USER_ENTERED",
        body={"values": [[new_value]]}
    ).execute()

    return response
