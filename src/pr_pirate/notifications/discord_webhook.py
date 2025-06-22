"""Discord webhook notifications for PR Pirate progress and results."""

import os
import requests
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from ..models import Issue, Assessment


class DiscordNotifier:
    """Send notifications to Discord via webhook."""

    def __init__(self):
        """Initialize Discord webhook notifier."""
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        self.enabled = bool(
            self.webhook_url
            and self.webhook_url
            != "https://discord.com/api/webhooks/your_webhook_url_here"
        )

    def send_message(self, content: str, embed: Optional[dict] = None) -> bool:
        """Send a message to Discord webhook."""
        if not self.enabled:
            return False

        try:
            payload = {"content": content}
            if embed:
                payload["embeds"] = [embed]

            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to send Discord notification: {e}")
            return False

    def send_start_notification(self, categories: List[str], repo_count: int) -> bool:
        """Send notification when PR Pirate starts."""
        embed = {
            "title": "📻 RepoRadio Started",
            "description": "Beginning GitHub issue discovery and analysis",
            "color": 0x00FF00,  # Green
            "fields": [
                {
                    "name": "📂 Categories",
                    "value": ", ".join(categories),
                    "inline": True,
                },
                {
                    "name": "🏛️ Repositories Found",
                    "value": str(repo_count),
                    "inline": True,
                },
                {
                    "name": "⏰ Started",
                    "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "inline": False,
                },
            ],
            "thumbnail": {
                "url": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
            },
        }

        return self.send_message("", embed)

    def send_assessment_results(
        self, issues: List[Issue], assessments: List[Assessment]
    ) -> bool:
        """Send LLM assessment results for top 10 issues."""
        if not issues or not assessments:
            return False

        # Create assessment map
        assessment_map = {a.issue_id: a for a in assessments}

        # Create issue-assessment pairs and sort by composite score (highest to lowest = easiest to hardest)
        issue_assessment_pairs = []
        for issue in issues[:10]:
            if issue.id in assessment_map:
                assessment = assessment_map[issue.id]
                issue_assessment_pairs.append((issue, assessment))

        # Sort by composite score (descending = easiest first)
        issue_assessment_pairs.sort(key=lambda x: x[1].composite_score, reverse=True)

        # Build results list (properly sorted by difficulty)
        results = []
        for i, (issue, assessment) in enumerate(issue_assessment_pairs, 1):
            difficulty = (
                "🟢 Easy"
                if assessment.composite_score >= 7.0
                else "🟡 Medium"
                if assessment.composite_score >= 5.0
                else "🔴 Hard"
            )

            # Determine issue type emoji
            issue_type = "🔧 Enhancement"
            if any(label.lower() in ["bug", "bugfix"] for label in issue.labels):
                issue_type = "🐛 Bug"
            elif any(label.lower() in ["feature"] for label in issue.labels):
                issue_type = "✨ Feature"
            elif any(
                label.lower() in ["documentation", "docs"] for label in issue.labels
            ):
                issue_type = "📚 Docs"

            # Sanitize title to prevent Discord markdown issues
            title_clean = issue.title.replace("`", "\\`")  # Escape backticks
            title_short = (
                title_clean[:50] + "..." if len(title_clean) > 50 else title_clean
            )

            results.append(
                f"`{i:2d}.` [**{issue.repo_full_name}** #{issue.number}]({issue.html_url}) • {issue_type}\n"
                f"    {title_short}\n"
                f"    {difficulty} • Score: {assessment.composite_score:.1f}/10"
            )

        embed = {
            "title": "🎧 LLM Assessment Complete",
            "description": f"Analyzed {len(assessments)} issues and ranked them by difficulty",
            "color": 0x0099FF,  # Blue
            "fields": [
                {
                    "name": "🎯 Top 10 Issues (Easiest → Hardest)",
                    "value": "\n\n".join(results[:5]),  # First 5 issues
                    "inline": False,
                }
            ],
        }

        # Add second field for remaining issues if more than 5
        if len(results) > 5:
            embed["fields"].append(
                {
                    "name": "📋 Issues 6-10",
                    "value": "\n\n".join(results[5:]),
                    "inline": False,
                }
            )

        embed["fields"].append(
            {
                "name": "📊 Assessment Stats",
                "value": f"🟢 Easy: {sum(1 for a in assessments if a.composite_score >= 7.0)} issues\n"
                f"🟡 Medium: {sum(1 for a in assessments if 5.0 <= a.composite_score < 7.0)} issues\n"
                f"🔴 Hard: {sum(1 for a in assessments if a.composite_score < 5.0)} issues",
                "inline": True,
            }
        )

        return self.send_message("", embed)

    def send_audio_complete(
        self,
        audio_path: str,
        script_length: int,
        voice: str,
        speed: float,
        drive_link: Optional[str] = None,
    ) -> bool:
        """Send notification when audio generation is complete."""
        file_size = "Unknown"
        try:
            size_bytes = Path(audio_path).stat().st_size
            file_size = (
                f"{size_bytes / (1024 * 1024):.1f} MB"
                if size_bytes > 1024 * 1024
                else f"{size_bytes / 1024:.1f} KB"
            )
        except:
            pass

        fields = [
            {
                "name": "📁 File Info",
                "value": f"**Path:** `{audio_path}`\n**Size:** {file_size}",
                "inline": True,
            },
            {
                "name": "🎙️ Audio Settings",
                "value": f"**Voice:** {voice}\n**Speed:** {speed}x",
                "inline": True,
            },
            {
                "name": "📝 Script Details",
                "value": f"**Length:** {script_length} characters",
                "inline": False,
            },
        ]

        # Add Google Drive link if available
        if drive_link:
            fields.append(
                {
                    "name": "☁️ Google Drive",
                    "value": f"[📥 Download Audio File]({drive_link})",
                    "inline": False,
                }
            )

        embed = {
            "title": "📻 Audio Broadcast Complete!",
            "description": "Your GitHub issues audio summary is ready",
            "color": 0xFF6B35,  # Orange
            "fields": fields,
            "footer": {"text": "Generated by RepoRadio 📻"},
            "timestamp": datetime.now().isoformat(),
        }

        return self.send_message("🎉 **Audio summary generation complete!**", embed)

    def send_error_notification(self, error_message: str, stage: str) -> bool:
        """Send error notification."""
        embed = {
            "title": "❌ RepoRadio Error",
            "description": f"An error occurred during {stage}",
            "color": 0xFF0000,  # Red
            "fields": [
                {
                    "name": "🚨 Error Details",
                    "value": f"```{error_message[:1000]}```",
                    "inline": False,
                },
                {"name": "📍 Stage", "value": stage, "inline": True},
                {
                    "name": "⏰ Time",
                    "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "inline": True,
                },
            ],
        }

        return self.send_message("🚨 **RepoRadio encountered an error**", embed)

    def send_file(self, file_path: str, message: str = "") -> bool:
        """Send a file to Discord (for audio files)."""
        if not self.enabled:
            return False

        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                data = {"content": message} if message else {}

                response = requests.post(
                    self.webhook_url, data=data, files=files, timeout=30
                )
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Failed to send file to Discord: {e}")
            return False

    def is_enabled(self) -> bool:
        """Check if Discord notifications are enabled."""
        return self.enabled
