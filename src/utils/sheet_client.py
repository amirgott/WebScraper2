import gspread
from google.oauth2.service_account import Credentials
import os
from src.utils.config import get_google_sheet_id, get_service_account_file

class SheetClient:
    def __init__(self):
        """Initialize the Google Sheets client"""
        self.sheet_id = get_google_sheet_id()
        self.service_account_file = get_service_account_file()

        if not self.sheet_id:
            raise ValueError("GOOGLE_SHEET_ID environment variable not set")

        if not self.service_account_file:
            raise ValueError("SERVICE_ACCOUNT_FILE environment variable not set")

        if not os.path.exists(self.service_account_file):
            raise FileNotFoundError(f"Service account file not found: {self.service_account_file}")

        # Authenticate with Google Sheets API
        self.scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.creds = Credentials.from_service_account_file(self.service_account_file, scopes=self.scope)
        self.client = gspread.authorize(self.creds)

        # Open the spreadsheet
        try:
            self.sheet = self.client.open_by_key(self.sheet_id).sheet1
        except Exception as e:
            raise Exception(f"Error opening Google Sheet: {str(e)}")

    def get_headers(self):
        """Get the headers (first row) of the sheet"""
        try:
            return self.sheet.row_values(1)
        except Exception as e:
            print(f"Error getting headers: {str(e)}")
            return []

    def append_event_record(self, event_record):
        """Append an event record to the sheet"""
        try:
            # Get the headers to ensure correct order
            headers = self.get_headers()

            # If no headers exist, add them first
            if not headers and event_record:
                headers = list(event_record.keys())
                self.sheet.append_row(headers)

            # Prepare row values in the same order as headers
            row_values = [event_record.get(header, '') for header in headers]

            # Append the row
            self.sheet.append_row(row_values)
            return True
        except Exception as e:
            print(f"Error appending to sheet: {str(e)}")
            return False

    def get_all_records(self):
        """Get all records from the sheet"""
        try:
            return self.sheet.get_all_records()
        except Exception as e:
            print(f"Error getting records: {str(e)}")
            return []
