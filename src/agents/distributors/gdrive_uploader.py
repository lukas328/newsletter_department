import os
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)


class GDriveUploader:
    """Lädt Dateien in Google Drive hoch using a service account."""

    def __init__(self, credentials_path: str):
        scopes = ['https://www.googleapis.com/auth/drive.file']
        try:
            credentials = service_account.Credentials.from_service_account_file(credentials_path, scopes=scopes)
            self.service = build('drive', 'v3', credentials=credentials)
        except Exception as e:
            logger.error(f"Fehler beim Initialisieren des Google Drive Clients: {e}")
            raise

    def upload_file(self, file_path: str, folder_id: str | None = None) -> str:
        file_metadata = {'name': os.path.basename(file_path)}
        if folder_id:
            file_metadata['parents'] = [folder_id]
        media = MediaFileUpload(file_path, mimetype='application/epub+zip')
        uploaded = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return uploaded.get('id')
