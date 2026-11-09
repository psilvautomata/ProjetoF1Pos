"""Pipelines idempotentes de ingestão por evento e sessão."""

import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from openf1_pipeline.config import Settings, get_settings
from openf1_pipeline.connectors import OpenF1Client
from openf1_pipeline.connectors.openf1 import OpenF1Error, OpenF1HTTPError
from openf1_pipeline.services import RANKING_COLUMNS, build_lap_dataset
from openf1_pipeline.transformations import normalize_records, validate_records

logger = logging.getLogger(__name__)
ESSENTIAL_ENDPOINTS = ("drivers", "session_result", "starting_grid")
PERFORMANCE_ENDPOINTS = ("laps", "stints", "pit", "weather", "position", "race_control")


def _scope(kind: str, identifier: int | str) -> str:
    """Valida identificadores antes de usá-los em caminhos de saída."""
    value = str(identifier)
    if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ValueError(f"Identificador inválido: {identifier!r}")
    return f"{kind}_{value}"


def _session_has_ended(session: dict[str, Any]) -> bool:
    """Confirma que uma sessão terminou para limitar a ingestão ao histórico gratuito."""
    end_value = session.get("date_end")
    if not isinstance(end_value, str) or not end_value.strip():
        return False
    try:
        end_time = datetime.fromisoformat(end_value.replace("Z", "+00:00"))
    except ValueError:
        return False
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=UTC)
    return end_time <= datetime.now(UTC)


class IngestionPipeline:
    """Baixa dados históricos e grava cópias brutas e tratadas."""

    def __init__(
        self, client: OpenF1Client | None = None, settings: Settings | None = None
    ) -> None:
        self.settings = settings or get_settings()
        self.client = client or OpenF1Client(self.settings)

    def ingest_meeting(self, meeting_key: int | str) -> dict[str, Any]:
        """Ingere o meeting, suas sessões e as tabelas associadas."""
        meeting_scope = _scope("meeting", meeting_key)
        meetings = self._fetch("meetings", {"meeting_key": meeting_key}, meeting_scope)
        if not meetings:
            raise ValueError(f"Nenhum meeting encontrado para meeting_key={meeting_key}")
        sessions = self._fetch("sessions", {"meeting_key": meeting_key}, meeting_scope)
        summaries = []
        for session in sessions:
            key = session.get("session_key")
            if key is not None:
                summaries.append(self.ingest_session(key, session=session))
        return {"meeting_key": meeting_key, "sessions": summaries}

    def ingest_session(
        self, session_key: int | str, session: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Ingere endpoints essenciais e de desempenho de uma sessão."""
        session_scope = _scope("session", session_key)
        metadata = session
        if metadata is None:
            rows = self._fetch("sessions", {"session_key": session_key}, session_scope)
            metadata = rows[0] if rows else {}
        session_type = str(
            metadata.get("session_type") or metadata.get("session_name") or ""
        ).lower()
        endpoints = list(ESSENTIAL_ENDPOINTS + PERFORMANCE_ENDPOINTS)
        if "race" in session_type:
            endpoints.append("intervals")
        outputs: dict[str, int] = {}
        for endpoint in endpoints:
            rows = self._fetch(endpoint, {"session_key": session_key}, session_scope)
            outputs[endpoint] = len(rows)
        return {"session_key": session_key, "records": outputs}

    def ingest_year(self, year: int) -> dict[str, Any]:
        """Ingere meetings/sessões de um ano e atualiza a base do dashboard."""
        if year < 2023:
            raise ValueError(
                "A API OpenF1 disponibiliza dados históricos gratuitos a partir de 2023"
            )
        meetings = self._fetch_or_load("meetings", {"year": year}, _scope("year", year))
        sessions: list[dict[str, Any]] = []
        laps: list[dict[str, Any]] = []
        drivers: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []
        session_status: list[dict[str, Any]] = []
        cancelled_count = 0
        pending_count = 0
        rate_limit_blocked = False

        for meeting in meetings:
            meeting_key = meeting.get("meeting_key")
            if meeting_key is None:
                failures.append(
                    {"meeting_key": None, "endpoint": "sessions", "error": "meeting_key ausente"}
                )
                continue
            try:
                meeting_sessions = self._fetch_or_load(
                    "sessions", {"meeting_key": meeting_key}, _scope("meeting", meeting_key)
                )
            except OpenF1Error as exc:
                failure = {"meeting_key": meeting_key, "endpoint": "sessions", "error": str(exc)}
                if isinstance(exc, OpenF1HTTPError):
                    failure["status_code"] = exc.status_code
                failures.append(failure)
                if isinstance(exc, OpenF1HTTPError) and exc.status_code == 429:
                    rate_limit_blocked = True
                    break
                continue

            for session in meeting_sessions:
                session_key = session.get("session_key")
                if session_key is None:
                    failures.append(
                        {
                            "meeting_key": meeting_key,
                            "endpoint": "sessions",
                            "error": "session_key ausente",
                        }
                    )
                    continue
                if session.get("is_cancelled") is True:
                    cancelled_count += 1
                    session_status.append(
                        {"session_key": session_key, "status": "cancelled", "endpoints": {}}
                    )
                    continue
                if not _session_has_ended(session):
                    pending_count += 1
                    session_status.append(
                        {
                            "session_key": session_key,
                            "session_name": session.get("session_name"),
                            "status": "pending",
                            "endpoints": {},
                        }
                    )
                    continue

                sessions.append(session)
                endpoint_status: dict[str, str] = {}
                for endpoint in ("drivers", "laps"):
                    try:
                        records = self._fetch_or_load(
                            endpoint,
                            {"session_key": session_key},
                            _scope("session", session_key),
                        )
                    except OpenF1Error as exc:
                        endpoint_status[endpoint] = "failed"
                        failure = {
                            "meeting_key": meeting_key,
                            "session_key": session_key,
                            "endpoint": endpoint,
                            "error": str(exc),
                        }
                        if isinstance(exc, OpenF1HTTPError):
                            failure["status_code"] = exc.status_code
                        failures.append(failure)
                        if isinstance(exc, OpenF1HTTPError) and exc.status_code == 429:
                            rate_limit_blocked = True
                            break
                    else:
                        endpoint_status[endpoint] = "complete"
                        if endpoint == "drivers":
                            drivers.extend(records)
                        else:
                            laps.extend(records)
                session_status.append(
                    {
                        "session_key": session_key,
                        "session_name": session.get("session_name"),
                        "status": "partial" if "failed" in endpoint_status.values() else "complete",
                        "endpoints": endpoint_status,
                    }
                )
                if rate_limit_blocked:
                    break
            if rate_limit_blocked:
                break

        lap_dataset = build_lap_dataset(laps, meetings, sessions, drivers)
        self._merge_year_dataset(year, lap_dataset)
        status = "empty" if not meetings else "partial" if failures or pending_count else "complete"
        year_manifest = {
            "year": year,
            "status": status,
            "meeting_count": len(meetings),
            "session_count": len(sessions),
            "cancelled_session_count": cancelled_count,
            "pending_session_count": pending_count,
            "valid_lap_count": len(lap_dataset),
            "sessions": session_status,
            "failures": failures,
        }
        self._update_dashboard_manifest(year, year_manifest)
        return year_manifest

    def _merge_year_dataset(self, year: int, year_laps: pd.DataFrame) -> None:
        dashboard_dir = self.settings.data_dir / "processed" / "dashboard"
        dashboard_dir.mkdir(parents=True, exist_ok=True)
        destination = dashboard_dir / "lap_rankings.csv"
        if destination.exists():
            existing = pd.read_csv(destination)
            if "year" in existing.columns:
                existing = existing.loc[pd.to_numeric(existing["year"], errors="coerce") != year]
        else:
            existing = pd.DataFrame(columns=RANKING_COLUMNS)
        if existing.empty:
            combined = year_laps.copy()
        elif year_laps.empty:
            combined = existing.copy()
        else:
            combined = pd.concat([existing, year_laps], ignore_index=True)
        if not combined.empty:
            combined = combined.sort_values(
                by=[
                    "year",
                    "circuit_short_name",
                    "lap_duration",
                    "meeting_key",
                    "session_key",
                    "driver_number",
                    "lap_number",
                ],
                kind="mergesort",
                na_position="last",
            )
        temporary = destination.with_suffix(".csv.tmp")
        combined.to_csv(temporary, index=False, encoding="utf-8")
        temporary.replace(destination)

    def _update_dashboard_manifest(self, year: int, year_status: dict[str, Any]) -> None:
        dashboard_dir = self.settings.data_dir / "processed" / "dashboard"
        dashboard_dir.mkdir(parents=True, exist_ok=True)
        destination = dashboard_dir / "ingestion_manifest.json"
        manifest = (
            json.loads(destination.read_text(encoding="utf-8"))
            if destination.exists()
            else {"years": {}}
        )
        manifest.setdefault("years", {})[str(year)] = year_status
        temporary = destination.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
        )
        temporary.replace(destination)

    def _fetch(self, endpoint: str, filters: dict[str, Any], scope: str) -> list[dict[str, Any]]:
        rows = self.client.get(endpoint, filters)
        required = ("session_key",) if endpoint not in {"meetings", "sessions"} else ()
        validate_records(rows, required)
        self._save(endpoint, scope, rows)
        return rows

    def _fetch_or_load(
        self, endpoint: str, filters: dict[str, Any], scope: str
    ) -> list[dict[str, Any]]:
        """Reusa JSON válido já ingerido para permitir retomar uma temporada parcialmente."""
        cached_path = self.settings.data_dir / "raw" / scope / f"{endpoint}.json"
        if cached_path.exists():
            try:
                cached_rows = json.loads(cached_path.read_text(encoding="utf-8"))
                if not isinstance(cached_rows, list) or any(
                    not isinstance(row, dict) for row in cached_rows
                ):
                    raise ValueError("cache não contém uma lista de objetos")
                required = () if endpoint in {"meetings", "sessions"} else ("session_key",)
                validate_records(cached_rows, required)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                logger.warning("Cache inválido em %s; consultando a API: %s", cached_path, exc)
            else:
                logger.info("Reutilizando %s registros de %s", len(cached_rows), cached_path)
                return cached_rows
        return self._fetch(endpoint, filters, scope)

    def _save(self, endpoint: str, scope: str, rows: list[dict[str, Any]]) -> None:
        raw_dir = self.settings.data_dir / "raw" / scope
        processed_dir = self.settings.data_dir / "processed" / scope
        raw_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)
        raw_path = raw_dir / f"{endpoint}.json"
        raw_tmp = raw_path.with_suffix(".json.tmp")
        raw_tmp.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        raw_tmp.replace(raw_path)
        frame = normalize_records(rows)
        csv_path = processed_dir / f"{endpoint}.csv"
        csv_tmp = csv_path.with_suffix(".csv.tmp")
        frame.to_csv(csv_tmp, index=False, encoding="utf-8")
        csv_tmp.replace(csv_path)
        logger.info("Gravados %s registros em %s", len(rows), Path(csv_path))
