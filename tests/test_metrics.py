from src.metrics import compare_records, latency_summary, summarise_matches, values_match


def test_priority_and_language_are_case_insensitive() -> None:
    assert values_match("priority", "URGENT", "urgent")
    assert values_match("language", "Roman Urdu", "roman urdu")
    assert not values_match("product", "HP Laptops", "hp laptops")


def test_missing_fields_are_order_independent() -> None:
    assert values_match("missing_fields", ["location", "deadline"], ["deadline", "location"])


def test_compare_records_returns_all_contract_fields() -> None:
    record = {
        "customer_name": "Ali",
        "product": "laptop",
        "quantity": 1,
        "location": "Lahore",
        "deadline": "Friday",
        "priority": "unknown",
        "missing_fields": [],
        "is_relevant": True,
        "contradictions": [],
        "language": "English",
    }
    matches = compare_records(record, {**record, "priority": "UNKNOWN"})
    assert all(matches.values())


def test_summary_calculates_record_field_and_category_accuracy() -> None:
    records = [
        {"category": "complete", "matches": {"product": True, "quantity": True}},
        {"category": "complete", "matches": {"product": True, "quantity": False}},
        {"category": "incomplete", "matches": {"product": False, "quantity": False}},
    ]
    summary = summarise_matches(records)
    assert summary["completely_correct_records"] == 1
    assert summary["exact_record_accuracy"] == 0.3333
    assert summary["field_level_exact_match_accuracy"] == 0.5
    assert summary["performance_by_category"]["complete"]["exact_record_accuracy"] == 0.5


def test_latency_summary_uses_nearest_rank_p95() -> None:
    assert latency_summary([10.0, 20.0, 30.0, 40.0]) == {
        "mean_ms": 25.0,
        "median_ms": 25.0,
        "p95_ms": 40.0,
    }
    assert latency_summary([])["mean_ms"] is None
