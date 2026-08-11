from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from google.genai import errors

from src.config import ConfigurationError
from src.extractor import (
    AuthenticationError,
    EmptyMessageError,
    ExtractionValidationError,
    NetworkError,
    extract_customer_request,
)


VALID_RESPONSE = {
    "customer_name": "Ali Khan",
    "product": "HP laptops",
    "quantity": 5,
    "location": "Quetta",
    "deadline": "before Friday",
    "priority": "urgent",
    "missing_fields": [],
    "is_relevant": True,
    "contradictions": [],
    "language": "English",
}


def patch_client(monkeypatch: pytest.MonkeyPatch, response: object) -> Mock:
    if isinstance(response, BaseException):
        generate_content = Mock(side_effect=response)
    else:
        generate_content = Mock(return_value=response)
    client = SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))
    monkeypatch.setattr("src.extractor.create_gemini_client", lambda: (client, "test-model"))
    return generate_content


def test_extracts_and_revalidates_structured_response(monkeypatch: pytest.MonkeyPatch) -> None:
    generate_content = patch_client(monkeypatch, SimpleNamespace(parsed=VALID_RESPONSE))

    result = extract_customer_request("Please send five HP laptops to Quetta.")

    assert result.customer_name == "Ali Khan"
    assert generate_content.call_args.kwargs["contents"] == "Please send five HP laptops to Quetta."
    config = generate_content.call_args.kwargs["config"]
    assert config.response_schema is not None
    assert config.system_instruction


def test_empty_message_does_not_call_gemini(monkeypatch: pytest.MonkeyPatch) -> None:
    create_client = Mock()
    monkeypatch.setattr("src.extractor.create_gemini_client", create_client)

    with pytest.raises(EmptyMessageError):
        extract_customer_request("  ")

    create_client.assert_not_called()


def test_invalid_model_data_raises_safe_validation_error(monkeypatch: pytest.MonkeyPatch) -> None:
    invalid = {**VALID_RESPONSE, "quantity": 0}
    patch_client(monkeypatch, SimpleNamespace(parsed=invalid))

    with pytest.raises(ExtractionValidationError):
        extract_customer_request("Send laptops.")


def test_irrelevant_message_response_is_supported(monkeypatch: pytest.MonkeyPatch) -> None:
    irrelevant = {
        "customer_name": None,
        "product": None,
        "quantity": None,
        "location": None,
        "deadline": None,
        "priority": "unknown",
        "missing_fields": ["customer_name", "product", "quantity", "location", "deadline"],
        "is_relevant": False,
        "contradictions": [],
        "language": "English",
    }
    patch_client(monkeypatch, SimpleNamespace(parsed=irrelevant))

    assert extract_customer_request("What is the capital of France?").is_relevant is False


def test_authentication_error_is_user_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_client(monkeypatch, errors.ClientError(401, {"message": "secret detail"}))

    with pytest.raises(AuthenticationError, match="API key"):
        extract_customer_request("Send one laptop.")


def test_server_error_is_user_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_client(monkeypatch, errors.ServerError(503, {"message": "provider detail"}))

    with pytest.raises(NetworkError, match="temporarily unavailable"):
        extract_customer_request("Send one laptop.")


def test_missing_configuration_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_to_create_client() -> tuple[object, str]:
        raise ConfigurationError("GEMINI_API_KEY is not configured.")

    monkeypatch.setattr("src.extractor.create_gemini_client", fail_to_create_client)

    with pytest.raises(ConfigurationError, match="GEMINI_API_KEY"):
        extract_customer_request("Send one laptop.")
