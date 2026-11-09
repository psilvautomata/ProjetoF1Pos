from unittest.mock import Mock, patch

import pytest
import requests

from openf1_pipeline.connectors.openf1 import (
    OpenF1Client,
    OpenF1HTTPError,
    OpenF1ResponseError,
    OpenF1TimeoutError,
    _query_string,
)


def test_query_supports_comparison_operators():
    assert _query_string({"speed>=": 315, "date<": "2024-01-01T00:00:00+00:00"}) == (
        "speed>=315&date<2024-01-01T00:00:00%2B00:00"
    )


@patch("openf1_pipeline.connectors.openf1.requests.get")
def test_get_returns_empty_list(mock_get, settings):
    response = Mock()
    response.json.return_value = []
    mock_get.return_value = response
    assert OpenF1Client(settings).get("drivers", {"session_key": "latest"}) == []
    response.raise_for_status.assert_called_once()
    mock_get.assert_called_once_with(
        "https://api.openf1.org/v1/drivers?session_key=latest", timeout=settings.timeout
    )


@patch("openf1_pipeline.connectors.openf1.requests.get", side_effect=requests.Timeout)
def test_get_raises_timeout(mock_get, settings):
    with pytest.raises(OpenF1TimeoutError):
        OpenF1Client(settings).get("laps")


@patch("openf1_pipeline.connectors.openf1.requests.get")
def test_get_raises_http_error(mock_get, settings):
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError("404")
    mock_get.return_value = response
    with pytest.raises(OpenF1HTTPError):
        OpenF1Client(settings).get("laps")


@patch("openf1_pipeline.connectors.openf1.requests.get")
def test_get_rejects_invalid_json(mock_get, settings):
    response = Mock()
    response.json.side_effect = ValueError("invalid")
    mock_get.return_value = response
    with pytest.raises(OpenF1ResponseError):
        OpenF1Client(settings).get("laps")


def test_endpoint_path_is_validated(settings):
    with pytest.raises(ValueError):
        OpenF1Client(settings).get("../secrets")
    with pytest.raises(ValueError):
        OpenF1Client(settings).get("laps?csv=true")
