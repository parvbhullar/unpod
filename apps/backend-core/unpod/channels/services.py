import os
import base64
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class GoogleService:
    """Class to handle Gmail API authentication and email processing."""
    
    def __init__(self, creds_file):
        self.creds_file = creds_file
        self.service = self.authenticate_gmail()

    def authenticate_gmail(self):
        """Authenticate with the Gmail API using OAuth2."""
        creds = None
        if os.path.exists('token.json'):  # Check if token is saved
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Token refresh failed: {e}")
                    creds = None

            if not creds:
                flow = InstalledAppFlow.from_client_secrets_file(self.creds_file, SCOPES)
                creds = flow.run_local_server(port=0)

                # Save the credentials for future use
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())

        # Build Gmail API service
        service = build('gmail', 'v1', credentials=creds)
        return service

    def get_user_info(self):
        """Fetch and return the user's Gmail profile information."""
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            return profile  
        except Exception as error:
            print(f'An error occurred while fetching user info: {error}')
            return {'emailAddress': 'Unknown', 'name': 'Unknown'}

    def list_messages(self):
        """List the emails from the Gmail account."""
        try:
            results = self.service.users().messages().list(userId='me').execute()
            messages = results.get('messages', [])
            return messages
        except Exception as error:
            print(f'An error occurred while listing emails: {error}')
            return []
