"""Google Drive integration for uploading audio files."""

import os
from pathlib import Path
from typing import Optional

from rich.console import Console

console = Console()


class GoogleDriveUploader:
    """Upload files to Google Drive using service account."""

    def __init__(self):
        """Initialize Google Drive uploader."""
        self.credentials_path = os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH")
        self.folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        self.service = None
        self.enabled = False

        if self.credentials_path and self.folder_id:
            try:
                self._initialize_service()
                self.enabled = True
                console.print("[green]✓[/green] Google Drive client initialized")
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Could not initialize Google Drive: {e}[/yellow]"
                )

    def _initialize_service(self):
        """Initialize Google Drive service."""
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        # Load service account credentials
        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_path, scopes=["https://www.googleapis.com/auth/drive.file"]
        )

        # Build the service
        self.service = build("drive", "v3", credentials=credentials)

    def upload_file(self, file_path: str, description: str = "") -> Optional[str]:
        """Upload a file to Google Drive and return shareable link."""
        if not self.enabled:
            return None

        try:
            from googleapiclient.http import MediaFileUpload

            file_name = Path(file_path).name
            file_size = Path(file_path).stat().st_size

            console.print(
                f"[blue]☁️ Uploading {file_name} to Google Drive ({file_size / (1024 * 1024):.1f} MB)...[/blue]"
            )

            # File metadata
            file_metadata = {
                "name": file_name,
                "description": description,
                "parents": [self.folder_id] if self.folder_id else [],
            }

            # Upload the file
            media = MediaFileUpload(file_path, resumable=True)
            file = (
                self.service.files()
                .create(
                    body=file_metadata, media_body=media, fields="id,name,webViewLink"
                )
                .execute()
            )

            # Make the file publicly accessible
            self.service.permissions().create(
                fileId=file["id"], body={"role": "reader", "type": "anyone"}
            ).execute()

            # Get the shareable link
            file_info = (
                self.service.files()
                .get(fileId=file["id"], fields="webViewLink,webContentLink")
                .execute()
            )

            console.print(
                f"[green]✓[/green] Uploaded to Google Drive: {file_info['webViewLink']}"
            )
            return file_info["webViewLink"]

        except Exception as e:
            console.print(f"[red]✗[/red] Failed to upload to Google Drive: {e}")
            return None

    def is_enabled(self) -> bool:
        """Check if Google Drive upload is enabled."""
        return self.enabled

    def get_download_link(self, file_id: str) -> Optional[str]:
        """Get direct download link for a file."""
        if not self.enabled:
            return None

        try:
            # For direct download, we use the webContentLink
            file_info = (
                self.service.files()
                .get(fileId=file_id, fields="webContentLink")
                .execute()
            )
            return file_info.get("webContentLink")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not get download link: {e}[/yellow]")
            return None
