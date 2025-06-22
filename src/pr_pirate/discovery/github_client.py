import os
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from github import Github, RateLimitExceededException
from rich.console import Console
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

console = Console()


class GitHubClient:
    """GitHub API client with rate limiting and error handling."""

    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub client with authentication."""
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError(
                "GitHub token required. Set GITHUB_TOKEN environment variable."
            )

        self.github = Github(self.token)
        self.rate_limit_buffer = 100  # Keep buffer to avoid hitting limits

        console.print("[green]✓[/green] GitHub client initialized")
        self._print_rate_limits()

    def _print_rate_limits(self):
        """Print current rate limit status."""
        try:
            core_rate = self.github.get_rate_limit().core
            search_rate = self.github.get_rate_limit().search

            console.print("[blue]Rate Limits:[/blue]")
            console.print(
                f"  Core: {core_rate.remaining}/{core_rate.limit} (resets at {core_rate.reset})"
            )
            console.print(
                f"  Search: {search_rate.remaining}/{search_rate.limit} (resets at {search_rate.reset})"
            )
        except Exception as e:
            console.print(f"[yellow]Warning: Could not fetch rate limits: {e}[/yellow]")

    @retry(
        retry=retry_if_exception_type(RateLimitExceededException),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    def search_repositories(
        self, query: str, sort: str = "stars", order: str = "desc", per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """Search repositories with rate limit handling."""
        self._check_rate_limits()

        try:
            search_result = self.github.search_repositories(
                query=query, sort=sort, order=order
            )

            repositories = []
            count = 0

            for repo in search_result:
                if count >= per_page:
                    break

                repo_data = {
                    "id": repo.id,
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "html_url": repo.html_url,
                    "stargazers_count": repo.stargazers_count,
                    "forks_count": repo.forks_count,
                    "language": repo.language,
                    "topics": getattr(
                        repo, "topics", []
                    ),  # Use cached topics if available
                    "license": getattr(getattr(repo, "license", None), "name", None),
                    "created_at": repo.created_at,
                    "updated_at": repo.updated_at,
                    "pushed_at": repo.pushed_at,
                    "open_issues_count": repo.open_issues_count,
                    "has_issues": repo.has_issues,
                    "archived": repo.archived,
                    "disabled": getattr(repo, "disabled", False),
                }

                repositories.append(repo_data)
                count += 1

            console.print(f"[green]✓[/green] Found {len(repositories)} repositories")
            return repositories

        except RateLimitExceededException:
            console.print("[yellow]Rate limit exceeded, retrying...[/yellow]")
            raise
        except Exception as e:
            console.print(f"[red]Error searching repositories: {e}[/red]")
            raise

    @retry(
        retry=retry_if_exception_type(RateLimitExceededException),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    def get_repository_issues(
        self,
        repo_full_name: str,
        state: str = "open",
        labels: Optional[List[str]] = None,
        per_page: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get issues from a specific repository."""
        self._check_rate_limits()

        try:
            repo = self.github.get_repo(repo_full_name)

            # Get issues - we'll filter by labels after fetching
            issues = repo.get_issues(state=state)

            issue_list = []
            count = 0

            for issue in issues:
                if count >= per_page:
                    break

                # Skip pull requests (they appear as issues in GitHub API)
                if issue.pull_request:
                    continue

                issue_data = {
                    "id": issue.id,
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "html_url": issue.html_url,
                    "state": issue.state,
                    "labels": [label.name for label in issue.labels],
                    "assignee": issue.assignee.login if issue.assignee else None,
                    "assignees": [assignee.login for assignee in issue.assignees],
                    "comments": issue.comments,
                    "created_at": issue.created_at,
                    "updated_at": issue.updated_at,
                    "author_association": getattr(issue, "author_association", "NONE"),
                    "repo_id": repo.id,
                    "repo_full_name": repo_full_name,
                }

                issue_list.append(issue_data)
                count += 1

            console.print(
                f"[green]✓[/green] Found {len(issue_list)} issues in {repo_full_name}"
            )
            return issue_list

        except RateLimitExceededException:
            console.print("[yellow]Rate limit exceeded, retrying...[/yellow]")
            raise
        except Exception as e:
            console.print(f"[red]Error getting issues from {repo_full_name}: {e}[/red]")
            return []

    def _check_rate_limits(self):
        """Check if we're approaching rate limits."""
        try:
            rate_limit = self.github.get_rate_limit()

            # Check core API rate limit
            if rate_limit.core.remaining < self.rate_limit_buffer:
                wait_time = (rate_limit.core.reset - datetime.now()).total_seconds()
                if wait_time > 0:
                    console.print(
                        f"[yellow]Rate limit low, waiting {wait_time:.0f}s...[/yellow]"
                    )
                    time.sleep(wait_time + 1)

            # Check search API rate limit
            if rate_limit.search.remaining < 5:
                wait_time = (rate_limit.search.reset - datetime.now()).total_seconds()
                if wait_time > 0:
                    console.print(
                        f"[yellow]Search rate limit low, waiting {wait_time:.0f}s...[/yellow]"
                    )
                    time.sleep(wait_time + 1)

        except Exception as e:
            console.print(f"[yellow]Warning: Could not check rate limits: {e}[/yellow]")

    def get_authenticated_user(self):
        """Get authenticated user info for testing."""
        try:
            user = self.github.get_user()
            console.print(f"[green]✓[/green] Authenticated as: {user.login}")
            return user
        except Exception as e:
            console.print(f"[red]Authentication failed: {e}[/red]")
            raise
