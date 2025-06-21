#!/usr/bin/env python3
"""
PR Pirate - Discovery Phase Testing

This script tests the GitHub repository and issue discovery functionality.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent / "src"))

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from pr_pirate.discovery import GitHubClient, RepositoryDiscoverer, IssueDiscoverer
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
    type=int
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
    type=int
)
def main(
    repos: Optional[str],
    categories: str,
    min_stars: int,
    max_stars: int,
    max_repos: int,
    max_issues_per_repo: int,
):
    """🏴‍☠️ PR Pirate - Automated GitHub issue discovery and fixing using AI."""
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

        # Choose discovery method
        if repos:
            # Check if it's a predefined list name
            try:
                from repo_lists import get_repo_list, list_available_repo_lists
                
                if repos.lower() in list_available_repo_lists():
                    # Use predefined list
                    repo_list = get_repo_list(repos.lower())
                    console.print(f"\n[blue]📋 Using predefined '{repos}' repository list ({len(repo_list)} repositories)...[/blue]")
                else:
                    # Parse as comma-separated list
                    repo_list = [repo.strip() for repo in repos.split(",")]
                    console.print(f"\n[blue]📋 Processing {len(repo_list)} specified repositories...[/blue]")
            except ImportError:
                # Fallback if config not available
                repo_list = [repo.strip() for repo in repos.split(",")]
                console.print(f"\n[blue]📋 Processing {len(repo_list)} specified repositories...[/blue]")
            
            for repo in repo_list[:10]:  # Show first 10
                console.print(f"  • {repo}")
            if len(repo_list) > 10:
                console.print(f"  ... and {len(repo_list) - 10} more")
            
            repositories = repo_discoverer.get_repositories_by_names(repo_list)
        else:
            # Discovery mode
            category_list = [cat.strip() for cat in categories.split(",")]
            console.print(f"\n[blue]🔍 Starting repository discovery for categories: {', '.join(category_list)}...[/blue]")
            
            repositories = repo_discoverer.discover_repositories(
                categories=category_list,
                min_stars=min_stars,
                max_stars=max_stars,
                max_repos_per_query=max_repos,
            )

        if not repositories:
            console.print(
                "[yellow]No repositories found. Try adjusting search criteria or repository list.[/yellow]"
            )
            return 0

        # Get top repositories for issue discovery
        top_repos = repo_discoverer.get_top_repositories(limit=min(len(repositories), 10))
        console.print(
            f"\n[green]✓[/green] Selected top {len(top_repos)} repositories for issue discovery"
        )

        # Discover issues
        console.print("\n[blue]🎯 Starting issue discovery...[/blue]")
        issues = issue_discoverer.discover_issues(
            repositories=top_repos,
            max_issues_per_repo=max_issues_per_repo,
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
