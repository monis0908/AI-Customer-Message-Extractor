import json

import pytest
from pydantic import ValidationError

from src.corrections import save_corrected_example
from src.schemas import CustomerRequest


def sample_request() -> CustomerRequest:
    return CustomerRequest(
        customer_name="Ali Khan",
        product="laptops",
        quantity=2,
        location="Lahore",
        deadline="Friday",
        priority="high",
        missing_fields=[],
        is_relevant=True,
        contradictions=[],
        language="English",
    )


def test_save_corrected_example_appends_valid_jsonl(tmp_path) -> None:
    destination = tmp_path / "corrections.jsonl"
    record = save_corrected_example(
        original_message="Please send two laptops to Lahore by Friday.",
        original_prediction=sample_request(),
        corrected_result=sample_request(),
        was_correct=True,
        path=destination,
    )

    saved = json.loads(destination.read_text(encoding="utf-8"))
    assert saved["original_message"] == record.original_message
    assert saved["was_correct"] is True
    assert saved["corrected_result"]["quantity"] == 2


def test_save_corrected_example_revalidates_the_message(tmp_path) -> None:
    with pytest.raises(ValidationError, match="original_message"):
        save_corrected_example(
            original_message="   ",
            original_prediction=sample_request(),
            corrected_result=sample_request(),
            was_correct=False,
            path=tmp_path / "corrections.jsonl",
        )
