from openf1_pipeline.config.settings import get_settings


def test_loads_environment_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENF1_BASE_URL", "https://example.test/api")
    monkeypatch.setenv("OPENF1_TIMEOUT", "12")
    monkeypatch.setenv("OPENF1_DATA_DIR", str(tmp_path))
    settings = get_settings()
    assert settings.base_url == "https://example.test/api/"
    assert settings.timeout == 12
    assert settings.data_dir == tmp_path


def test_rejects_nonpositive_timeout(monkeypatch):
    monkeypatch.setenv("OPENF1_TIMEOUT", "0")
    try:
        get_settings()
    except ValueError as exc:
        assert "maior que zero" in str(exc)
    else:
        raise AssertionError("timeout inválido deveria falhar")
