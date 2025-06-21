#!/usr/bin/env python3
"""
Simple example of using the PR Pirate discovery system.

This example shows how to discover repositories and issues
without the full CLI interface.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pr_pirate.discovery import GitHubClient, RepositoryDiscoverer, IssueDiscoverer


def main():
    # Check for GitHub token
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Please set GITHUB_TOKEN environment variable")
        return 1

    print("🏴‍☠️ PR Pirate Discovery Example")
    print("=" * 40)

    # Initialize client
    client = GitHubClient(token)

    # Discover repositories
    print("\n📋 Discovering repositories...")
    repo_discoverer = RepositoryDiscoverer(client)

    repositories = repo_discoverer.discover_repositories(
        categories=["llm"],  # Just LLM repos for this example
        min_stars=50,
        max_stars=2000,
        max_repos_per_query=10,
    )

    print(f"Found {len(repositories)} repositories")

    if repositories:
        # Show top 3 repositories
        top_repos = repo_discoverer.get_top_repositories(limit=3)
        print(f"\nTop {len(top_repos)} repositories:")
        for i, repo in enumerate(top_repos, 1):
            print(f"  {i}. {repo.full_name} ({repo.stars} ⭐)")

        # Discover issues from top repository
        print(f"\n🎯 Discovering issues from {top_repos[0].full_name}...")
        issue_discoverer = IssueDiscoverer(client)

        issues = issue_discoverer.discover_issues(
            repositories=[top_repos[0]],  # Just the top repo
            max_issues_per_repo=5,
            include_unlabeled=False,
        )

        print(f"Found {len(issues)} suitable issues")

        if issues:
            print("\nTop issues:")
            for i, issue in enumerate(issues[:3], 1):
                print(f"  {i}. #{issue.number}: {issue.title[:50]}...")
                print(f"     Labels: {', '.join(issue.labels[:3])}")
                print(f"     Priority: {issue.priority_score:.2f}")
                print()

    print("✅ Discovery example complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
