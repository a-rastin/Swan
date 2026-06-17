"""Google Drive via owner OAuth refresh token (personal account, no service account).

Phase 3. Uses google-auth Credentials built from the stored refresh token; google-auth
auto-refreshes the access token. Files go to GOOGLE_DRIVE_ROOT_FOLDER_ID / <user> subfolder.
"""
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload

from app.core.config import settings

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
TOKEN_URI = "https://oauth2.googleapis.com/token"


def _credentials() -> Credentials:
    creds = Credentials(
        token=None,
        refresh_token=settings.GOOGLE_DRIVE_REFRESH_TOKEN,
        token_uri=TOKEN_URI,
        client_id=settings.GOOGLE_OAUTH_CLIENT_ID,
        client_secret=settings.GOOGLE_OAUTH_CLIENT_SECRET,
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return creds


def _service():
    return build("drive", "v3", credentials=_credentials(), cache_discovery=False)


def ensure_user_folder(user_id: str) -> str:
    """Find/create Swan/<user_id> folder, return its id. TODO phase 3: cache id in DB."""
    svc = _service()
    q = (
        f"name='{user_id}' and mimeType='application/vnd.google-apps.folder' "
        f"and '{settings.GOOGLE_DRIVE_ROOT_FOLDER_ID}' in parents and trashed=false"
    )
    found = svc.files().list(q=q, fields="files(id)").execute().get("files", [])
    if found:
        return found[0]["id"]
    meta = {
        "name": user_id,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [settings.GOOGLE_DRIVE_ROOT_FOLDER_ID],
    }
    return svc.files().create(body=meta, fields="id").execute()["id"]


def upload_file(user_id: str, filename: str, data: bytes, mime: str) -> dict:
    svc = _service()
    folder_id = ensure_user_folder(user_id)
    media = MediaInMemoryUpload(data, mimetype=mime, resumable=False)
    meta = {"name": filename, "parents": [folder_id]}
    return (
        svc.files()
        .create(body=meta, media_body=media, fields="id,name,mimeType,size,webViewLink")
        .execute()
    )


def delete_file(drive_file_id: str) -> None:
    _service().files().delete(fileId=drive_file_id).execute()
