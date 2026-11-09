"""Transformações determinísticas para tabelas da OpenF1."""

import json
import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)
DATE_FIELDS = frozenset({"date", "date_start", "date_end"})
INTEGER_FIELDS = frozenset(
    {
        "meeting_key",
        "session_key",
        "driver_number",
        "lap_number",
        "lap_start",
        "lap_end",
        "position",
        "stint_number",
        "tyre_age_at_start",
        "rainfall",
    }
)
FLOAT_FIELDS = frozenset(
    {
        "speed",
        "duration",
        "lane_duration",
        "stop_duration",
        "lap_duration",
        "total_duration",
        "duration_sector_1",
        "duration_sector_2",
        "duration_sector_3",
        "i1_speed",
        "i2_speed",
        "st_speed",
        "air_temperature",
        "track_temperature",
        "humidity",
        "pressure",
        "wind_speed",
        "wind_direction",
    }
)
VALUE_RANGES = (("speed", 0, 400), ("humidity", 0, 100), ("position", 1, 30))


def normalize_records(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Normaliza datas, tipos conhecidos e duplicatas sem alterar a entrada."""
    unique_records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in records:
        signature = json.dumps(record, sort_keys=True, ensure_ascii=False, default=str)
        if signature not in seen:
            seen.add(signature)
            unique_records.append(record)
    if len(unique_records) != len(records):
        logger.info("Removidas %d linhas duplicadas", len(records) - len(unique_records))
    frame = pd.DataFrame.from_records(unique_records)
    if frame.empty:
        return frame
    for field in DATE_FIELDS.intersection(frame.columns):
        parsed = pd.to_datetime(frame[field], errors="coerce", utc=True, format="mixed")
        frame[field] = parsed.map(lambda value: value.isoformat() if pd.notna(value) else None)
    for field in INTEGER_FIELDS.intersection(frame.columns):
        frame[field] = pd.to_numeric(frame[field], errors="coerce").astype("Int64")
    for field in FLOAT_FIELDS.intersection(frame.columns):
        frame[field] = pd.to_numeric(frame[field], errors="coerce")
    return frame.reset_index(drop=True)


def validate_records(
    records: list[dict[str, Any]], required_fields: tuple[str, ...] = ()
) -> list[str]:
    """Devolve problemas de qualidade sem impedir endpoints com dados parciais."""
    issues: list[str] = []
    for index, record in enumerate(records):
        missing = [field for field in required_fields if record.get(field) is None]
        if missing:
            issues.append(f"registro {index}: campos obrigatórios ausentes: {', '.join(missing)}")
        for field, minimum, maximum in VALUE_RANGES:
            value = record.get(field)
            if value is None:
                continue
            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                issues.append(f"registro {index}: {field} não é numérico")
                continue
            if not minimum <= numeric_value <= maximum:
                issues.append(f"registro {index}: {field} fora da faixa [{minimum}, {maximum}]")
    if issues:
        logger.warning("Validação encontrou %d problema(s)", len(issues))
    return issues
