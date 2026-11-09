"""Carregamento de configurações via ambiente."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    """Configurações imutáveis da aplicação."""

    base_url: str = "https://api.openf1.org/v1/"
    timeout: float = 30.0
    data_dir: Path = Path("data")


def get_settings() -> Settings:
    """Lê configurações de ambiente e valida os valores numéricos."""
    defaults = Settings()
    base_url = os.getenv("OPENF1_BASE_URL", defaults.base_url).rstrip("/") + "/"
    timeout = float(os.getenv("OPENF1_TIMEOUT", str(defaults.timeout)))
    if timeout <= 0:
        raise ValueError("OPENF1_TIMEOUT deve ser maior que zero")
    data_dir = Path(os.getenv("OPENF1_DATA_DIR", "data")).expanduser()
    return Settings(base_url=base_url, timeout=timeout, data_dir=data_dir)
