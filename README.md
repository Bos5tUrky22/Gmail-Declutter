# Gmail Cleanup Script

This Python script deletes old and automated emails from your Gmail account in batches of 100.

## What It Does
- Deletes all emails older than 2 years (before March 15, 2023, by default).
- Deletes automated emails (with "unsubscribe") from 2 years to 6 months ago (March 15, 2023, to September 15, 2024).
- Empties Trash and Spam folders.

## Prerequisites
- Python 3.8+ installed ([Download](https://www.python.org/downloads/)).
- Google Cloud credentials (`credentials.json`).

## Setup
1. **Install Dependencies**:
   ```bash
   pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client