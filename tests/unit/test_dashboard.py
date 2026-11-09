import json
from pathlib import Path
from unittest.mock import Mock

import pandas as pd
from streamlit.testing.v1 import AppTest

from openf1_pipeline.services import RANKING_COLUMNS

APP_PATH = Path(__file__).resolve().parents[2] / "src" / "openf1_pipeline" / "dashboard" / "app.py"


def _mock_meetings(monkeypatch):
    response = Mock()
    response.json.return_value = [{"year": 2027}, {"year": 2024}, {"year": 2023}]
    response.raise_for_status.return_value = None
    monkeypatch.setattr("requests.get", Mock(return_value=response))


def test_dashboard_explains_how_to_prepare_first_season(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENF1_DATA_DIR", str(tmp_path))
    _mock_meetings(monkeypatch)

    app = AppTest.from_file(str(APP_PATH)).run()

    assert 2027 not in app.selectbox[0].options
    assert any("--year 2024" in item.value for item in app.code)


def test_dashboard_displays_top_five_and_partial_coverage(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENF1_DATA_DIR", str(tmp_path))
    _mock_meetings(monkeypatch)
    dashboard_dir = tmp_path / "processed" / "dashboard"
    dashboard_dir.mkdir(parents=True)
    rows = [
        {
            "year": 2024,
            "circuit_short_name": "Monaco",
            "meeting_key": 44,
            "meeting_name": "Monaco GP",
            "session_key": 71,
            "session_name": "Qualifying",
            "session_type": "Qualifying",
            "driver_number": number,
            "driver_name": f"Driver {number}",
            "lap_number": number,
            "lap_duration": 70.0 + number,
        }
        for number in range(1, 7)
    ]
    pd.DataFrame(rows, columns=RANKING_COLUMNS).to_csv(
        dashboard_dir / "lap_rankings.csv", index=False
    )
    (dashboard_dir / "ingestion_manifest.json").write_text(
        json.dumps({"years": {"2024": {"status": "partial"}}}), encoding="utf-8"
    )

    app = AppTest.from_file(str(APP_PATH)).run()

    assert any("cobertura desta temporada está parcial" in item.value for item in app.warning)
    assert any(item.value == "Monaco · 2024" for item in app.subheader)
    assert len(app.dataframe) == 1
