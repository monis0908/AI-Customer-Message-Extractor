"""Streamlit user interface for AI Customer Message Extractor."""

import streamlit as st

from src.config import ConfigurationError
from src.corrections import CorrectionStorageError, save_corrected_example
from src.extractor import (
    AuthenticationError,
    EmptyMessageError,
    ExtractionError,
    ExtractionValidationError,
    GeminiResponseError,
    NetworkError,
    extract_customer_request,
)
from src.schemas import CustomerRequest, REQUIRED_BUSINESS_FIELDS


EXAMPLES = {
    "Complete request": (
        "My name is Ali Khan. I need 5 HP laptops delivered to Quetta before Friday. "
        "This is urgent."
    ),
    "Incomplete request": "Need some office chairs soon.",
    "Contradiction": "Deliver 10 monitors to Lahore and deliver the same order to Karachi.",
    "Roman Urdu": "Kal Islamabad mein 3 keyboards deliver kar dein. Mera naam Hassan hai.",
}


def set_example(message: str) -> None:
    """Fill the input area without making an API request."""
    st.session_state.message_input = message


def show_result(result: CustomerRequest) -> None:
    """Display both a quick business summary and the validated JSON contract."""
    st.subheader("Extracted request")

    first_column, second_column = st.columns(2)
    with first_column:
        st.write("**Customer:**", result.customer_name or "Not provided")
        st.write("**Product:**", result.product or "Not provided")
        st.write("**Quantity:**", result.quantity if result.quantity is not None else "Not provided")
        st.write("**Location:**", result.location or "Not provided")
    with second_column:
        st.write("**Deadline:**", result.deadline or "Not provided")
        st.write("**Priority:**", result.priority.title())
        st.write("**Language:**", result.language)
        st.write("**Relevant request:**", "Yes" if result.is_relevant else "No")

    if not result.is_relevant:
        st.warning("This message does not appear to be a customer request.")

    if result.missing_fields:
        st.info("Missing required fields: " + ", ".join(result.missing_fields))

    if result.contradictions:
        st.warning("Contradictions found: " + " | ".join(result.contradictions))

    st.subheader("Validated JSON")
    st.json(result.model_dump(mode="json"))


def optional_text(value: str) -> str | None:
    """Turn an empty correction input into the schema's null representation."""
    return value.strip() or None


def show_correction_form(message: str, prediction: CustomerRequest) -> None:
    """Let a reviewer edit and explicitly save a validated correction."""
    st.divider()
    st.subheader("Review and correct this extraction")
    st.caption(
        "Corrections are saved locally for future evaluation or improvement. "
        "They are not sent for training automatically."
    )

    with st.form("correction_form"):
        left_column, right_column = st.columns(2)
        with left_column:
            customer_name = st.text_input("Customer name", value=prediction.customer_name or "")
            product = st.text_input("Product", value=prediction.product or "")
            quantity = st.text_input(
                "Quantity (positive whole number or blank)",
                value="" if prediction.quantity is None else str(prediction.quantity),
            )
            location = st.text_input("Delivery location", value=prediction.location or "")
            deadline = st.text_input("Deadline", value=prediction.deadline or "")
        with right_column:
            priority = st.selectbox(
                "Priority",
                options=["low", "medium", "high", "urgent", "unknown"],
                index=["low", "medium", "high", "urgent", "unknown"].index(prediction.priority),
            )
            is_relevant = st.checkbox("This is a relevant customer request", value=prediction.is_relevant)
            language = st.text_input("Detected language", value=prediction.language)
            missing_fields = st.multiselect(
                "Missing required fields",
                options=list(REQUIRED_BUSINESS_FIELDS),
                default=prediction.missing_fields,
            )
            contradictions = st.text_area(
                "Contradictions (one per line)", value="\n".join(prediction.contradictions)
            )

        was_correct = st.radio(
            "Was the original extraction correct?",
            options=[True, False],
            format_func=lambda value: "Yes" if value else "No",
            horizontal=True,
        )
        save_correction = st.form_submit_button("Validate and save correction", type="primary")

    if not save_correction:
        return

    try:
        parsed_quantity = int(quantity) if quantity.strip() else None
        corrected_result = CustomerRequest.model_validate(
            {
                "customer_name": optional_text(customer_name),
                "product": optional_text(product),
                "quantity": parsed_quantity,
                "location": optional_text(location),
                "deadline": optional_text(deadline),
                "priority": priority,
                "missing_fields": missing_fields,
                "is_relevant": is_relevant,
                "contradictions": [line.strip() for line in contradictions.splitlines() if line.strip()],
                "language": language,
            },
            extra="forbid",
        )
        save_corrected_example(
            original_message=message,
            original_prediction=prediction,
            corrected_result=corrected_result,
            was_correct=was_correct,
        )
    except (ValueError, CorrectionStorageError) as error:
        st.error(f"Correction was not saved: {error}")
    except Exception:
        st.error(
            "Correction was not saved because it does not satisfy the required data format. "
            "Check the quantity and missing fields."
        )
    else:
        st.success("Validated correction saved locally in data/corrected_examples.jsonl.")


def show_error(error: Exception) -> None:
    """Map service errors to helpful messages without leaking sensitive details."""
    if isinstance(error, EmptyMessageError):
        st.warning(str(error))
    elif isinstance(error, ConfigurationError):
        st.error("Gemini is not configured. Add GEMINI_API_KEY and GEMINI_MODEL to .env.")
    elif isinstance(error, AuthenticationError):
        st.error("Gemini could not authenticate. Check your API key in .env.")
    elif isinstance(error, NetworkError):
        st.error("Gemini is unavailable right now. Check your connection and try again.")
    elif isinstance(error, ExtractionValidationError):
        st.error("Gemini returned an unusable result. Please try the message again.")
    elif isinstance(error, GeminiResponseError):
        st.error("Gemini could not process this message. Please try again.")
    else:
        st.error("An unexpected error occurred. Please try again.")


st.set_page_config(page_title="AI Customer Message Extractor", page_icon="📦")
st.title("AI Customer Message Extractor")
st.write(
    "Paste a messy customer message and Gemini will extract validated business data. "
    "The result is checked by Pydantic before it is shown."
)

st.caption("Try an example (this only fills the text area):")
example_columns = st.columns(len(EXAMPLES))
for column, (label, example) in zip(example_columns, EXAMPLES.items()):
    with column:
        st.button(label, on_click=set_example, args=(example,), use_container_width=True)

message = st.text_area(
    "Customer message",
    placeholder="Example: Please send 10 monitors to Lahore by Friday.",
    height=180,
    key="message_input",
)

if st.button("Extract", type="primary"):
    try:
        with st.spinner("Extracting and validating customer data..."):
            st.session_state.last_result = extract_customer_request(message)
            st.session_state.extracted_message = message
    except (ConfigurationError, ExtractionError) as error:
        st.session_state.pop("last_result", None)
        st.session_state.pop("extracted_message", None)
        show_error(error)
    except Exception as error:  # The UI must never reveal SDK or credential details.
        st.session_state.pop("last_result", None)
        st.session_state.pop("extracted_message", None)
        show_error(error)

if (
    "last_result" in st.session_state
    and st.session_state.get("extracted_message") == message
):
    show_result(st.session_state.last_result)
    show_correction_form(message, st.session_state.last_result)
