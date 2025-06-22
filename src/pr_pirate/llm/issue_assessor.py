"""LLM-based issue assessment and script generation."""

import os
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.progress import Progress

from ..models import Issue, Assessment

console = Console()


class IssueAssessor:
    """Assesses GitHub issues using LLM and generates TTS scripts."""

    def __init__(self):
        """Initialize the issue assessor with available LLM clients."""
        self.anthropic_client = None
        self.openai_client = None

        # Try to initialize Anthropic client
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            try:
                import anthropic

                self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
                console.print("[green]✓[/green] Anthropic Claude client initialized")
            except ImportError:
                console.print(
                    "[yellow]Warning: anthropic package not installed[/yellow]"
                )

        # Try to initialize OpenAI client
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                import openai

                self.openai_client = openai.OpenAI(api_key=openai_key)
                console.print("[green]✓[/green] OpenAI client initialized")
            except ImportError:
                console.print("[yellow]Warning: openai package not installed[/yellow]")

        if not self.anthropic_client and not self.openai_client:
            raise ValueError(
                "No LLM client available. Please set ANTHROPIC_API_KEY or OPENAI_API_KEY in your .env file."
            )

    def assess_issues(
        self, issues: List[Issue], max_workers: int = 3
    ) -> List[Assessment]:
        """Assess multiple issues in parallel and return sorted assessments."""
        assessments = []

        with Progress() as progress:
            task = progress.add_task("[green]Assessing issues...", total=len(issues))

            # Use ThreadPoolExecutor for parallel processing
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_issue = {
                    executor.submit(self._assess_single_issue, issue): issue
                    for issue in issues
                }

                # Process completed tasks as they finish
                for future in as_completed(future_to_issue):
                    issue = future_to_issue[future]
                    try:
                        assessment = future.result()
                        assessments.append(assessment)
                        console.print(
                            f"  [green]✓[/green] Assessed #{issue.number}: {assessment.overall_score:.1f}/10"
                        )
                    except Exception as e:
                        console.print(
                            f"  [red]✗[/red] Failed to assess #{issue.number}: {e}"
                        )

                    progress.update(task, advance=1)

        # Sort by composite score (easiest to hardest)
        assessments.sort(key=lambda x: x.composite_score, reverse=True)
        return assessments

    def _assess_single_issue(self, issue: Issue) -> Assessment:
        """Assess a single issue using the available LLM."""
        prompt = self._create_assessment_prompt(issue)

        if self.anthropic_client:
            response = self._call_anthropic(prompt)
        elif self.openai_client:
            response = self._call_openai(prompt)
        else:
            raise ValueError("No LLM client available")

        return self._parse_assessment_response(issue, response)

    def _create_assessment_prompt(self, issue: Issue) -> str:
        """Create assessment prompt for the LLM."""
        return f"""
Assess this GitHub issue for difficulty and feasibility. Provide scores from 1-10:

Repository: {issue.repo_full_name}
Issue #{issue.number}: {issue.title}
Labels: {", ".join(issue.labels)}
Description: {issue.body[:500] if issue.body else "No description"}

Please rate:
1. Complexity (1=very simple, 10=very complex)
2. Clarity (1=unclear requirements, 10=crystal clear)
3. Scope (1=tiny change, 10=massive undertaking)
4. Feasibility (1=impossible, 10=definitely doable)

Also provide:
- Overall score (1-10)
- Is this doable? (yes/no)
- Confidence (0-1)
- Brief reasoning (2-3 sentences)
- Estimated effort in hours
- Required skills (list)
- Potential risks (list)

Respond in this exact JSON format:
{{
    "complexity_score": 5.0,
    "clarity_score": 8.0,
    "scope_score": 3.0,
    "feasibility_score": 7.0,
    "overall_score": 6.0,
    "is_doable": true,
    "confidence": 0.8,
    "reasoning": "This is a straightforward bug fix with clear reproduction steps.",
    "estimated_effort_hours": 4.0,
    "required_skills": ["Python", "Testing"],
    "potential_risks": ["Breaking existing functionality"]
}}
"""

    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API."""
        response = self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI GPT API."""
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
        )
        return response.choices[0].message.content

    def _parse_assessment_response(self, issue: Issue, response: str) -> Assessment:
        """Parse LLM response into Assessment object."""
        import json

        try:
            # Extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]

            data = json.loads(json_str)

            return Assessment(
                issue_id=issue.id,
                issue_number=issue.number,
                repo_full_name=issue.repo_full_name,
                complexity_score=data["complexity_score"],
                clarity_score=data["clarity_score"],
                scope_score=data["scope_score"],
                feasibility_score=data["feasibility_score"],
                overall_score=data["overall_score"],
                is_doable=data["is_doable"],
                confidence=data["confidence"],
                reasoning=data["reasoning"],
                estimated_effort_hours=data.get("estimated_effort_hours"),
                required_skills=data.get("required_skills", []),
                potential_risks=data.get("potential_risks", []),
                model_used="claude-3-5-sonnet" if self.anthropic_client else "gpt-4",
            )
        except (json.JSONDecodeError, KeyError) as e:
            console.print(
                f"[yellow]Warning: Failed to parse assessment response: {e}[/yellow]"
            )
            # Return default assessment
            return Assessment(
                issue_id=issue.id,
                issue_number=issue.number,
                repo_full_name=issue.repo_full_name,
                complexity_score=5.0,
                clarity_score=5.0,
                scope_score=5.0,
                feasibility_score=5.0,
                overall_score=5.0,
                is_doable=True,
                confidence=0.5,
                reasoning="Could not parse detailed assessment",
                model_used="fallback",
            )

    def generate_audio_script(
        self, issues: List[Issue], assessments: List[Assessment]
    ) -> str:
        """Generate a TTS-friendly script from issues and assessments."""
        from ..templates import AudioScriptTemplate

        # Create issue-assessment pairs sorted by difficulty
        issue_data = []
        assessment_map = {a.issue_id: a for a in assessments}

        for issue in issues:
            if issue.id in assessment_map:
                assessment = assessment_map[issue.id]

                # Determine difficulty level
                composite_score = assessment.composite_score
                if composite_score >= 7.0:
                    difficulty = "Easy"
                elif composite_score >= 5.0:
                    difficulty = "Medium"
                else:
                    difficulty = "Hard"

                # Determine issue type from labels
                issue_type = "Enhancement"
                if any(label.lower() in ["bug", "bugfix"] for label in issue.labels):
                    issue_type = "Bug"
                elif any(
                    label.lower() in ["feature", "enhancement"]
                    for label in issue.labels
                ):
                    issue_type = "Feature"
                elif any(
                    label.lower() in ["documentation", "docs"] for label in issue.labels
                ):
                    issue_type = "Documentation"

                issue_data.append(
                    {
                        "number": len(issue_data) + 1,
                        "repo_name": issue.repo_full_name.split("/")[
                            1
                        ],  # Just repo name
                        "issue_type": issue_type,
                        "title": issue.title,
                        "description": issue.body[:200] + "..."
                        if issue.body and len(issue.body) > 200
                        else issue.body or "No description provided",
                        "difficulty": difficulty,
                        "composite_score": composite_score,
                    }
                )

        # Sort by composite score (easiest first)
        issue_data.sort(key=lambda x: x["composite_score"], reverse=True)

        # Generate script using template
        template = AudioScriptTemplate()
        return template.generate_script(issue_data[:10])  # Top 10 issues
