"""Validated local storage for human-corrected extraction examples."""

import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.schemas import CustomerRequest


DEFAULT_CORRECTIONS_PATH = Path("data/corrected_examples.jsonl")


class CorrectionRecord(BaseModel):
    """One human-reviewed prediction, retained for later evaluation or improvement."""

    model_config = ConfigDict(extra="forbid")

    created_at_utc: datetime
    original_message: str = Field(min_length=1)
    original_prediction: CustomerRequest
    corrected_result: CustomerRequest
    was_correct: bool

    @field_validator("created_at_utc")
    @classmethod
    def timestamp_must_be_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("created_at_utc must include a timezone")
        return value


class CorrectionStorageError(RuntimeError):
    """Raised when a corrected example cannot be safely stored locally."""


def save_corrected_example(
    *,
    original_message: str,
    original_prediction: CustomerRequest,
    corrected_result: CustomerRequest,
    was_correct: bool,
    path: Path = DEFAULT_CORRECTIONS_PATH,
) -> CorrectionRecord:
    """Validate and append a human correction as one JSON Lines record.

    These examples are deliberately stored only as local data. Nothing here
    sends them to Gemini or uses them to train a model.
    """
    record = CorrectionRecord(
        created_at_utc=datetime.now(UTC),
        original_message=original_message.strip(),
        original_prediction=original_prediction,
        corrected_result=corrected_result,
        was_correct=was_correct,
    )
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as file:
            file.write(record.model_dump_json() + "\n")
    except OSError as error:
        raise CorrectionStorageError("The corrected example could not be saved locally.") from error
    return record
