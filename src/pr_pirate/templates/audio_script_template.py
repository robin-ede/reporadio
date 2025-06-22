"""Template for generating TTS audio scripts."""

from typing import List, Dict, Any


class AudioScriptTemplate:
    """Generates TTS-friendly scripts from issue data."""

    def generate_script(self, issues_data: List[Dict[str, Any]]) -> str:
        """Generate a complete audio script from issue data."""
        script_parts = []

        # Introduction
        script_parts.append(self._generate_intro(len(issues_data)))

        # Issue summaries
        for issue in issues_data:
            script_parts.append(self._generate_issue_summary(issue))

        # Conclusion
        script_parts.append(self._generate_outro())

        return " ".join(script_parts)

    def _generate_intro(self, total_issues: int) -> str:
        """Generate introduction text."""
        return f"""
Welcome to your GitHub Issues Summary! 
I've discovered {total_issues} interesting issues from various repositories, 
and I've ranked them from easiest to hardest based on complexity, clarity, and scope. 
Let's dive into these opportunities to contribute to open source projects.
"""

    def _generate_issue_summary(self, issue: Dict[str, Any]) -> str:
        """Generate summary text for a single issue."""
        return f"""
Issue {issue["number"]} of 10. 
Repository: {issue["repo_name"]}. 
Type: {issue["issue_type"]}. 
Title: {issue["title"]}. 
Description: {issue["description"]}. 
Difficulty Level: {issue["difficulty"]}.
"""

    def _generate_outro(self) -> str:
        """Generate conclusion text."""
        return """
That concludes your GitHub Issues Summary! 
These issues are sorted from easiest to hardest, so you might want to start with the first few. 
Remember to read the full issue descriptions and repository contribution guidelines before diving in. 
Happy coding!
"""

    def generate_preview_text(self, issues_data: List[Dict[str, Any]]) -> str:
        """Generate a short preview of the script for display."""
        if not issues_data:
            return "No issues to preview."

        preview_parts = [
            f"📻 Audio Summary Preview ({len(issues_data)} issues):",
            "",
            "🎯 Top 3 Issues:",
        ]

        for i, issue in enumerate(issues_data[:3], 1):
            preview_parts.append(
                f"  {i}. [{issue['repo_name']}] {issue['issue_type']}: {issue['title'][:50]}... ({issue['difficulty']})"
            )

        if len(issues_data) > 3:
            preview_parts.append(f"  ... and {len(issues_data) - 3} more issues")

        return "\n".join(preview_parts)
