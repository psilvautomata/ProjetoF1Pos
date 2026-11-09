import json
from unittest.mock import Mock

from openf1_pipeline.pipelines import IngestionPipeline


def test_ingest_meeting_discovers_sessions_and_writes_outputs(settings):
    client = Mock()
    client.get.side_effect = [
        [{"meeting_key": 1219, "meeting_name": "São Paulo Grand Prix"}],
        [{"session_key": 9161, "session_name": "Race"}],
        [{"session_key": 9161, "driver_number": 1}],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    ]
    result = IngestionPipeline(client, settings).ingest_meeting(1219)
    assert result["sessions"][0]["session_key"] == 9161
    raw = settings.data_dir / "raw" / "meeting_1219" / "meetings.json"
    assert json.loads(raw.read_text(encoding="utf-8"))[0]["meeting_key"] == 1219
    assert (settings.data_dir / "processed" / "session_9161" / "drivers.csv").exists()
    called = [call.args[0] for call in client.get.call_args_list]
    assert "intervals" in called


def test_intervals_skipped_for_non_race_session(settings):
    client = Mock()
    client.get.side_effect = [
        [{"session_key": 1, "session_name": "Practice 1"}],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    ]
    IngestionPipeline(client, settings).ingest_session(1)
    assert all(call.args[0] != "intervals" for call in client.get.call_args_list)


def test_ingest_year_builds_dashboard_data_and_manifest(settings):
    client = Mock()
    client.get.side_effect = [
        [
            {
                "meeting_key": 44,
                "year": 2024,
                "circuit_short_name": "Monaco",
                "meeting_name": "Monaco GP",
            }
        ],
        [
            {
                "session_key": 71,
                "meeting_key": 44,
                "session_name": "Qualifying",
                "session_type": "Qualifying",
                "date_end": "2024-05-25T16:00:00+00:00",
            }
        ],
        [{"session_key": 71, "driver_number": 16, "full_name": "Charles Leclerc"}],
        [{"session_key": 71, "driver_number": 16, "lap_number": 5, "lap_duration": 72.0}],
    ]

    result = IngestionPipeline(client, settings).ingest_year(2024)

    assert result["status"] == "complete"
    csv_path = settings.data_dir / "processed" / "dashboard" / "lap_rankings.csv"
    rows = csv_path.read_text(encoding="utf-8")
    assert "Monaco" in rows and "Charles Leclerc" in rows
    manifest = settings.data_dir / "processed" / "dashboard" / "ingestion_manifest.json"
    assert json.loads(manifest.read_text(encoding="utf-8"))["years"]["2024"]["status"] == "complete"


def test_ingest_year_skips_sessions_not_yet_ended(settings):
    client = Mock()
    client.get.side_effect = [
        [{"meeting_key": 44, "year": 2026, "circuit_short_name": "Monaco"}],
        [
            {
                "session_key": 72,
                "meeting_key": 44,
                "session_name": "Race",
                "session_type": "Race",
                "date_end": "2999-05-26T16:00:00+00:00",
            }
        ],
    ]

    result = IngestionPipeline(client, settings).ingest_year(2026)

    assert result["status"] == "partial"
    assert result["pending_session_count"] == 1
    assert result["sessions"][0]["status"] == "pending"
    assert [call.args[0] for call in client.get.call_args_list] == ["meetings", "sessions"]


def test_ingest_year_rejects_pre_2023_year(settings):
    client = Mock()
    try:
        IngestionPipeline(client, settings).ingest_year(2022)
    except ValueError as exc:
        assert "2023" in str(exc)
    else:
        raise AssertionError("ano anterior à cobertura deveria ser rejeitado")
    client.get.assert_not_called()
