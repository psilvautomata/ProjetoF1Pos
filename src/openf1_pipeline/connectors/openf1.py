"""Cliente HTTP para a API OpenF1."""

import logging
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from time import monotonic, sleep
from typing import Any
from urllib.parse import quote, urljoin

import requests

from openf1_pipeline.config import Settings, get_settings

logger = logging.getLogger(__name__)
OPERATORS = (">=", "<=", ">", "<", "=")
MIN_REQUEST_INTERVAL = 2.1
MAX_RATE_LIMIT_RETRIES = 1
RATE_LIMIT_RETRY_DELAY = 60.0


class OpenF1Error(Exception):
    """Erro base de comunicação ou resposta da API."""


class OpenF1TimeoutError(OpenF1Error):
    """A API não respondeu dentro do timeout configurado."""


class OpenF1HTTPError(OpenF1Error):
    """A API respondeu com status HTTP de erro."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


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
        self._last_request_at: float | None = None

    def _pace_request(self) -> None:
        """Mantém o cliente abaixo do limite gratuito de 30 requisições por minuto."""
        if self._last_request_at is not None:
            elapsed = monotonic() - self._last_request_at
            delay = MIN_REQUEST_INTERVAL - elapsed
            if delay > 0:
                sleep(delay)
        self._last_request_at = monotonic()

    @staticmethod
    def _retry_delay(response: requests.Response | None, retry_number: int) -> float:
        """Lê Retry-After (segundos ou data HTTP) ou usa espera exponencial segura."""
        retry_after = response.headers.get("Retry-After") if response is not None else None
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                try:
                    retry_at = parsedate_to_datetime(retry_after)
                except (TypeError, ValueError, OverflowError):
                    pass
                else:
                    if retry_at.tzinfo is None:
                        retry_at = retry_at.replace(tzinfo=UTC)
                    return max(0.0, (retry_at - datetime.now(UTC)).total_seconds())
        return RATE_LIMIT_RETRY_DELAY * (2**retry_number)

    def get(self, endpoint: str, filters: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        """Consulta um endpoint e devolve uma lista de registros JSON."""
        endpoint = endpoint.strip("/")
        if not re.fullmatch(r"[a-z_]+", endpoint):
            raise ValueError("Endpoint inválido")
        url = urljoin(self.settings.base_url, endpoint)
        query = _query_string(filters)
        if query:
            url = f"{url}?{query}"
        for retry_number in range(MAX_RATE_LIMIT_RETRIES + 1):
            self._pace_request()
            try:
                response = requests.get(url, timeout=self.settings.timeout)
                response.raise_for_status()
            except requests.Timeout as exc:
                logger.warning("Timeout consultando %s", endpoint)
                raise OpenF1TimeoutError(f"Timeout consultando /{endpoint}") from exc
            except requests.HTTPError as exc:
                status_code = exc.response.status_code if exc.response is not None else None
                if status_code == 429 and retry_number < MAX_RATE_LIMIT_RETRIES:
                    delay = self._retry_delay(exc.response, retry_number)
                    logger.warning(
                        "Limite da OpenF1 atingido em /%s; nova tentativa em %.1f s",
                        endpoint,
                        delay,
                    )
                    sleep(delay)
                    continue
                logger.warning("Erro HTTP consultando %s (status %s)", endpoint, status_code)
                raise OpenF1HTTPError(
                    f"Erro HTTP consultando /{endpoint} (status {status_code})", status_code
                ) from exc
            except requests.RequestException as exc:
                logger.warning("Falha de rede consultando %s: %s", endpoint, exc)
                raise OpenF1Error(f"Falha consultando /{endpoint}: {exc}") from exc
            break
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
