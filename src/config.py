"""Application configuration loaded from environment variables."""

from pathlib import Path

from dotenv import load_dotenv


# Load a local .env file when the app or scripts run from the project root.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


REQUIRED_ENVIRONMENT_VARIABLES = ("GEMINI_API_KEY", "GEMINI_MODEL")

