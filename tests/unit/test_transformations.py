from openf1_pipeline.transformations import normalize_records, validate_records


def test_normalize_converts_date_and_removes_duplicates():
    records = [
        {"session_key": "9158", "date": "2023-09-10T14:30:20Z"},
        {"session_key": "9158", "date": "2023-09-10T14:30:20Z"},
    ]
    result = normalize_records(records)
    assert len(result) == 1
    assert str(result.loc[0, "session_key"]) == "9158"
    assert result.loc[0, "date"] == "2023-09-10T14:30:20+00:00"


def test_validation_reports_missing_fields():
    assert validate_records([{"session_key": None}], ("session_key",)) == [
        "registro 0: campos obrigatórios ausentes: session_key"
    ]


def test_validation_reports_out_of_range_values():
    assert validate_records([{"speed": 450}]) == ["registro 0: speed fora da faixa [0, 400]"]


def test_normalize_handles_empty_response():
    assert normalize_records([]).empty


def test_normalize_deduplicates_records_with_nested_values():
    records = [
        {"session_key": 1, "segments": [1, 2], "metadata": {"sector": 1}},
        {"session_key": 1, "segments": [1, 2], "metadata": {"sector": 1}},
    ]
    assert len(normalize_records(records)) == 1


def test_normalize_preserves_lapped_interval_labels():
    result = normalize_records([{"interval": "+1 LAP", "gap_to_leader": "+1 LAP"}])
    assert result.loc[0, "interval"] == "+1 LAP"
    assert result.loc[0, "gap_to_leader"] == "+1 LAP"
