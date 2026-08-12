"""Pure comparison functions for evaluating extraction predictions."""

from collections import defaultdict
from math import ceil
from statistics import mean, median
from typing import Any


FIELD_NAMES = (
    "customer_name",
    "product",
    "quantity",
    "location",
    "deadline",
    "priority",
    "missing_fields",
    "is_relevant",
    "contradictions",
    "language",
)


def values_match(field: str, expected: Any, predicted: Any) -> bool:
    """Compare one field without normalizing away meaningful extraction mistakes."""
    if field in {"priority", "language"} and isinstance(expected, str) and isinstance(predicted, str):
        return expected.strip().casefold() == predicted.strip().casefold()
    if field == "missing_fields" and isinstance(expected, list) and isinstance(predicted, list):
        return set(expected) == set(predicted)
    return expected == predicted


def compare_records(expected: dict[str, Any], predicted: dict[str, Any]) -> dict[str, bool]:
    """Return an exact-match result for every contract field."""
    return {field: values_match(field, expected.get(field), predicted.get(field)) for field in FIELD_NAMES}


def latency_summary(latencies_ms: list[float]) -> dict[str, float | None]:
    """Return mean, median, and nearest-rank P95 latency in milliseconds."""
    if not latencies_ms:
        return {"mean_ms": None, "median_ms": None, "p95_ms": None}

    ordered = sorted(latencies_ms)
    p95_index = ceil(0.95 * len(ordered)) - 1
    return {
        "mean_ms": round(mean(ordered), 2),
        "median_ms": round(median(ordered), 2),
        "p95_ms": round(ordered[p95_index], 2),
    }


def summarise_matches(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate record, field, and category accuracy from completed comparisons."""
    field_matches = defaultdict(int)
    field_totals = defaultdict(int)
    category_totals = defaultdict(int)
    category_correct = defaultdict(int)
    exact_records = 0

    for record in records:
        matches = record["matches"]
        is_exact = all(matches.values())
        exact_records += int(is_exact)
        category = record["category"]
        category_totals[category] += 1
        category_correct[category] += int(is_exact)
        for field, matched in matches.items():
            field_totals[field] += 1
            field_matches[field] += int(matched)

    total_records = len(records)
    total_field_comparisons = sum(field_totals.values())
    return {
        "completed_records": total_records,
        "completely_correct_records": exact_records,
        "exact_record_accuracy": round(exact_records / total_records, 4) if total_records else 0.0,
        "field_level_exact_match_accuracy": (
            round(sum(field_matches.values()) / total_field_comparisons, 4)
            if total_field_comparisons
            else 0.0
        ),
        "per_field_accuracy": {
            field: round(field_matches[field] / field_totals[field], 4)
            for field in FIELD_NAMES
            if field_totals[field]
        },
        "performance_by_category": {
            category: {
                "total": category_totals[category],
                "completely_correct": category_correct[category],
                "exact_record_accuracy": round(category_correct[category] / category_totals[category], 4),
            }
            for category in sorted(category_totals)
        },
    }
