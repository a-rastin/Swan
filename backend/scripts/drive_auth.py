"""One-time: mint a Google Drive refresh token for the owner's personal account.

Prereq: Google Cloud OAuth client (type "Web application"), owner added as test user,
scope drive.file. Run locally with the redirect set to a localhost URL during setup, OR
use the console flow below.

Usage:
    pip install google-auth-oauthlib
    GOOGLE_OAUTH_CLIENT_ID=... GOOGLE_OAUTH_CLIENT_SECRET=... python scripts/drive_auth.py

Copy the printed refresh_token into .env as GOOGLE_DRIVE_REFRESH_TOKEN.
"""
import os

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def main() -> None:
    client_config = {
        "installed": {
            "client_id": os.environ["GOOGLE_OAUTH_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_OAUTH_CLIENT_SECRET"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8765/"],
        }
    }
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=8765, access_type="offline", prompt="consent")
    print("\nGOOGLE_DRIVE_REFRESH_TOKEN=" + creds.refresh_token)


if __name__ == "__main__":
    main()
