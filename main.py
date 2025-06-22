#!/usr/bin/env python3
"""
RepoRadio - GitHub Issue Discovery with TTS Audio Summaries

Discover GitHub issues and generate audio summaries for listening on-the-go.
"""

import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent / "src"))

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from pr_pirate.discovery import GitHubClient, RepositoryDiscoverer, IssueDiscoverer
from pr_pirate.llm import IssueAssessor
from pr_pirate.tts import ReplicateTTS
from pr_pirate.templates import AudioScriptTemplate
from pr_pirate.notifications import DiscordNotifier, GoogleDriveUploader
from pr_pirate.utils import DatabaseManager

# Add config to path for dynamic imports
sys.path.insert(0, str(Path(__file__).parent / "config"))

console = Console()


@click.command()
@click.option(
    "--repos",
    "-r",
    help="Comma-separated list of repositories to check (e.g., 'owner/repo1,owner/repo2') OR predefined list name (llm,genai,llmops,ml,nlp)",
    type=str,
)
@click.option(
    "--categories",
    "-c",
    help="Categories to discover (llm,genai,llmops,ml,nlp)",
    default="llm,genai",
    type=str,
)
@click.option(
    "--min-stars",
    help="Minimum stars for discovered repositories",
    default=10,
    type=int,
)
@click.option(
    "--max-stars",
    help="Maximum stars for discovered repositories",
    default=5000,
    type=int,
)
@click.option(
    "--max-repos",
    help="Maximum repositories to process",
    default=20,
    type=int,
)
@click.option(
    "--max-issues-per-repo",
    help="Maximum issues to fetch per repository",
    default=5,
    type=int,
)
@click.option(
    "--output-audio",
    help="Path to save the audio file",
    default="issues_summary.wav",
    type=str,
)
@click.option(
    "--voice",
    help="TTS voice to use",
    default="af_bella",
    type=str,
)
@click.option(
    "--speed",
    help="TTS speech speed",
    default=1.15,
    type=float,
)
@click.option(
    "--skip-tts",
    help="Generate script only, don't create audio",
    is_flag=True,
    default=False,
)
@click.option(
    "--max-workers",
    help="Maximum parallel workers for LLM assessment",
    default=3,
    type=int,
)
@click.option(
    "--no-discord",
    help="Disable Discord notifications",
    is_flag=True,
    default=False,
)
def main(
    repos: Optional[str],
    categories: str,
    min_stars: int,
    max_stars: int,
    max_repos: int,
    max_issues_per_repo: int,
    output_audio: str,
    voice: str,
    speed: float,
    skip_tts: bool,
    max_workers: int,
    no_discord: bool,
):
    """📻 RepoRadio - GitHub issue discovery with TTS audio summaries."""
    console.print(
        Panel.fit(
            Text("📻 RepoRadio - Audio Summary Generator", style="bold blue"),
            style="bold",
        )
    )

    # Check for GitHub token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        console.print(
            Panel(
                "[red]Error: GITHUB_TOKEN environment variable not set.\n"
                "Please set your GitHub personal access token:\n"
                "[bold cyan]export GITHUB_TOKEN=your_token_here[/bold cyan]",
                title="⚠️ Missing GitHub Token",
                style="red",
            )
        )
        return 1

    try:
        # Initialize components
        console.print("\n[blue]🔧 Initializing components...[/blue]")

        github_client = GitHubClient(github_token)
        repo_discoverer = RepositoryDiscoverer(github_client)
        issue_discoverer = IssueDiscoverer(github_client)
        db_manager = DatabaseManager()
        discord_notifier = DiscordNotifier()
        google_drive = GoogleDriveUploader()
        if no_discord:
            discord_notifier.enabled = False

        # Test authentication
        console.print("\n[blue]🔐 Testing GitHub authentication...[/blue]")
        github_client.get_authenticated_user()

        # Choose discovery method
        if repos:
            # Check if it's a predefined list name
            try:
                from repo_lists import get_repo_list, list_available_repo_lists  # type: ignore

                if repos.lower() in list_available_repo_lists():
                    # Use predefined list
                    repo_list = get_repo_list(repos.lower())
                    console.print(
                        f"\n[blue]📋 Using predefined '{repos}' repository list ({len(repo_list)} repositories)...[/blue]"
                    )
                else:
                    # Parse as comma-separated list
                    repo_list = [repo.strip() for repo in repos.split(",")]
                    console.print(
                        f"\n[blue]📋 Processing {len(repo_list)} specified repositories...[/blue]"
                    )
            except ImportError:
                # Fallback if config not available
                repo_list = [repo.strip() for repo in repos.split(",")]
                console.print(
                    f"\n[blue]📋 Processing {len(repo_list)} specified repositories...[/blue]"
                )

            for repo in repo_list[:10]:  # Show first 10
                console.print(f"  • {repo}")
            if len(repo_list) > 10:
                console.print(f"  ... and {len(repo_list) - 10} more")

            repositories = repo_discoverer.get_repositories_by_names(repo_list)
        else:
            # Discovery mode
            category_list = [cat.strip() for cat in categories.split(",")]
            console.print(
                f"\n[blue]🔍 Starting repository discovery for categories: {', '.join(category_list)}...[/blue]"
            )

            repositories = repo_discoverer.discover_repositories(
                categories=category_list,
                min_stars=min_stars,
                max_stars=max_stars,
                max_repos_per_query=max_repos,
                max_workers=max_workers,
            )

        if not repositories:
            console.print(
                "[yellow]No repositories found. Try adjusting search criteria or repository list.[/yellow]"
            )
            return 0

        # Get top repositories for issue discovery
        top_repos = repo_discoverer.get_top_repositories(
            limit=min(len(repositories), 10)
        )
        console.print(
            f"\n[green]✓[/green] Selected top {len(top_repos)} repositories for issue discovery"
        )

        # Send Discord start notification
        if discord_notifier.is_enabled():
            category_list = [cat.strip() for cat in categories.split(",")]
            discord_notifier.send_start_notification(category_list, len(repositories))

        # Discover issues
        console.print("\n[blue]🎯 Starting issue discovery...[/blue]")
        issues = issue_discoverer.discover_issues(
            repositories=top_repos,
            max_issues_per_repo=max_issues_per_repo,
            include_unlabeled=False,
            max_workers=max_workers,
        )

        if not issues:
            console.print("[yellow]No suitable issues found.[/yellow]")
            return 0

        # Show results summary
        console.print("\n[bold green]🎉 Discovery Complete![/bold green]")
        console.print(f"  • Found {len(repositories)} repositories")
        console.print(f"  • Found {len(issues)} suitable issues")

        # Get top 10 issues for assessment
        top_issues = issue_discoverer.get_top_issues(limit=10)
        console.print(
            f"\n[blue]🧠 Starting LLM assessment of top {len(top_issues)} issues...[/blue]"
        )

        # Initialize LLM assessor
        try:
            issue_assessor = IssueAssessor()
        except ValueError as e:
            console.print(f"[red]❌ {e}[/red]")
            console.print(
                "[yellow]Skipping LLM assessment and TTS generation.[/yellow]"
            )
            return 1

        # Assess issues with LLM
        assessments = issue_assessor.assess_issues(top_issues, max_workers=max_workers)

        if not assessments:
            console.print("[yellow]No issues were successfully assessed.[/yellow]")
            return 0

        # Send Discord assessment results notification
        if discord_notifier.is_enabled():
            discord_notifier.send_assessment_results(top_issues, assessments)

        # Generate audio script
        console.print("\n[blue]📝 Generating audio script...[/blue]")
        script = issue_assessor.generate_audio_script(top_issues, assessments)

        # Show script preview
        template = AudioScriptTemplate()
        issues_data = []
        assessment_map = {a.issue_id: a for a in assessments}

        for issue in top_issues:
            if issue.id in assessment_map:
                assessment = assessment_map[issue.id]
                composite_score = assessment.composite_score

                difficulty = (
                    "Easy"
                    if composite_score >= 7.0
                    else "Medium"
                    if composite_score >= 5.0
                    else "Hard"
                )
                issue_type = (
                    "Bug"
                    if any(label.lower() in ["bug", "bugfix"] for label in issue.labels)
                    else "Feature"
                )

                issues_data.append(
                    {
                        "repo_name": issue.repo_full_name.split("/")[1],
                        "issue_type": issue_type,
                        "title": issue.title,
                        "difficulty": difficulty,
                        "composite_score": composite_score,
                    }
                )

        preview = template.generate_preview_text(issues_data)
        console.print(f"\n{preview}")

        if skip_tts:
            console.print("\n[blue]📄 Script generated (TTS skipped)[/blue]")
            console.print(f"Script length: {len(script)} characters")
            return 0

        # Generate audio with TTS
        console.print("\n[blue]🎤 Generating audio summary...[/blue]")
        try:
            tts = ReplicateTTS()
            audio_path = tts.generate_audio(
                text=script, output_path=output_audio, voice=voice, speed=speed
            )

            console.print("\n[bold green]🎉 Audio Summary Complete![/bold green]")
            console.print(f"  • Assessed {len(assessments)} issues")
            console.print(f"  • Generated script ({len(script)} characters)")
            console.print(f"  • Audio saved to: {audio_path}")
            console.print(f"  • Voice: {voice}, Speed: {speed}x")

            # Upload to Google Drive if enabled
            drive_link = None
            if google_drive.is_enabled():
                drive_link = google_drive.upload_file(
                    audio_path,
                    f"RepoRadio audio summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                )
                if drive_link:
                    console.print(f"  • Google Drive: {drive_link}")

            # Send Discord completion notification
            if discord_notifier.is_enabled():
                discord_notifier.send_audio_complete(
                    audio_path, len(script), voice, speed, drive_link
                )
                # Also try to send the audio file itself (if not too large and no Google Drive)
                if not drive_link:
                    try:
                        from pathlib import Path

                        file_size = Path(audio_path).stat().st_size
                        if file_size < 8 * 1024 * 1024:  # Discord 8MB limit
                            discord_notifier.send_file(
                                audio_path, "🎧 **Your audio summary is ready!**"
                            )
                    except:
                        pass

        except Exception as e:
            console.print(f"[red]❌ TTS Error: {e}[/red]")
            console.print(
                f"[blue]📄 Script was generated successfully ({len(script)} characters)[/blue]"
            )
            # Send Discord error notification
            if discord_notifier.is_enabled():
                discord_notifier.send_error_notification(str(e), "TTS Audio Generation")
            return 1

        return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Interrupted by user[/yellow]")
        return 130
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        console.print_exception()
        # Send Discord error notification
        if "discord_notifier" in locals() and discord_notifier.is_enabled():
            discord_notifier.send_error_notification(str(e), "General Execution")
        return 1
    finally:
        try:
            db_manager.close()
        except:
            pass


if __name__ == "__main__":
    sys.exit(main())
