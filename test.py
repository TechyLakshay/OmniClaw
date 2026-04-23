# test_gmail.py

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def test_gmail_connection():
    creds = None
    
    # first time → opens browser for auth
    if not os.path.exists('token.json'):
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES
        )
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as f:
            f.write(creds.to_json())
    else:
        creds = Credentials.from_authorized_user_file('token.json')
    
    # connect to Gmail
    service = build('gmail', 'v1', credentials=creds)
    
    # fetch 1 email only
    results = service.users().messages().list(
        userId='me',
        maxResults=50,
        q='is:unread',
    ).execute()
    
    messages = results.get('messages', [])
    
    if messages:
        print("✅ Gmail connected successfully!")
        print(f"✅ Found {len(messages)} message")
        print(f"✅ Message ID: {messages[0]['id']}")
    else:
        print("✅ Connected but no emails found")

if __name__ == "__main__":
    test_gmail_connection()