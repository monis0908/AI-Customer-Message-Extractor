"""Gemini-backed extraction with independent Pydantic validation."""

from typing import Any

import httpx
from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from src.config import ConfigurationError, get_gemini_settings
from src.prompts import SYSTEM_INSTRUCTION
from src.schemas import CustomerRequest


class ExtractionError(RuntimeError):
    """Base class for user-safe extraction failures."""


class EmptyMessageError(ExtractionError):
    """Raised before Gemini is called for a blank message."""


class AuthenticationError(ExtractionError):
    """Raised when Gemini rejects the configured credentials."""


class NetworkError(ExtractionError):
    """Raised when Gemini cannot be reached or times out."""


class GeminiResponseError(ExtractionError):
    """Raised when Gemini returns no usable structured response."""


class ExtractionValidationError(ExtractionError):
    """Raised when the model output violates the CustomerRequest contract."""


def create_gemini_client() -> tuple[genai.Client, str]:
    """Create a Gemini client only after environment settings are validated."""
    settings = get_gemini_settings()
    return genai.Client(api_key=settings.api_key), settings.model


def _validate_response(response: Any) -> CustomerRequest:
    """Validate structured SDK output again, independent of Gemini's schema mode."""
    parsed = getattr(response, "parsed", None)
    try:
        if parsed is not None:
            return CustomerRequest.model_validate(parsed, extra="forbid")

        text = getattr(response, "text", None)
        if not text:
            raise GeminiResponseError("Gemini returned no structured result.")
        return CustomerRequest.model_validate_json(text, extra="forbid")
    except ValidationError as error:
        raise ExtractionValidationError(
            "Gemini returned data that did not match the expected customer-request format."
        ) from error


def extract_customer_request(message: str) -> CustomerRequest:
    """Extract a validated customer request from one customer message.

    The system instruction is passed separately through Gemini configuration;
    the untrusted customer message is sent only as request content.
    """
    if not message or not message.strip():
        raise EmptyMessageError("Enter a customer message before extracting data.")

    try:
        client, model = create_gemini_client()
        response = client.models.generate_content(
            model=model,
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=CustomerRequest,
                temperature=0,
            ),
        )
    except ConfigurationError:
        raise
    except errors.ClientError as error:
        if error.code in {401, 403}:
            raise AuthenticationError(
                "Gemini rejected the configured API key. Check your local .env file."
            ) from error
        raise GeminiResponseError("Gemini could not process this request.") from error
    except errors.ServerError as error:
        raise NetworkError("Gemini is temporarily unavailable. Please try again later.") from error
    except (httpx.NetworkError, httpx.TimeoutException) as error:
        raise NetworkError("Could not reach Gemini. Check your connection and try again.") from error
    except errors.APIError as error:
        raise GeminiResponseError("Gemini returned an unexpected API error.") from error

    return _validate_response(response)
