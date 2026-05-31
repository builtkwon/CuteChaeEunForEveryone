import io
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from app.backends.base import CloudStorage


class GoogleDriveStorage(CloudStorage):
    """Google Drive 기반 CloudStorage 구현체."""

    def __init__(self, creds: Credentials, folder_name: str) -> None:
        self._service = build("drive", "v3", credentials=creds)
        self._folder_name = folder_name

    def upload(self, file_bytes: bytes, filename: str) -> str:
        folder_id = self._get_or_create_folder(self._folder_name)

        uploaded = self._service.files().create(
            body={"name": filename, "parents": [folder_id]},
            media_body=MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype="image/jpeg"),
            fields="id",
        ).execute()

        file_id = uploaded["id"]
        self._service.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"},
        ).execute()

        return f"https://drive.google.com/uc?export=download&id={file_id}"

    def _get_or_create_folder(self, name: str) -> str:
        query = (
            f"name='{name}' "
            f"and mimeType='application/vnd.google-apps.folder' "
            f"and trashed=false"
        )
        files = self._service.files().list(q=query, fields="files(id)").execute().get("files", [])
        if files:
            return files[0]["id"]

        folder = self._service.files().create(
            body={"name": name, "mimeType": "application/vnd.google-apps.folder"},
            fields="id",
        ).execute()
        return folder["id"]
