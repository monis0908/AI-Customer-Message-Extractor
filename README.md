# AI Customer Message Extractor

An educational Streamlit project that converts messy customer messages into
validated business data. Gemini will provide structured extraction, while
Pydantic independently enforces the output contract.

## Phase 1 status

This foundation defines the data contract and offline tests. Gemini extraction,
the Streamlit interface, evaluation, and the correction screen will be added in
later phases.

## Setup

Requires Python 3.11+.

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Add your local Gemini credentials to `.env`; never commit that file.

## Run tests

```powershell
pytest
```

## Schema rule

`missing_fields` is not merely a model suggestion: it must exactly list the
five required business fields whose values are `null`. This makes an incomplete
extraction visibly and consistently incomplete.
