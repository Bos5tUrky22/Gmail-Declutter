import os
import pickle
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Choose your scope(s) here (uncomment one or more lines)
# - Full access (read, send, delete): covers all actions in this script
SCOPES = ['https://mail.google.com/']
# - Modify (read, modify, delete, no sending): still allows deletion
# SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
# - Read-only (list emails, no changes): won’t allow deletion
# SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Note: After changing SCOPES, delete 'token.pickle' to reauthorize

def authenticate_gmail():
    """Authenticate with Gmail API and return the service object."""
    creds = None
    token_file = 'token.pickle'
    
    if os.path.exists(token_file):
        print(f"Found existing {token_file}. If this isn’t your account or you changed SCOPES, delete it first.")
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        try:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    print("Error: 'credentials.json' not found. See README.md for setup instructions.")
                    return None
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=8080)
            
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
        except Exception as e:
            print(f"Authentication failed: {e}")
            return None

    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        print(f"Failed to build Gmail service: {e}")
        return None

def batch_delete_emails(service, message_ids, action_desc):
    """Delete a batch of emails with retries."""
    if not message_ids:
        return 0
    
    retries = 3
    for attempt in range(retries):
        try:
            service.users().messages().batchDelete(
                userId='me',
                body={'ids': message_ids}
            ).execute()
            print(f'{action_desc} {len(message_ids)} emails: {", ".join(message_ids[:3])}...')
            time.sleep(1)
            return len(message_ids)
        except (HttpError, ConnectionResetError) as e:
            if isinstance(e, HttpError) and e.resp.status == 404:
                print(f'Some messages not found, skipping batch.')
                return len(message_ids)
            if attempt < retries - 1:
                print(f'Error on batch (attempt {attempt + 1}/{retries}): {e}. Retrying...')
                time.sleep(2 ** attempt)
            else:
                print(f'Failed to delete batch after {retries} attempts: {e}')
                return 0
    return 0

def delete_old_emails(service, before_date, batch_size=100):
    """Delete all emails before a certain date in batches."""
    if service is None:
        print("Service not available. Aborting.")
        return

    if 'https://www.googleapis.com/auth/gmail.readonly' in SCOPES and len(SCOPES) == 1:
        print("Error: Read-only scope selected. Cannot delete emails. Use 'modify' or 'full' scope.")
        return

    query = f'before:{before_date} -in:trash -in:spam'
    page_token = None
    total_deleted = 0
    message_ids = []

    try:
        while True:
            results = service.users().messages().list(
                userId='me', q=query, pageToken=page_token, maxResults=500
            ).execute()
            messages = results.get('messages', [])
            
            if not messages and not message_ids:
                print(f'No emails found before {before_date} to delete.')
                break

            for message in messages:
                message_ids.append(message['id'])
                if len(message_ids) >= batch_size:
                    total_deleted += batch_delete_emails(service, message_ids, "Deleted (older than 2 years)")
                    message_ids = []

            page_token = results.get('nextPageToken')
            if not page_token:
                if message_ids:
                    total_deleted += batch_delete_emails(service, message_ids, "Deleted (older than 2 years)")
                break

        print(f'Deleted {total_deleted} emails older than {before_date}.')
    except HttpError as e:
        print(f"Error deleting old emails: {e}")

def delete_automated_emails(service, start_date, end_date, batch_size=100):
    """Delete automated emails between start_date and end_date in batches."""
    if service is None:
        print("Service not available. Aborting.")
        return

    if 'https://www.googleapis.com/auth/gmail.readonly' in SCOPES and len(SCOPES) == 1:
        print("Error: Read-only scope selected. Cannot delete emails. Use 'modify' or 'full' scope.")
        return

    query = f'after:{start_date} before:{end_date} unsubscribe -in:trash -in:spam'
    page_token = None
    total_deleted = 0
    message_ids = []

    try:
        while True:
            results = service.users().messages().list(
                userId='me', q=query, pageToken=page_token, maxResults=500
            ).execute()
            messages = results.get('messages', [])
            
            if not messages and not message_ids:
                print(f'No automated emails found between {start_date} and {end_date} to delete.')
                break

            for message in messages:
                message_ids.append(message['id'])
                if len(message_ids) >= batch_size:
                    total_deleted += batch_delete_emails(service, message_ids, "Deleted (automated)")
                    message_ids = []

            page_token = results.get('nextPageToken')
            if not page_token:
                if message_ids:
                    total_deleted += batch_delete_emails(service, message_ids, "Deleted (automated)")
                break

        print(f'Deleted {total_deleted} automated emails between {start_date} and {end_date}.')
    except HttpError as e:
        print(f"Error deleting automated emails: {e}")

def empty_folder(service, folder_query, batch_size=100):
    """Permanently delete all emails in a folder in batches."""
    if service is None:
        print("Service not available. Aborting.")
        return

    if 'https://www.googleapis.com/auth/gmail.readonly' in SCOPES and len(SCOPES) == 1:
        print("Error: Read-only scope selected. Cannot delete emails. Use 'modify' or 'full' scope.")
        return

    page_token = None
    total_deleted = 0
    message_ids = []

    try:
        while True:
            results = service.users().messages().list(
                userId='me', q=folder_query, pageToken=page_token, maxResults=500
            ).execute()
            messages = results.get('messages', [])

            if not messages and not message_ids:
                print(f'No messages found in {folder_query.split(":")[1]} to delete.')
                break

            for message in messages:
                message_ids.append(message['id'])
                if len(message_ids) >= batch_size:
                    total_deleted += batch_delete_emails(service, message_ids, f"Permanently deleted from {folder_query.split(':')[1]}")
                    message_ids = []

            page_token = results.get('nextPageToken')
            if not page_token:
                if message_ids:
                    total_deleted += batch_delete_emails(service, message_ids, f"Permanently deleted from {folder_query.split(':')[1]}")
                break

        print(f'Permanently deleted {total_deleted} messages from {folder_query.split(":")[1]}.')
    except HttpError as e:
        print(f"Error emptying {folder_query.split(':')[1]}: {e}")

def main():
    """Main function to manage Gmail cleanup."""
    service = authenticate_gmail()
    if service is None:
        print("Authentication failed. Exiting.")
        return
    
    # Configurable dates (default: as of March 15, 2025)
    two_years_ago = '2023/03/15'  # Change this to adjust the "older than" cutoff
    six_months_ago = '2024/09/15'  # Change this to adjust the recent cutoff
    
    # Delete emails older than 2 years
    print("Deleting emails older than 2 years...")
    delete_old_emails(service, two_years_ago, batch_size=100)
    
    # Delete automated emails from 2 years to 6 months ago
    print("\nDeleting automated emails from 2 years to 6 months ago...")
    delete_automated_emails(service, two_years_ago, six_months_ago, batch_size=100)
    
    # Empty Trash
    print("\nEmptying Trash folder...")
    empty_folder(service, 'in:trash', batch_size=100)
    
    # Empty Spam
    print("\nEmptying Spam folder...")
    empty_folder(service, 'in:spam', batch_size=100)

if __name__ == '__main__':
    main()
    input("Press Enter to exit...")