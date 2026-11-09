"""Relacionamento de voltas e ranking dos cinco melhores tempos."""

import math
from typing import Any

import pandas as pd

RANKING_COLUMNS = (
    "year",
    "circuit_short_name",
    "meeting_key",
    "meeting_name",
    "session_key",
    "session_name",
    "session_type",
    "driver_number",
    "driver_name",
    "lap_number",
    "lap_duration",
)
SORT_COLUMNS = (
    "lap_duration",
    "meeting_key",
    "session_key",
    "driver_number",
    "lap_number",
)


def _is_pit_out(value: Any) -> bool:
    return value is True or (isinstance(value, str) and value.strip().lower() == "true")


def _driver_name(driver: dict[str, Any] | None, driver_number: Any) -> str:
    if driver:
        name = driver.get("full_name") or driver.get("broadcast_name")
        if name:
            return str(name)
        parts = [str(driver.get(field, "")).strip() for field in ("first_name", "last_name")]
        if any(parts):
            return " ".join(part for part in parts if part)
        if driver.get("name_acronym"):
            return str(driver["name_acronym"])
    return f"Piloto {driver_number}" if driver_number is not None else "Piloto desconhecido"


def build_lap_dataset(
    laps: list[dict[str, Any]],
    meetings: list[dict[str, Any]],
    sessions: list[dict[str, Any]],
    drivers: list[dict[str, Any]],
) -> pd.DataFrame:
    """Junta respostas OpenF1 e mantém apenas voltas elegíveis ao ranking."""
    meetings_by_key = {str(row.get("meeting_key")): row for row in meetings}
    sessions_by_key = {str(row.get("session_key")): row for row in sessions}
    drivers_by_key = {
        (str(row.get("session_key")), str(row.get("driver_number"))): row for row in drivers
    }
    rows: list[dict[str, Any]] = []

    for lap in laps:
        session_key = lap.get("session_key")
        session = sessions_by_key.get(str(session_key))
        meeting_key = (session or {}).get("meeting_key", lap.get("meeting_key"))
        meeting = meetings_by_key.get(str(meeting_key))
        if session is None or meeting is None or _is_pit_out(lap.get("is_pit_out_lap")):
            continue
        try:
            duration = float(lap.get("lap_duration"))
        except (TypeError, ValueError):
            continue
        if duration <= 0 or not math.isfinite(duration):
            continue
        driver_number = lap.get("driver_number")
        driver = drivers_by_key.get((str(session_key), str(driver_number)))
        rows.append(
            {
                "year": meeting.get("year", session.get("year")),
                "circuit_short_name": meeting.get(
                    "circuit_short_name", session.get("circuit_short_name")
                ),
                "meeting_key": meeting_key,
                "meeting_name": meeting.get("meeting_name"),
                "session_key": session_key,
                "session_name": session.get("session_name"),
                "session_type": session.get("session_type"),
                "driver_number": driver_number,
                "driver_name": _driver_name(driver, driver_number),
                "lap_number": lap.get("lap_number"),
                "lap_duration": duration,
            }
        )

    frame = pd.DataFrame.from_records(rows, columns=RANKING_COLUMNS)
    if frame.empty:
        return frame
    frame = frame.drop_duplicates().sort_values(
        by=["year", "circuit_short_name", *SORT_COLUMNS],
        kind="mergesort",
        na_position="last",
    )
    return frame.reset_index(drop=True)


def top_five_laps(
    laps: pd.DataFrame,
    year: int,
    circuit_short_name: str,
    session_type: str | None = None,
) -> pd.DataFrame:
    """Retorna até cinco voltas ordenadas de forma estável para pista/ano."""
    if laps.empty:
        return laps.copy()
    selected = laps.loc[
        (pd.to_numeric(laps["year"], errors="coerce") == year)
        & (laps["circuit_short_name"] == circuit_short_name)
    ]
    if session_type and session_type != "Todos":
        selected = selected.loc[selected["session_type"] == session_type]
    return (
        selected.sort_values(by=list(SORT_COLUMNS), kind="mergesort", na_position="last")
        .head(5)
        .reset_index(drop=True)
    )


def format_lap_duration(seconds: float) -> str:
    """Formata segundos decimais como minutos, segundos e milissegundos."""
    minutes, remaining_milliseconds = divmod(round(seconds * 1000), 60_000)
    whole_seconds, milliseconds = divmod(remaining_milliseconds, 1000)
    return f"{minutes}:{whole_seconds:02d}.{milliseconds:03d}"
