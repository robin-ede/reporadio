from typing import List, Dict
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

from ..models import Repository, Issue
from .github_client import GitHubClient

console = Console()


class IssueDiscoverer:
    """Discovers suitable issues from GitHub repositories."""

    # Labels that indicate good issues for automation
    GOOD_LABELS = {
        "good first issue",
        "good-first-issue",
        "beginner",
        "easy",
        "bug",
        "enhancement",
        "feature",
        "help wanted",
        "hacktoberfest",
    }

    # Labels that indicate issues we should avoid
    BAD_LABELS = {
        "wontfix",
        "invalid",
        "duplicate",
        "question",
        "discussion",
        "needs-design",
        "breaking-change",
        "major",
        "epic",
        "tracking",
    }

    def __init__(self, github_client: GitHubClient):
        self.github = github_client
        self.discovered_issues: List[Issue] = []

    def discover_issues(
        self,
        repositories: List[Repository],
        max_issues_per_repo: int = 10,
        include_unlabeled: bool = False,
    ) -> List[Issue]:
        """Discover issues from the given repositories."""
        all_issues = []

        with Progress() as progress:
            task = progress.add_task(
                "[green]Discovering issues...", total=len(repositories)
            )

            for repo in repositories:
                console.print(f"\n[blue]🔍 Scanning {repo.full_name}...[/blue]")

                try:
                    issues = self._get_repository_issues(
                        repo, max_issues_per_repo, include_unlabeled
                    )
                    all_issues.extend(issues)

                    console.print(
                        f"  [green]✓[/green] Found {len(issues)} suitable issues"
                    )

                except Exception as e:
                    console.print(f"  [red]✗[/red] Error: {e}")

                progress.update(task, advance=1)

        # Filter and prioritize issues
        filtered_issues = self._filter_and_prioritize_issues(all_issues)

        self.discovered_issues = filtered_issues
        self._print_discovery_summary()

        return filtered_issues

    def _get_repository_issues(
        self, repository: Repository, max_issues: int, include_unlabeled: bool
    ) -> List[Issue]:
        """Get issues from a specific repository."""
        issues = []

        try:
            # First, try to get issues with good labels
            for label_batch in self._get_label_batches():
                if len(issues) >= max_issues:
                    break

                try:
                    issue_data_list = self.github.get_repository_issues(
                        repo_full_name=repository.full_name,
                        state="open",
                        labels=label_batch,
                        per_page=max_issues - len(issues),
                    )

                    for issue_data in issue_data_list:
                        issue_data["discovered_at"] = datetime.now()
                        issue = Issue(**issue_data)
                        issues.append(issue)

                except Exception as e:
                    console.print(
                        f"    [yellow]Warning: Could not fetch issues with labels {label_batch}: {e}[/yellow]"
                    )
                    continue

            # If we still need more issues and include_unlabeled is True
            if len(issues) < max_issues and include_unlabeled:
                try:
                    remaining = max_issues - len(issues)
                    issue_data_list = self.github.get_repository_issues(
                        repo_full_name=repository.full_name,
                        state="open",
                        per_page=remaining,
                    )

                    # Filter out issues we already have
                    existing_ids = {issue.id for issue in issues}

                    for issue_data in issue_data_list:
                        if issue_data["id"] not in existing_ids:
                            issue_data["discovered_at"] = datetime.now()
                            issue = Issue(**issue_data)
                            issues.append(issue)

                except Exception as e:
                    console.print(
                        f"    [yellow]Warning: Could not fetch unlabeled issues: {e}[/yellow]"
                    )

        except Exception as e:
            console.print(
                f"[red]Error getting issues from {repository.full_name}: {e}[/red]"
            )
            return []

        return issues

    def _get_label_batches(self) -> List[List[str]]:
        """Get batches of labels to search for."""
        # GitHub API allows searching for multiple labels, but we'll batch them
        # to get better coverage
        return [
            ["good first issue"],
            ["good-first-issue"],
            ["bug"],
            ["enhancement"],
            ["help wanted"],
            ["beginner", "easy"],
        ]

    def _filter_and_prioritize_issues(self, issues: List[Issue]) -> List[Issue]:
        """Filter issues and sort by priority."""
        # Filter out unsuitable issues
        suitable_issues = []

        for issue in issues:
            if self._is_issue_suitable(issue):
                suitable_issues.append(issue)

        # Sort by priority score
        suitable_issues.sort(key=lambda x: x.priority_score, reverse=True)

        console.print(
            f"[blue]ℹ[/blue] Filtered to {len(suitable_issues)} suitable issues from {len(issues)} total"
        )

        return suitable_issues

    def _is_issue_suitable(self, issue: Issue) -> bool:
        """Check if an issue is suitable for automated fixing."""
        # Use the issue's built-in candidate check
        if not issue.is_good_candidate:
            return False

        # Additional checks

        # Age filter (not too old, not too new)
        if issue.age_days > 365:  # Too old
            return False
        if issue.age_days < 1:  # Too new (might still be in discussion)
            return False

        # Title quality check
        if len(issue.title) < 10:  # Too short
            return False

        # Body quality check (if exists)
        if issue.body and len(issue.body) < 20:  # Too short for meaningful description
            return False

        # Check for bad indicators in title/body
        bad_keywords = {
            "design",
            "discuss",
            "rfc",
            "proposal",
            "breaking",
            "major refactor",
            "architecture",
            "backwards compatibility",
        }

        text_to_check = (issue.title + " " + (issue.body or "")).lower()
        if any(keyword in text_to_check for keyword in bad_keywords):
            return False

        return True

    def _print_discovery_summary(self):
        """Print a summary of discovered issues."""
        if not self.discovered_issues:
            console.print("[yellow]No issues discovered.[/yellow]")
            return

        # Create summary table
        table = Table(title="🎯 Issue Discovery Summary")
        table.add_column("Repository", style="bold")
        table.add_column("Issue #", justify="right", style="cyan")
        table.add_column("Title", max_width=50)
        table.add_column("Labels", style="green")
        table.add_column("Priority", justify="right", style="yellow")

        # Show top issues
        for issue in self.discovered_issues[:20]:
            labels_str = ", ".join(issue.labels[:3])  # Show first 3 labels
            if len(issue.labels) > 3:
                labels_str += "..."

            table.add_row(
                issue.repo_full_name.split("/")[1],  # Just repo name, not full
                str(issue.number),
                issue.title[:47] + "..." if len(issue.title) > 50 else issue.title,
                labels_str,
                f"{issue.priority_score:.2f}",
            )

        console.print(table)

        # Print statistics
        repo_counts = {}
        label_counts = {}

        for issue in self.discovered_issues:
            repo_counts[issue.repo_full_name] = (
                repo_counts.get(issue.repo_full_name, 0) + 1
            )
            for label in issue.labels:
                label_counts[label] = label_counts.get(label, 0) + 1

        console.print("\n[bold]📊 Statistics:[/bold]")
        console.print(f"  Total issues: {len(self.discovered_issues)}")
        console.print(f"  Repositories: {len(repo_counts)}")
        console.print(
            f"  Top labels: {dict(sorted(label_counts.items(), key=lambda x: x[1], reverse=True)[:5])}"
        )

        # Print top repositories by issue count
        top_repos = sorted(repo_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        console.print(f"  Top repos: {dict(top_repos)}")

    def get_issues_by_repository(self) -> Dict[str, List[Issue]]:
        """Group issues by repository."""
        repo_issues = {}

        for issue in self.discovered_issues:
            if issue.repo_full_name not in repo_issues:
                repo_issues[issue.repo_full_name] = []
            repo_issues[issue.repo_full_name].append(issue)

        return repo_issues

    def get_top_issues(self, limit: int = 10) -> List[Issue]:
        """Get top issues by priority score."""
        return self.discovered_issues[:limit]
