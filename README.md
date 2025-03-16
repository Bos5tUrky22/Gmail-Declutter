# Gmail Cleanup Script

This Python script deletes old and automated emails from your Gmail account in batches of 100.

## What It Does
- Deletes all emails older than 2 years (before March 15, 2023, by default).
- Deletes automated emails (with "unsubscribe") from 2 years to 6 months ago (March 15, 2023, to September 15, 2024).
- Empties Trash and Spam folders.

## Prerequisites
- Python 3.8+ installed ([Download](https://www.python.org/downloads/)).
- Google Cloud credentials (`credentials.json`):
  - Go to [Google Cloud Console](https://console.cloud.google.com/) and sign in with your Google account.
  - Click the project dropdown at the top (it might say "Select a project") > Click "New Project" (top right).
  - Name your project (e.g., "GmailCleanup"), leave the organization as is, and click "Create".
  - Once the project is created, select it from the project dropdown.
  - Enable the Gmail API:
    - In the left sidebar, go to "APIs & Services" > "Library".
    - Search for "Gmail API", click on it, and click "Enable".
  - Set up the OAuth consent screen:
    - In the left sidebar, go to "APIs & Services" > "OAuth consent screen".
    - Choose "External" as the user type (or "Internal" if you’re in a Google Workspace organization) and click "Create".
    - Fill in the required fields:
      - **App name**: "GmailCleanup" (or any name you prefer).
      - **User support email**: Your email address.
      - **Developer contact information**: Your email address.
    - Leave other fields as default and click "Save and Continue" through the next steps (Scopes, Test users, Summary).
    - On the "Test users" step, you can add your Gmail address as a test user (but the developer will also need to add you—see the note below).
  - Create an OAuth 2.0 Client ID:
    - In the left sidebar, go to "APIs & Services" > "Credentials".
    - Click "Create Credentials" (top) > Select "OAuth 2.0 Client IDs".
    - Set "Application type" to "Desktop app".
    - Name it (e.g., "GmailCleanup Desktop Client") and click "Create".
    - Download the credentials:
      - You’ll see your new Client ID in the list. Click the download button (a downward arrow) on the right.
      - The file will download as `credentials.json`. Move it to the same folder as `delete_emails.py`.
  - **Note**: This script uses a Google Cloud project in "Testing" mode. You must be added as a test user to authenticate. Contact the developer (Bos5tUrky22) with your Gmail address to be added.

## Setup
1. **Install Dependencies**:
   ```bash
   pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
