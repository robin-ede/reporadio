from typing import List, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

from ..models import Repository
from .github_client import GitHubClient

console = Console()


class RepositoryDiscoverer:
    """Discovers GitHub repositories based on topics and criteria."""

    # Target topics for LLM/GenAI repositories
    TARGET_TOPICS = {
        "llm": [
            "llm",
            "large-language-model",
            "language-model",
            "gpt",
            "bert",
            "transformer",
        ],
        "genai": ["generative-ai", "genai", "ai-generation", "artificial-intelligence"],
        "llmops": [
            "llmops",
            "mlops",
            "ai-ops",
            "model-deployment",
            "ai-infrastructure",
        ],
        "ml": [
            "machine-learning",
            "deep-learning",
            "neural-network",
            "pytorch",
            "tensorflow",
        ],
        "nlp": [
            "nlp",
            "natural-language-processing",
            "text-processing",
            "language-understanding",
        ],
    }

    # Languages we can work with
    SUPPORTED_LANGUAGES = {"Python", "JavaScript", "TypeScript", "Go", "Rust", "Java"}

    def __init__(self, github_client: GitHubClient):
        self.github = github_client
        self.discovered_repos: List[Repository] = []

    def discover_repositories(
        self,
        categories: Optional[List[str]] = None,
        min_stars: int = 10,
        max_stars: int = 10000,
        max_repos_per_query: int = 50,
        exclude_archived: bool = True,
        max_workers: int = 3,
    ) -> List[Repository]:
        """Discover repositories matching our criteria with parallel search."""
        if categories is None:
            categories = list(self.TARGET_TOPICS.keys())

        all_repositories = []

        # Get all topics from all categories for parallel processing
        all_topics = []
        for category in categories:
            topics = self.TARGET_TOPICS.get(category, [category])
            for topic in topics:
                all_topics.append((category, topic))

        console.print(
            f"\n[blue]🔍 Searching {len(all_topics)} topics across {len(categories)} categories...[/blue]"
        )

        with Progress() as progress:
            task = progress.add_task(
                "[green]Discovering repositories...", total=len(all_topics)
            )

            # Use ThreadPoolExecutor for parallel topic searches
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all topic search tasks
                future_to_topic = {
                    executor.submit(
                        self._search_single_topic,
                        topic,
                        min_stars,
                        max_stars,
                        max_repos_per_query,
                        exclude_archived,
                    ): (category, topic)
                    for category, topic in all_topics
                }

                # Process completed searches as they finish
                for future in as_completed(future_to_topic):
                    category, topic = future_to_topic[future]
                    try:
                        repos = future.result()
                        all_repositories.extend(repos)
                        console.print(
                            f"  [green]✓[/green] Found {len(repos)} repos for '{topic}' ({category})"
                        )
                    except Exception as e:
                        console.print(f"  [red]✗[/red] Error searching '{topic}': {e}")

                    progress.update(task, advance=1)

        # Remove duplicates and filter
        unique_repos = self._deduplicate_repositories(all_repositories)
        filtered_repos = self._filter_repositories(unique_repos)

        self.discovered_repos = filtered_repos
        self._print_discovery_summary()

        return filtered_repos

    def _search_single_topic(
        self,
        topic: str,
        min_stars: int,
        max_stars: int,
        max_repos: int,
        exclude_archived: bool,
    ) -> List[Repository]:
        """Search repositories for a single topic (optimized for parallel execution)."""
        repositories = []

        try:
            # Build search query
            query_parts = [
                f"topic:{topic}",
                f"stars:{min_stars}..{max_stars}",
                "is:public",
            ]

            if exclude_archived:
                query_parts.append("archived:false")

            query = " ".join(query_parts)

            # Search repositories
            repo_data_list = self.github.search_repositories(
                query=query,
                sort="stars",
                order="desc",
                per_page=min(max_repos, 100),
            )

            # Convert to Repository objects (without fetching topics to save API calls)
            for repo_data in repo_data_list:
                try:
                    repo_data["discovered_at"] = datetime.now()
                    # Use topics from search result instead of making additional API calls
                    if "topics" not in repo_data:
                        repo_data["topics"] = []
                    repo = Repository(**repo_data)
                    repositories.append(repo)
                except Exception:
                    # Skip problematic repos silently during parallel execution
                    continue

        except Exception as e:
            console.print(f"[red]✗[/red] Failed to search topic '{topic}': {e}")

        return repositories

    def _search_category_repositories(
        self,
        category: str,
        min_stars: int,
        max_stars: int,
        max_repos: int,
        exclude_archived: bool,
    ) -> List[Repository]:
        """Search repositories for a specific category."""
        topics = self.TARGET_TOPICS.get(category, [category])
        repositories = []

        for topic in topics:
            try:
                # Build search query
                query_parts = [
                    f"topic:{topic}",
                    f"stars:{min_stars}..{max_stars}",
                    "is:public",
                ]

                if exclude_archived:
                    query_parts.append("archived:false")

                query = " ".join(query_parts)

                # Search repositories
                repo_data_list = self.github.search_repositories(
                    query=query,
                    sort="stars",
                    order="desc",
                    per_page=min(max_repos, 100),
                )

                # Convert to Repository objects
                for repo_data in repo_data_list:
                    try:
                        repo_data["discovered_at"] = datetime.now()
                        repo = Repository(**repo_data)
                        repositories.append(repo)
                    except Exception as e:
                        console.print(
                            f"[yellow]Warning: Could not parse repository {repo_data.get('full_name', 'unknown')}: {e}[/yellow]"
                        )
                        continue

                console.print(
                    f"  [green]✓[/green] Found {len(repo_data_list)} repos for topic '{topic}'"
                )

            except Exception as e:
                console.print(f"[red]Error searching topic '{topic}': {e}[/red]")
                continue

        return repositories

    def _deduplicate_repositories(
        self, repositories: List[Repository]
    ) -> List[Repository]:
        """Remove duplicate repositories."""
        seen = set()
        unique_repos = []

        for repo in repositories:
            if repo.full_name not in seen:
                seen.add(repo.full_name)
                unique_repos.append(repo)

        console.print(
            f"[blue]ℹ[/blue] Removed {len(repositories) - len(unique_repos)} duplicates"
        )
        return unique_repos

    def _filter_repositories(self, repositories: List[Repository]) -> List[Repository]:
        """Filter repositories based on our criteria."""
        filtered = []

        for repo in repositories:
            if self._is_repository_suitable(repo):
                filtered.append(repo)

        console.print(
            f"[blue]ℹ[/blue] Filtered to {len(filtered)} suitable repositories"
        )
        return filtered

    def _is_repository_suitable(self, repo: Repository) -> bool:
        """Check if repository meets our suitability criteria."""
        # Basic viability check (has issues, not archived/disabled)
        if not repo.has_issues or repo.archived or repo.disabled:
            return False

        # Activity check (must be updated within last 6 months)
        if repo.pushed_at:
            six_months_ago = datetime.now() - timedelta(days=180)
            if repo.pushed_at.replace(tzinfo=None) < six_months_ago:
                return False

        # Issue activity check
        if repo.open_issues_count == 0:
            return False

        return True

    def _print_discovery_summary(self):
        """Print a summary of discovered repositories."""
        if not self.discovered_repos:
            console.print("[yellow]No repositories discovered.[/yellow]")
            return

        # Create summary table
        table = Table(title="🎯 Repository Discovery Summary")
        table.add_column("Repository", style="bold")
        table.add_column("Language", style="cyan")
        table.add_column("Stars", justify="right", style="yellow")
        table.add_column("Issues", justify="right", style="green")
        table.add_column("Activity", style="blue")

        # Sort by priority (stars * activity_score)
        sorted_repos = sorted(
            self.discovered_repos,
            key=lambda r: r.stars * r.activity_score,
            reverse=True,
        )

        for repo in sorted_repos[:20]:  # Show top 20
            activity = f"{repo.activity_score:.1f}"
            table.add_row(
                repo.full_name,
                repo.language or "Unknown",
                str(repo.stars),
                str(repo.open_issues_count),
                activity,
            )

        console.print(table)

        # Print statistics
        languages = {}
        total_issues = 0

        for repo in self.discovered_repos:
            lang = repo.language or "Unknown"
            languages[lang] = languages.get(lang, 0) + 1
            total_issues += repo.open_issues_count

        console.print("\n[bold]📊 Statistics:[/bold]")
        console.print(f"  Total repositories: {len(self.discovered_repos)}")
        console.print(f"  Total open issues: {total_issues}")
        console.print(
            f"  Languages: {dict(sorted(languages.items(), key=lambda x: x[1], reverse=True))}"
        )

    def get_top_repositories(self, limit: int = 10) -> List[Repository]:
        """Get top repositories by priority score."""
        if not self.discovered_repos:
            return []

        # Sort by composite score (stars * activity * issue_density)
        def priority_score(repo: Repository) -> float:
            issue_density = repo.open_issues_count / max(repo.stars, 1)
            return repo.stars * repo.activity_score * min(issue_density, 1.0)

        sorted_repos = sorted(self.discovered_repos, key=priority_score, reverse=True)

        return sorted_repos[:limit]

    def get_repositories_by_names(self, repo_names: List[str]) -> List[Repository]:
        """Get repository data directly from a list of repository names."""
        repositories = []

        with Progress() as progress:
            task = progress.add_task(
                "[green]Fetching repositories...", total=len(repo_names)
            )

            for repo_name in repo_names:
                console.print(f"\n[blue]📋 Fetching {repo_name}...[/blue]")

                try:
                    # Use GitHub client to get repository data
                    repo_data_list = self.github.search_repositories(
                        query=f"repo:{repo_name}", per_page=1
                    )

                    if repo_data_list:
                        repo_data = repo_data_list[0]
                        repo_data["discovered_at"] = datetime.now()

                        try:
                            repo = Repository(**repo_data)
                            repositories.append(repo)
                            console.print(f"  [green]✓[/green] Added {repo_name}")
                        except Exception as e:
                            console.print(
                                f"  [yellow]⚠[/yellow] Could not parse {repo_name}: {e}"
                            )
                    else:
                        console.print(
                            f"  [red]✗[/red] Repository {repo_name} not found or not accessible"
                        )

                except Exception as e:
                    console.print(f"  [red]✗[/red] Error fetching {repo_name}: {e}")

                progress.update(task, advance=1)

        # Filter repositories using the same criteria
        filtered_repos = self._filter_repositories(repositories)

        self.discovered_repos = filtered_repos
        console.print(
            f"\n[blue]ℹ[/blue] Successfully fetched {len(filtered_repos)} repositories"
        )

        return filtered_repos
