# AI Customer Message Extractor

An educational Streamlit project that converts messy customer messages into
validated business data. Gemini will provide structured extraction, while
Pydantic independently enforces the output contract.

## Current status

The project includes a Gemini extraction service using the official `google-genai` SDK.
It requests JSON constrained by the Pydantic schema and validates the returned
data independently before the application uses it. The Streamlit interface is
available; evaluation and the correction screen will be added in later phases.

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

## Run the app

```powershell
streamlit run app.py
```

The app opens in your browser. Enter a message and select **Extract**; Gemini
is called only after that button is pressed.

## Test dataset

[`data/test_cases.json`](data/test_cases.json) is a versioned, manually labelled
evaluation dataset. Version 1.0.0 contains 30 cases: 8 complete English
requests, 5 incomplete requests, 4 contradictory requests, 4 multilingual or
Roman Urdu requests, 3 irrelevant messages, 3 invalid or boundary-quantity
messages, and 3 ambiguous deadline or priority messages.

The labels are a starting point for human review. Review every expected result
against the extraction rules before treating evaluation results as meaningful.
The production extractor receives only each original message, never its expected
answer.

## Run a live evaluation

```powershell
python scripts/evaluate.py
```

This sends all 30 messages to Gemini and writes a timestamped JSON report in
`evaluation_reports/`, which is intentionally ignored by Git. The report records
the UTC date, Gemini model, prompt version, dataset version, and Python version.

Metrics are defined as follows:

- **Exact-record accuracy:** the proportion of completed cases where every field
  matches its expected value.
- **Field-level exact-match accuracy:** correct field comparisons divided by all
  field comparisons for completed cases.
- **Per-field accuracy:** exact-match accuracy calculated independently for each
  schema field.
- **Performance by category:** exact-record accuracy grouped by test category.
- **Latency:** mean, median, and nearest-rank P95 request time in milliseconds.

Only `priority` and `language` are compared case-insensitively. `missing_fields`
is treated as an unordered set because its order has no business meaning; other
fields, including contradictions, are compared exactly.

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
