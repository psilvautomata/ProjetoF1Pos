"""Interface Streamlit para explorar os cinco melhores tempos por pista/ano."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from openf1_pipeline.config import get_settings
from openf1_pipeline.connectors import OpenF1Client
from openf1_pipeline.connectors.openf1 import OpenF1Error
from openf1_pipeline.services import RANKING_COLUMNS, format_lap_duration, top_five_laps


@st.cache_data(show_spinner=False)
def _load_data(
    csv_path: str | None,
    manifest_path: str | None,
    csv_modified: int,
    manifest_modified: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    laps = pd.read_csv(csv_path) if csv_path else pd.DataFrame(columns=RANKING_COLUMNS)
    manifest = (
        json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        if manifest_path
        else {"years": {}}
    )
    return laps, manifest


@st.cache_data(ttl=86400, show_spinner=False)
def _load_free_seasons() -> list[int]:
    """Descobre temporadas com meetings históricos, sem consultar telemetria ao vivo."""
    meetings = OpenF1Client().get("meetings", {"year>=": 2023})
    current_year = datetime.now(UTC).year
    return sorted(
        {
            int(meeting["year"])
            for meeting in meetings
            if meeting.get("year") is not None and int(meeting["year"]) <= current_year
        },
        reverse=True,
    )


def main() -> None:
    """Renderiza filtros, cobertura de dados e ranking de voltas."""
    st.set_page_config(page_title="F1 | Voltas mais rápidas", page_icon="🏎️", layout="wide")
    st.markdown(
        """
        <style>
        .block-container {padding-top: 2.4rem; padding-bottom: 3rem;}
        [data-testid="stMetric"] {
            border: 1px solid rgba(225, 6, 0, .18);
            border-radius: 12px;
            padding: 14px 16px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("🏁 Voltas mais rápidas da Fórmula 1")
    st.caption(
        "As cinco voltas válidas mais rápidas por pista e temporada, "
        "com dados históricos da OpenF1. "
        "O histórico gratuito começa em 2023; as temporadas disponíveis são descobertas pela API."
    )

    dashboard_dir = get_settings().data_dir / "processed" / "dashboard"
    csv_path = dashboard_dir / "lap_rankings.csv"
    manifest_path = dashboard_dir / "ingestion_manifest.json"
    laps, manifest = _load_data(
        str(csv_path) if csv_path.exists() else None,
        str(manifest_path) if manifest_path.exists() else None,
        csv_path.stat().st_mtime_ns if csv_path.exists() else 0,
        manifest_path.stat().st_mtime_ns if manifest_path.exists() else 0,
    )
    year_statuses = manifest.get("years", {})
    api_error = None
    try:
        api_years = _load_free_seasons()
    except OpenF1Error as exc:
        api_years = []
        api_error = str(exc)
    local_years = {int(year) for year in year_statuses if str(year).isdigit() and int(year) >= 2023}
    if not laps.empty and "year" in laps:
        local_years.update(
            pd.to_numeric(laps["year"], errors="coerce").dropna().astype(int).unique().tolist()
        )
    years = sorted(set(api_years) | local_years, reverse=True)
    if api_error:
        st.warning(
            "Não foi possível atualizar as temporadas pela API; "
            "exibindo os anos já disponíveis localmente. "
            f"Detalhe: {api_error}"
        )
    if not years:
        st.info(
            "Não foi possível obter temporadas pela API e ainda não há temporadas importadas. "
            "A OpenF1 oferece histórico gratuito a partir de 2023."
        )
        st.stop()
    with st.container(border=True):
        year_column, track_column, session_column = st.columns(3)
        year = year_column.selectbox("Temporada", years)
        year_data = (
            laps.loc[pd.to_numeric(laps["year"], errors="coerce") == year]
            if not laps.empty
            else laps
        )
        if year_data.empty:
            st.info(
                f"A temporada {year} está disponível no histórico gratuito da API, "
                "mas ainda não foi importada."
            )
            st.code(
                f"poetry run python -m openf1_pipeline --year {year}",
                language="powershell",
            )
            st.stop()
        available_tracks = sorted(year_data["circuit_short_name"].dropna().unique())
        if not available_tracks:
            st.warning("Não há pistas disponíveis para esta temporada.")
            st.stop()
        circuit = track_column.selectbox("Pista", available_tracks)
        session_types = sorted(
            year_data.loc[
                year_data["circuit_short_name"] == circuit,
                "session_type",
            ]
            .dropna()
            .astype(str)
            .unique()
        )
        selected_session = session_column.selectbox("Tipo de sessão", ["Todos", *session_types])

    year_status = manifest.get("years", {}).get(str(year), {})
    if year_status.get("status") != "complete":
        st.warning(
            "A cobertura desta temporada está parcial. "
            "O ranking inclui apenas os dados que foram ingeridos."
        )
    else:
        st.success("Todos os meetings e sessões não cancelados desta temporada foram ingeridos.")
    with st.expander("Detalhes da cobertura"):
        coverage_columns = st.columns(3)
        coverage_columns[0].metric("Meetings", year_status.get("meeting_count", 0))
        coverage_columns[1].metric("Sessões", year_status.get("session_count", 0))
        coverage_columns[2].metric(
            "Sessões canceladas", year_status.get("cancelled_session_count", 0)
        )
        st.metric("Sessões futuras/ao vivo ignoradas", year_status.get("pending_session_count", 0))
        for failure in year_status.get("failures", []):
            st.error(
                f"{failure.get('endpoint', 'API')} · sessão {failure.get('session_key', '—')}: "
                f"{failure.get('error', 'falha sem detalhes')}"
            )

    top = top_five_laps(laps, year, circuit, selected_session)
    if top.empty:
        st.info("Não há voltas válidas para estes filtros.")
        st.stop()

    fastest, slowest = top.iloc[0]["lap_duration"], top.iloc[-1]["lap_duration"]
    metric_columns = st.columns(3)
    metric_columns[0].metric("Melhor volta", format_lap_duration(fastest))
    metric_columns[1].metric("Voltas no ranking", len(top))
    metric_columns[2].metric("Diferença no top 5", f"+{slowest - fastest:.3f} s")
    st.subheader(f"{circuit} · {year}")

    display = top.copy()
    display.insert(0, "Posição", range(1, len(display) + 1))
    display["Tempo"] = display["lap_duration"].map(format_lap_duration)
    display = display.rename(
        columns={
            "driver_name": "Piloto",
            "driver_number": "Número",
            "lap_number": "Volta",
            "session_name": "Sessão",
            "meeting_name": "Grande Prêmio",
            "lap_duration": "Tempo (s)",
        }
    )
    st.dataframe(
        display[
            [
                "Posição",
                "Tempo",
                "Piloto",
                "Número",
                "Volta",
                "Sessão",
                "Grande Prêmio",
                "Tempo (s)",
            ]
        ],
        hide_index=True,
        width="stretch",
    )
    chart = top.copy()
    chart["Diferença (s)"] = (chart["lap_duration"] - fastest).round(3)
    chart["Piloto · volta"] = chart.apply(
        lambda row: f"{row['driver_name']} · volta {row['lap_number']}",
        axis=1,
    )
    st.subheader("Diferença para a volta mais rápida")
    st.scatter_chart(
        chart,
        x="Diferença (s)",
        y="Piloto · volta",
        color="session_type",
        x_label="Diferença para a melhor volta (s)",
        y_label="Piloto e volta",
        width="stretch",
        height=280,
        alt="Pontos de diferença de cada volta para a melhor marca do grupo",
    )


if __name__ == "__main__":
    main()
