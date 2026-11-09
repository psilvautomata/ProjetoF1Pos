"""Cliente HTTP para a API OpenF1."""

import logging
import re
from collections.abc import Mapping
from typing import Any
from urllib.parse import quote, urljoin

import requests

from openf1_pipeline.config import Settings, get_settings

logger = logging.getLogger(__name__)
OPERATORS = (">=", "<=", ">", "<", "=")


class OpenF1Error(Exception):
    """Erro base de comunicação ou resposta da API."""


class OpenF1TimeoutError(OpenF1Error):
    """A API não respondeu dentro do timeout configurado."""


class OpenF1HTTPError(OpenF1Error):
    """A API respondeu com status HTTP de erro."""


class OpenF1ResponseError(OpenF1Error):
    """A API devolveu JSON inválido ou formato inesperado."""


def _query_string(filters: Mapping[str, Any] | None) -> str:
    """Monta filtros preservando os operadores aceitos pela API."""
    pairs: list[str] = []
    for raw_key, value in (filters or {}).items():
        operator = "="
        field = raw_key
        for candidate in OPERATORS:
            if raw_key.endswith(candidate) and len(raw_key) > len(candidate):
                field, operator = raw_key[: -len(candidate)], candidate
                break
        if isinstance(value, tuple) and len(value) == 2:
            operator, value = value
        if operator not in OPERATORS or not field or value is None:
            raise ValueError(f"Filtro inválido: {raw_key!r}")
        encoded = quote(str(value), safe=":._~")
        pairs.append(f"{quote(field, safe='_')}" + operator + encoded)
    return "&".join(pairs)


class OpenF1Client:
    """Cliente reutilizável para requisições GET à API OpenF1."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def get(self, endpoint: str, filters: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        """Consulta um endpoint e devolve uma lista de registros JSON."""
        endpoint = endpoint.strip("/")
        if not re.fullmatch(r"[a-z_]+", endpoint):
            raise ValueError("Endpoint inválido")
        url = urljoin(self.settings.base_url, endpoint)
        query = _query_string(filters)
        if query:
            url = f"{url}?{query}"
        try:
            response = requests.get(url, timeout=self.settings.timeout)
            response.raise_for_status()
        except requests.Timeout as exc:
            logger.warning("Timeout consultando %s", endpoint)
            raise OpenF1TimeoutError(f"Timeout consultando /{endpoint}") from exc
        except requests.HTTPError as exc:
            logger.warning("Erro HTTP consultando %s: %s", endpoint, exc)
            raise OpenF1HTTPError(f"Erro HTTP consultando /{endpoint}: {exc}") from exc
        except requests.RequestException as exc:
            logger.warning("Falha de rede consultando %s: %s", endpoint, exc)
            raise OpenF1Error(f"Falha consultando /{endpoint}: {exc}") from exc
        try:
            data = response.json()
        except ValueError as exc:
            raise OpenF1ResponseError(f"JSON inválido em /{endpoint}") from exc
        if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
            raise OpenF1ResponseError(
                f"Formato inesperado em /{endpoint}; esperada lista de objetos"
            )
        logger.info("OpenF1 /%s: %d registros", endpoint, len(data))
        return data
