import pytest
from pydantic import ValidationError

from src.schemas import CustomerRequest, REQUIRED_BUSINESS_FIELDS


def valid_request(**overrides: object) -> CustomerRequest:
    data: dict[str, object] = {
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
    data.update(overrides)
    return CustomerRequest.model_validate(data)


def test_valid_customer_request() -> None:
    request = valid_request()
    assert request.quantity == 5
    assert request.priority == "urgent"


def test_missing_optional_values_require_matching_missing_fields() -> None:
    request = valid_request(
        customer_name=None,
        quantity=None,
        location=None,
        deadline=None,
        missing_fields=["customer_name", "quantity", "location", "deadline"],
    )
    assert request.product == "HP laptops"
    assert set(request.missing_fields) == {"customer_name", "quantity", "location", "deadline"}


@pytest.mark.parametrize("quantity", [0, -1])
def test_quantity_must_be_positive_when_provided(quantity: int) -> None:
    with pytest.raises(ValidationError):
        valid_request(quantity=quantity)


def test_priority_must_match_allowed_values() -> None:
    with pytest.raises(ValidationError):
        valid_request(priority="asap")


def test_missing_fields_must_be_consistent_with_null_values() -> None:
    with pytest.raises(ValidationError, match="missing_fields"):
        valid_request(customer_name=None, missing_fields=[])


def test_irrelevant_message_has_no_business_values_and_unknown_priority() -> None:
    request = CustomerRequest(
        customer_name=None,
        product=None,
        quantity=None,
        location=None,
        deadline=None,
        priority="unknown",
        missing_fields=list(REQUIRED_BUSINESS_FIELDS),
        is_relevant=False,
        language="English",
    )
    assert request.is_relevant is False


def test_irrelevant_message_rejects_business_values() -> None:
    with pytest.raises(ValidationError, match="irrelevant"):
        valid_request(is_relevant=False, priority="unknown")


def test_blank_optional_text_is_rejected() -> None:
    with pytest.raises(ValidationError, match="non-blank"):
        valid_request(product="")


def test_production_validation_rejects_unexpected_fields() -> None:
    data = valid_request().model_dump() | {"unexpected_field": "not allowed"}

    with pytest.raises(ValidationError, match="unexpected_field"):
        CustomerRequest.model_validate(data, extra="forbid")
