# AI Customer Message Extractor

An educational Streamlit project that converts messy customer messages into
validated business data. Gemini will provide structured extraction, while
Pydantic independently enforces the output contract.

## Phase 1 status

Phase 2 adds a Gemini extraction service using the official `google-genai` SDK.
It requests JSON constrained by the Pydantic schema and validates the returned
data independently before the application uses it. The Streamlit interface,
evaluation, and correction screen will be added in later phases.

## Setup

Requires Python 3.11+.

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Add your local Gemini credentials to `.env`; never commit that file. The sample
model is `models/gemini-3.6-flash`, a fast model suitable for structured
extraction. Keep the model name in `GEMINI_MODEL` rather than code.

## Run tests

```powershell
pytest
```

## Schema rule

`missing_fields` is not merely a model suggestion: it must exactly list the
five required business fields whose values are `null`. This makes an incomplete
extraction visibly and consistently incomplete.

## Gemini extraction

`extract_customer_request(message)` sends the customer message separately from
the extraction policy. Gemini is configured for `application/json` and the
`CustomerRequest` response schema; Pydantic then validates the SDK response a
second time. Unit tests mock the Gemini call, so running `pytest` uses no API
quota and needs no network connection.
