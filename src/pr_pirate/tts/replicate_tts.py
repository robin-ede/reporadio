"""Replicate TTS integration using Kokoro model."""

import os
import requests
from pathlib import Path
from rich.console import Console

console = Console()


class ReplicateTTS:
    """Text-to-speech using Replicate's Kokoro model."""

    MODEL_ID = "jaaari/kokoro-82m:f559560eb822dc509045f3921a1921234918b91739db4bf3daab2169b71c7a13"

    def __init__(self):
        """Initialize Replicate TTS client."""
        self.api_token = os.getenv("REPLICATE_API_TOKEN")
        if not self.api_token:
            raise ValueError(
                "REPLICATE_API_TOKEN not found. Please set it in your .env file."
            )

        try:
            import replicate

            self.client = replicate.Client(api_token=self.api_token)
            console.print("[green]✓[/green] Replicate TTS client initialized")
        except ImportError:
            raise ImportError(
                "replicate package not installed. Run: pip install replicate"
            )

    def generate_audio(
        self,
        text: str,
        output_path: str = "issues_summary.wav",
        voice: str = "af_bella",
        speed: float = 1.0,
    ) -> str:
        """Generate audio from text using Replicate Kokoro TTS."""
        console.print(
            f"[blue]🎤 Generating audio with voice '{voice}' at speed {speed}x...[/blue]"
        )

        try:
            # Call Replicate API
            output = self.client.run(
                self.MODEL_ID, input={"text": text, "speed": speed, "voice": voice}
            )

            # Download the audio file
            audio_url = output
            if isinstance(output, list) and len(output) > 0:
                audio_url = output[0]

            console.print("[blue]📥 Downloading audio file...[/blue]")
            self._download_audio(audio_url, output_path)

            console.print(f"[green]✓[/green] Audio saved to: {output_path}")
            return output_path

        except Exception as e:
            console.print(f"[red]❌ Error generating audio: {e}[/red]")
            raise

    def _download_audio(self, url: str, output_path: str) -> None:
        """Download audio file from URL."""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            # Ensure output directory exists
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Write audio data
            with open(output_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

        except requests.RequestException as e:
            raise Exception(f"Failed to download audio: {e}")

    def get_available_voices(self) -> list:
        """Get list of available voices for Kokoro model."""
        # Common Kokoro voices based on the model documentation
        return [
            "af_bella",
            "af_nicole",
            "af_sarah",
            "am_adam",
            "am_michael",
            "bf_emma",
            "bf_isabella",
            "bm_lewis",
            "bm_george",
        ]

    def preview_script(self, text: str, max_chars: int = 200) -> str:
        """Generate a preview of the script for TTS."""
        if len(text) <= max_chars:
            return text

        # Find a good breaking point
        preview = text[:max_chars]
        last_sentence = preview.rfind(".")
        if (
            last_sentence > max_chars * 0.7
        ):  # If we can find a sentence break in the last 30%
            preview = preview[: last_sentence + 1]

        return preview + "..."
