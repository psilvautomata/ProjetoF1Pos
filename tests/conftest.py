"""Fixtures compartilhadas dos testes unitários."""

import pytest

from openf1_pipeline.config import Settings


@pytest.fixture
def settings(tmp_path):
    return Settings(data_dir=tmp_path)
