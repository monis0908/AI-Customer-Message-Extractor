"""Run a live, reproducible Gemini evaluation against labelled test cases."""

import argparse
import json
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.extractor import ExtractionError, ExtractionValidationError, extract_customer_request
from src.metrics import compare_records, latency_summary, summarise_matches
from src.prompts import PROMPT_VERSION
from src.schemas import CustomerRequest


def load_dataset(path: Path) -> tuple[str, list[dict[str, Any]]]:
    """Load and validate human-labelled cases before evaluation starts."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload["cases"]
    for case in cases:
        CustomerRequest.model_validate(case["expected"], extra="forbid")
    return payload["dataset_version"], cases


def evaluate_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate each message independently; expected answers never reach Gemini."""
    completed_records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    latencies_ms: list[float] = []
    validation_failures = 0
    api_failures = 0

    for case in cases:
        started_at = perf_counter()
        try:
            prediction = extract_customer_request(case["message"])
            latency_ms = (perf_counter() - started_at) * 1000
            latencies_ms.append(latency_ms)
            expected = CustomerRequest.model_validate(case["expected"], extra="forbid")
            matches = compare_records(expected.model_dump(mode="json"), prediction.model_dump(mode="json"))
            completed_records.append(
                {
                    "id": case["id"],
                    "category": case["category"],
                    "latency_ms": round(latency_ms, 2),
                    "matches": matches,
                    "mismatched_fields": [field for field, matched in matches.items() if not matched],
                }
            )
        except ExtractionValidationError as error:
            validation_failures += 1
            failures.append({"id": case["id"], "category": case["category"], "type": type(error).__name__, "message": str(error)})
        except ExtractionError as error:
            api_failures += 1
            failures.append({"id": case["id"], "category": case["category"], "type": type(error).__name__, "message": str(error)})

    summary = summarise_matches(completed_records)
    return {
        **summary,
        "total_test_cases": len(cases),
        "pydantic_validation_failures": validation_failures,
        "api_failures": api_failures,
        "latency": latency_summary(latencies_ms),
        "failure_examples": failures,
        "records": completed_records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Gemini extraction against labelled cases.")
    parser.add_argument("--dataset", type=Path, default=PROJECT_ROOT / "data" / "test_cases.json")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "evaluation_reports")
    args = parser.parse_args()

    dataset_version, cases = load_dataset(args.dataset)
    results = evaluate_cases(cases)
    generated_at = datetime.now(UTC)
    report = {
        "metadata": {
            "generated_at_utc": generated_at.isoformat(),
            "gemini_model": __import__("os").getenv("GEMINI_MODEL", "not configured"),
            "prompt_version": PROMPT_VERSION,
            "dataset_version": dataset_version,
            "python_version": platform.python_version(),
        },
        "results": results,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / f"evaluation_{generated_at.strftime('%Y%m%dT%H%M%SZ')}.json"
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Report: {output_path}")
    print(f"Cases: {results['total_test_cases']}")
    print(f"Completed: {results['completed_records']}")
    print(f"Completely correct: {results['completely_correct_records']}")
    print(f"Exact-record accuracy: {results['exact_record_accuracy']:.2%}")
    print(f"Field-level accuracy: {results['field_level_exact_match_accuracy']:.2%}")
    print(f"Pydantic validation failures: {results['pydantic_validation_failures']}")
    print(f"API failures: {results['api_failures']}")
    print(f"Latency (ms): {results['latency']}")


if __name__ == "__main__":
    main()
