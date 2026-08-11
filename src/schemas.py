"""Validated data contracts used by the extractor and user interface."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


RequiredField = Literal[
    "customer_name", "product", "quantity", "location", "deadline"
]
Priority = Literal["low", "medium", "high", "urgent", "unknown"]

REQUIRED_BUSINESS_FIELDS: tuple[RequiredField, ...] = (
    "customer_name",
    "product",
    "quantity",
    "location",
    "deadline",
)


class CustomerRequest(BaseModel):
    """A customer message converted to structured, evidence-based business data.

    A relevant message must list exactly the required fields whose values are
    unavailable. An irrelevant message has no business values and therefore
    lists every required business field as missing.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    customer_name: str | None = Field(
        default=None, description="Customer name stated in the message, if available."
    )
    product: str | None = Field(
        default=None, description="Requested product or service, if available."
    )
    quantity: int | None = Field(
        default=None, gt=0, description="Requested positive whole-number quantity."
    )
    location: str | None = Field(
        default=None, description="Delivery location stated in the message."
    )
    deadline: str | None = Field(
        default=None,
        description="Deadline phrase as stated; do not invent an exact date.",
    )
    priority: Priority = Field(
        description="Business urgency stated or reasonably inferable from the message."
    )
    missing_fields: list[RequiredField] = Field(
        description="Required business fields that have no supported value."
    )
    is_relevant: bool = Field(
        description="Whether the message is a customer request suitable for extraction."
    )
    contradictions: list[str] = Field(
        default_factory=list,
        description="Unresolved conflicts in the message; affected values are null.",
    )
    language: str = Field(description="Detected language, such as English or Roman Urdu.")

    @field_validator("customer_name", "product", "location", "deadline")
    @classmethod
    def optional_text_must_not_be_blank(cls, value: str | None) -> str | None:
        if value == "":
            raise ValueError("text values must be null or non-blank")
        return value

    @field_validator("language")
    @classmethod
    def language_must_not_be_blank(cls, value: str) -> str:
        if not value:
            raise ValueError("language must not be blank")
        return value

    @field_validator("missing_fields")
    @classmethod
    def missing_fields_must_be_unique(cls, value: list[RequiredField]) -> list[RequiredField]:
        if len(value) != len(set(value)):
            raise ValueError("missing_fields must not contain duplicates")
        return value

    @model_validator(mode="after")
    def check_field_consistency(self) -> "CustomerRequest":
        expected_missing = {
            field for field in REQUIRED_BUSINESS_FIELDS if getattr(self, field) is None
        }
        actual_missing = set(self.missing_fields)

        if actual_missing != expected_missing:
            raise ValueError(
                "missing_fields must exactly match required business fields with null values"
            )

        if not self.is_relevant:
            if any(getattr(self, field) is not None for field in REQUIRED_BUSINESS_FIELDS):
                raise ValueError("irrelevant messages must not include business field values")
            if self.priority != "unknown":
                raise ValueError("irrelevant messages must use priority 'unknown'")

        return self

