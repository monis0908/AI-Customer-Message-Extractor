"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


# Load a local .env file when the app or scripts run from the project root.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


@dataclass(frozen=True)
class GeminiSettings:
    """Credentials and model selection needed for one Gemini request."""

    api_key: str
    model: str


def get_gemini_settings() -> GeminiSettings:
    """Return required Gemini settings or raise a safe configuration error."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "").strip()

    if not api_key:
        raise ConfigurationError("GEMINI_API_KEY is not configured.")
    if not model:
        raise ConfigurationError("GEMINI_MODEL is not configured.")

    return GeminiSettings(api_key=api_key, model=model)


class ConfigurationError(RuntimeError):
    """Raised when required local configuration is missing."""
