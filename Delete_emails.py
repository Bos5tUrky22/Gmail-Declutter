import os
import pickle
import time
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from datetime import datetime, timedelta

# Define the scopes (adjust as needed)
SCOPES = ['https://mail.google.com/']  # Full access; use 'https://www.googleapis.com/auth/gmail.modify' for read/modify/delete

def authenticate_gmail():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        print("Found existing token.pickle. If this isn’t your account or you changed SCOPES, delete it first.")
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

def delete_emails(service, query, batch_size=100):
    try:
        response = service.users().messages().list(userId='me', q=query).execute()
        messages = response.get('messages', [])
        total_deleted = 0

        while messages:
            batch = messages[:batch_size]
            message_ids = [msg['id'] for msg in batch]
            service.users().messages().batchDelete(userId='me', body={'ids': message_ids}).execute()
            total_deleted += len(batch)
            print(f"Deleted {len(batch)} emails: {', '.join(message_ids[:5]) + ('...' if len(batch) > 5 else '')}")
            time.sleep(1)  # Avoid rate limiting
            messages = messages[batch_size:]

            # Fetch more messages if there are any
            if 'nextPageToken' in response:
                response = service.users().messages().list(userId='me', q=query, pageToken=response['nextPageToken']).execute()
                messages.extend(response.get('messages', []))

        return total_deleted
    except Exception as e:
        print(f"Error deleting emails: {e}")
        return 0

def delete_promotional_emails(service, before_date, batch_size=100):
    try:
        # Use the CATEGORY_PROMOTIONS label and the before: filter
        query = f"in:category_promotions before:{before_date} -in:trash -in:spam"
        response = service.users().messages().list(userId='me', q=query).execute()
        messages = response.get('messages', [])
        total_deleted = 0

        if not messages:
            print(f"No promotional emails found before {before_date} to delete.")
            return 0

        while messages:
            batch = messages[:batch_size]
            message_ids = [msg['id'] for msg in batch]
            service.users().messages().batchDelete(userId='me', body={'ids': message_ids}).execute()
            total_deleted += len(batch)
            print(f"Deleted (promotional) {len(batch)} emails: {', '.join(message_ids[:5]) + ('...' if len(batch) > 5 else '')}")
            time.sleep(1)  # Avoid rate limiting
            messages = messages[batch_size:]

            if 'nextPageToken' in response:
                response = service.users().messages().list(userId='me', q=query, pageToken=response['nextPageToken']).execute()
                messages.extend(response.get('messages', []))

        return total_deleted
    except Exception as e:
        print(f"Error deleting promotional emails: {e}")
        return 0

def empty_folder(service, folder, batch_size=100):
    try:
        response = service.users().messages().list(userId='me', labelIds=[folder]).execute()
        messages = response.get('messages', [])
        total_deleted = 0

        while messages:
            batch = messages[:batch_size]
            message_ids = [msg['id'] for msg in batch]
            service.users().messages().batchDelete(userId='me', body={'ids': message_ids}).execute()
            total_deleted += len(batch)
            print(f"Permanently deleted from {folder.lower()} {len(batch)} emails: {', '.join(message_ids[:5]) + ('...' if len(batch) > 5 else '')}")
            time.sleep(1)  # Avoid rate limiting
            messages = messages[batch_size:]

            if 'nextPageToken' in response:
                response = service.users().messages().list(userId='me', labelIds=[folder], pageToken=response['nextPageToken']).execute()
                messages.extend(response.get('messages', []))

        return total_deleted
    except Exception as e:
        print(f"Error emptying {folder.lower()}: {e}")
        return 0

def main():
    # Dynamically calculate dates based on today's date
    today = datetime.now()
    two_years_ago = (today - timedelta(days=2*365)).strftime('%Y/%m/%d')  # Approx 2 years (730 days)
    six_months_ago = (today - timedelta(days=6*30)).strftime('%Y/%m/%d')  # Approx 6 months (180 days)
    two_months_ago = (today - timedelta(days=2*30)).strftime('%Y/%m/%d')  # Approx 2 months (60 days)

    service = authenticate_gmail()

    print(f"Deleting emails older than 2 years...")
    query_old = f"before:{two_years_ago} -in:trash -in:spam"
    deleted_old = delete_emails(service, query_old)
    print(f"Deleted {deleted_old} emails older than {two_years_ago}.")

    print(f"\nDeleting automated emails from 2 years to 6 months ago...")
    query_automated = f"after:{two_years_ago} before:{six_months_ago} unsubscribe -in:trash -in:spam"
    deleted_automated = delete_emails(service, query_automated)
    print(f"Deleted {deleted_automated} automated emails between {two_years_ago} and {six_months_ago}.")

    print(f"\nDeleting promotional emails older than 2 months...")
    deleted_promotions = delete_promotional_emails(service, two_months_ago)
    print(f"Deleted {deleted_promotions} promotional emails older than {two_months_ago}.")

    print(f"\nEmptying Trash folder...")
    deleted_trash = empty_folder(service, 'TRASH')
    print(f"Permanently deleted {deleted_trash} messages from trash.")

    print(f"\nEmptying Spam folder...")
    deleted_spam = empty_folder(service, 'SPAM')
    print(f"Permanently deleted {deleted_spam} messages from spam.")

    print("Press Enter to exit...")
    input()

if __name__ == '__main__':
    main()
