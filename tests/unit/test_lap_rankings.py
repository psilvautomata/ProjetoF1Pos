import pandas as pd

from openf1_pipeline.services import build_lap_dataset, format_lap_duration, top_five_laps


def test_build_lap_dataset_joins_metadata_and_filters_invalid_laps():
    meetings = [
        {
            "meeting_key": 44,
            "year": 2024,
            "circuit_short_name": "Monaco",
            "meeting_name": "Monaco GP",
        }
    ]
    sessions = [
        {
            "session_key": 71,
            "meeting_key": 44,
            "session_name": "Qualifying",
            "session_type": "Qualifying",
        }
    ]
    drivers = [{"session_key": 71, "driver_number": 16, "full_name": "Charles Leclerc"}]
    laps = [
        {"session_key": 71, "driver_number": 16, "lap_number": 5, "lap_duration": 72.0},
        {
            "session_key": 71,
            "driver_number": 16,
            "lap_number": 6,
            "lap_duration": 71.0,
            "is_pit_out_lap": True,
        },
        {"session_key": 71, "driver_number": 16, "lap_number": 7, "lap_duration": None},
    ]

    result = build_lap_dataset(laps, meetings, sessions, drivers)

    assert len(result) == 1
    assert result.loc[0, "circuit_short_name"] == "Monaco"
    assert result.loc[0, "driver_name"] == "Charles Leclerc"
    assert result.loc[0, "lap_duration"] == 72.0


def test_top_five_laps_applies_group_and_session_filter_stably():
    rows = [
        {
            "year": 2024,
            "circuit_short_name": "Monaco",
            "meeting_key": 44,
            "session_key": 71,
            "session_type": "Qualifying",
            "driver_number": number,
            "lap_number": 1,
            "lap_duration": duration,
        }
        for number, duration in enumerate((72.0, 71.0, 70.0, 69.0, 68.0, 67.0, 66.0))
    ]
    rows.append({**rows[0], "year": 2023, "lap_duration": 50.0})
    rows.append({**rows[1], "session_type": "Race", "lap_duration": 65.0})

    result = top_five_laps(pd.DataFrame(rows), 2024, "Monaco", "Qualifying")

    assert len(result) == 5
    assert result["lap_duration"].tolist() == [66.0, 67.0, 68.0, 69.0, 70.0]


def test_format_lap_duration_returns_minutes_and_milliseconds():
    assert format_lap_duration(91.743) == "1:31.743"
    assert format_lap_duration(59.9999) == "1:00.000"
