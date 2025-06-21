#!/usr/bin/env python3
"""
PR Pirate - Discovery Phase Testing

This script tests the GitHub repository and issue discovery functionality.
"""

import os
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from pr_pirate.discovery import GitHubClient, RepositoryDiscoverer, IssueDiscoverer
from pr_pirate.utils import DatabaseManager

console = Console()


def main():
    """Main discovery testing function."""
    console.print(
        Panel.fit(
            Text("🏴‍☠️ PR Pirate - Discovery Phase", style="bold blue"), style="bold"
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

        # Test authentication
        console.print("\n[blue]🔐 Testing GitHub authentication...[/blue]")
        user = github_client.get_authenticated_user()

        # Discover repositories
        console.print("\n[blue]🔍 Starting repository discovery...[/blue]")
        repositories = repo_discoverer.discover_repositories(
            categories=["llm", "genai"],  # Start with these categories
            min_stars=10,
            max_stars=5000,
            max_repos_per_query=20,  # Limit for testing
        )

        if not repositories:
            console.print(
                "[yellow]No repositories found. Try adjusting search criteria.[/yellow]"
            )
            return 0

        # Get top repositories for issue discovery
        top_repos = repo_discoverer.get_top_repositories(limit=5)
        console.print(
            f"\n[green]✓[/green] Selected top {len(top_repos)} repositories for issue discovery"
        )

        # Discover issues
        console.print("\n[blue]🎯 Starting issue discovery...[/blue]")
        issues = issue_discoverer.discover_issues(
            repositories=top_repos,
            max_issues_per_repo=5,  # Limit for testing
            include_unlabeled=False,
        )

        if not issues:
            console.print("[yellow]No suitable issues found.[/yellow]")
            return 0

        # Show results summary
        console.print("\n[bold green]🎉 Discovery Complete![/bold green]")
        console.print(f"  • Found {len(repositories)} repositories")
        console.print(f"  • Found {len(issues)} suitable issues")

        # Show top issues
        top_issues = issue_discoverer.get_top_issues(limit=5)
        console.print("\n[bold blue]🏆 Top Issues:[/bold blue]")
        for i, issue in enumerate(top_issues, 1):
            console.print(
                f"  {i}. [{issue.repo_full_name}] #{issue.number}: {issue.title[:60]}..."
            )
            console.print(
                f"     Priority: {issue.priority_score:.2f}, Labels: {', '.join(issue.labels[:3])}"
            )
            console.print(f"     URL: {issue.html_url}")
            console.print()

        return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Interrupted by user[/yellow]")
        return 130
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        console.print_exception()
        return 1
    finally:
        try:
            db_manager.close()
        except:
            pass


if __name__ == "__main__":
    sys.exit(main())
