"""Streamlit user interface for AI Customer Message Extractor."""

import streamlit as st

from src.config import ConfigurationError
from src.extractor import (
    AuthenticationError,
    EmptyMessageError,
    ExtractionError,
    ExtractionValidationError,
    GeminiResponseError,
    NetworkError,
    extract_customer_request,
)
from src.schemas import CustomerRequest


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
