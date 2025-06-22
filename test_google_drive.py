#!/usr/bin/env python3
"""
Test script for Google Drive connectivity.
Uploads the existing issues_summary.wav file to verify the integration works.
"""

import os
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from pr_pirate.notifications import GoogleDriveUploader

console = Console()


def main():
    """Test Google Drive upload functionality."""
    console.print("[bold blue]🧪 Testing Google Drive Connectivity[/bold blue]\n")

    # Check if audio file exists
    audio_file = "issues_summary.wav"
    if not Path(audio_file).exists():
        console.print(f"[red]❌ Audio file '{audio_file}' not found[/red]")
        console.print(
            "[yellow]Please run the main script first to generate an audio file[/yellow]"
        )
        return 1

    # Check environment variables
    credentials_path = os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH")
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

    console.print("[blue]🔧 Checking configuration...[/blue]")
    console.print(f"  • Credentials path: {credentials_path or '[NOT SET]'}")
    console.print(f"  • Folder ID: {folder_id or '[NOT SET]'}")

    if not credentials_path or not folder_id:
        console.print("\n[red]❌ Google Drive not configured[/red]")
        console.print(
            "[yellow]Please set GOOGLE_DRIVE_CREDENTIALS_PATH and GOOGLE_DRIVE_FOLDER_ID in your .env file[/yellow]"
        )
        return 1

    # Check if credentials file exists
    if not Path(credentials_path).exists():
        console.print(f"\n[red]❌ Credentials file not found: {credentials_path}[/red]")
        return 1

    console.print(
        f"  • Audio file: {audio_file} ({Path(audio_file).stat().st_size / (1024 * 1024):.1f} MB)"
    )

    # Initialize Google Drive uploader
    console.print("\n[blue]🚀 Initializing Google Drive uploader...[/blue]")
    try:
        drive_uploader = GoogleDriveUploader()

        if not drive_uploader.is_enabled():
            console.print("[red]❌ Google Drive uploader failed to initialize[/red]")
            return 1

        # Upload the file
        console.print("\n[blue]📤 Uploading test file...[/blue]")
        drive_link = drive_uploader.upload_file(
            audio_file, "Test upload from PR Pirate Google Drive connectivity test"
        )

        if drive_link:
            console.print("\n[bold green]✅ Success![/bold green]")
            console.print(f"[green]File uploaded successfully: {drive_link}[/green]")
            console.print(
                "\n[blue]🎉 Google Drive integration is working correctly![/blue]"
            )
            return 0
        else:
            console.print("\n[red]❌ Upload failed[/red]")
            return 1

    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        console.print("\n[yellow]💡 Troubleshooting tips:[/yellow]")
        console.print(
            "  • Make sure you're using a service account JSON (not OAuth2 credentials)"
        )
        console.print(
            "  • Service account JSON should contain: type, project_id, client_email, token_uri"
        )
        console.print(
            "  • Download from Google Cloud Console > IAM & Admin > Service Accounts"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
