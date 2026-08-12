# AI Customer Message Extractor

A portfolio project that turns unstructured customer messages into validated
business data. A Streamlit interface sends the message to Gemini using
structured output; Pydantic validates the result before it reaches the user.

## Problem

Customer requests often arrive as informal, incomplete, multilingual, or
contradictory text. Copying those messages into an order system manually is
slow and error-prone. This project extracts the operational fields a team needs
while making missing information and unresolved conflicts visible.

## Features

- Extracts customer name, product, quantity, location, deadline, priority, and language.
- Detects irrelevant messages, missing required information, and contradictions.
- Uses the official `google-genai` SDK with Gemini structured output.
- Validates every prediction independently with Pydantic v2.
- Gives clear Streamlit feedback for empty messages, API problems, and invalid output.
- Includes 30 human-labelled evaluation cases and a reproducible live evaluator.
- Provides a correction screen that validates and saves explicit human feedback locally.

## Architecture

```text
Customer message
      |
      v
Streamlit UI (app.py) ---> Gemini structured output ---> CustomerRequest validation
      |                                                    |
      |                                                    v
      |---------------------------------------> summary + validated JSON
      |
      +-- optional human correction --> corrected_examples.jsonl (local only)

test_cases.json --> evaluate.py --> metrics + timestamped evaluation report
```

## Technology stack

- Python 3.11+
- Gemini API through `google-genai`
- Pydantic v2
- Streamlit
- python-dotenv
- pytest

## Installation

```powershell
git clone https://github.com/monis0908/AI-Customer-Message-Extractor.git
cd AI-Customer-Message-Extractor
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` with your own credentials. Do not commit it:

```env
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=models/gemini-3.6-flash
```

The model name is environment configuration rather than an application
constant, so you can change it without editing source code. Confirm availability
for your own Gemini account in Google AI Studio.

## Run the app

```powershell
streamlit run app.py
```

Open the local URL shown in the terminal. Gemini is called only when you press
**Extract**—typing, refreshing, and choosing an example do not use API quota.

Example input:

```text
My name is Ali Khan. I need 5 HP laptops delivered to Quetta before Friday. This is urgent.
```

Example output (abridged):

```json
{
  "customer_name": "Ali Khan",
  "product": "HP laptops",
  "quantity": 5,
  "location": "Quetta",
  "deadline": "before Friday",
  "priority": "urgent",
  "missing_fields": [],
  "is_relevant": true,
  "contradictions": [],
  "language": "English"
}
```

## Schema and extraction rules

`CustomerRequest` is the central Pydantic contract. Required business fields
are `customer_name`, `product`, `quantity`, `location`, and `deadline`.

- A provided quantity must be a positive integer.
- `missing_fields` must exactly match required fields whose values are `null`.
- `priority` is one of `low`, `medium`, `high`, `urgent`, or `unknown`.
- The extractor never invents values or converts vague wording such as “soon”
  into an exact deadline.
- An irrelevant message has null business fields and priority `unknown`.
- An unresolved conflict makes the affected field null and is described in
  `contradictions`.
- Clear corrections in the message may replace an earlier value.
- Names, products, and locations remain in their original language where practical.

Gemini receives system extraction rules separately from the customer message.
Gemini's structured response is then independently revalidated by Pydantic;
the application does not parse JSON with regular expressions.

## Tests

```powershell
python -m pytest -q
```

Unit tests mock Gemini, so they use no API quota and require no network.
Coverage includes schema rules, empty input, irrelevant and contradictory
responses, Gemini error handling, correction saving, and metric calculations.

## Evaluation dataset and metrics

[`data/test_cases.json`](data/test_cases.json) is dataset version `1.0.0` with
30 manually labelled cases:

| Category | Cases |
| --- | ---: |
| Complete English | 8 |
| Incomplete | 5 |
| Contradictory | 4 |
| Multilingual / Roman Urdu | 4 |
| Irrelevant | 3 |
| Invalid or boundary quantity | 3 |
| Ambiguous deadline or priority | 3 |

Review labels whenever extraction policy changes. The evaluation script sends
only the original messages to Gemini; expected answers are used locally after
the prediction returns.

Run a live evaluation:

```powershell
python scripts/evaluate.py
```

It writes a timestamped JSON file to the ignored `evaluation_reports/` folder,
including date, Gemini model, prompt version, dataset version, and Python
version.

- **Exact-record accuracy:** completed records with every field exactly correct,
  divided by completed records.
- **Field-level exact-match accuracy:** correct field comparisons divided by all
  completed field comparisons.
- **Per-field accuracy:** exact-match accuracy for each individual field.
- **Performance by category:** exact-record accuracy grouped by category.
- **Latency:** mean, median, and nearest-rank P95 request latency.

Only priority and language compare case-insensitively. Missing fields compare as
an unordered set; all other fields, including contradictions, compare exactly.

### Latest evaluation result

The most recent run (2026-08-12, `models/gemini-3.6-flash`, prompt `1.0.0`,
dataset `1.0.0`, Python 3.12.1) completed 21 of 30 cases before nine API
failures consistent with quota/rate limiting. Its results should therefore not
be read as a full-dataset benchmark:

| Metric | Result |
| --- | ---: |
| Completely correct records | 11 / 21 completed |
| Exact-record accuracy | 52.38% |
| Field-level exact-match accuracy | 94.29% |
| Pydantic validation failures | 0 |
| API failures | 9 |
| Mean / median / P95 latency | 8.78 s / 5.22 s / 26.21 s |

Among completed records, deadline wording caused nine mismatches and
contradiction wording caused three. Rerun the evaluation once your account has
sufficient quota to produce a complete 30-case benchmark.

## Corrections

After an extraction, use **Review and correct this extraction** to edit every
field, mark whether the original result was correct, and save it. The app uses
the same `CustomerRequest` validation before appending a JSON Lines record to
`data/corrected_examples.jsonl`.

That file is ignored by Git because it may include customer personal data.
Corrections are collected only for future human review, evaluation, or a
deliberately designed improvement workflow—they are never silently used for
training or sent to Gemini.

## Demo

See [the short demonstration guide](docs/demo.md) for a repeatable walkthrough
of complete, incomplete, contradictory, irrelevant, and correction flows.

## Known limitations

- LLM output can vary between runs and may misunderstand subtle wording.
- Deadline and contradiction descriptions are intentionally compared strictly in
  evaluation, which can penalize semantically similar phrasing.
- The app does not resolve ambiguous requirements; it surfaces them for review.
- Live evaluation is constrained by Gemini account availability, rate limits,
  and quota.
- Corrected examples are local files, not a database or collaboration system.

## Privacy and security

Customer messages may contain personal or commercially sensitive data. Do not
send or store such messages without an appropriate privacy policy, lawful basis,
and user consent. Gemini is a third-party service, so understand its applicable
data handling terms before use. Keep API keys in `.env`, never in source code;
the repository ignores `.env`, virtual environments, reports, and correction
records.

## Future improvements

- Add review queues and role-based access control.
- Add a database only when durable multi-user storage is required.
- Add semantic evaluation for equivalent deadline and contradiction wording.
- Add controlled retry/backoff based on Gemini's returned retry guidance.
- Build a reviewed, privacy-safe dataset before considering fine-tuning or
prompt iteration.

## What I learned

- A structured LLM response still needs application-side validation.
- Explicit missing-data and contradiction policies make AI output safer for
  business workflows.
- Unit tests, labelled evaluation, and live API checks answer different
  reliability questions.
- Rate limits and partial evaluations must be reported honestly rather than
  hidden behind a single accuracy number.
