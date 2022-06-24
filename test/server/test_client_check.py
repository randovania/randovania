import pytest

from randovania.server import client_check


@pytest.fixture(name="expected_headers")
def _expected_headers():
    return {
        "X-Randovania-API-Version": "2",
        "X-Randovania-Preset-Version": "13",
        "X-Randovania-Permalink-Version": "4",
        "X-Randovania-Description-Version": "2",
    }


def test_check_client_headers_valid(expected_headers):
    result = client_check.check_client_headers(
        expected_headers,
        {
            "HTTP_X_RANDOVANIA_API_VERSION": "2",
            "HTTP_X_RANDOVANIA_PRESET_VERSION": "13",
            "HTTP_X_RANDOVANIA_PERMALINK_VERSION": "4",
            "HTTP_X_RANDOVANIA_DESCRIPTION_VERSION": "2",
        }
    )
    assert result is None


def test_check_client_headers_missing(expected_headers):
    result = client_check.check_client_headers(
        expected_headers,
        {
            "HTTP_X_RANDOVANIA_API_VERSION": "2",
            "HTTP_X_RANDOVANIA_PRESET_VERSION": "13",
            "HTTP_X_RANDOVANIA_PERMALINK_VERSION": "4",
        }
    )
    assert result is not None


def test_check_client_headers_wrong_value(expected_headers):
    result = client_check.check_client_headers(
        expected_headers,
        {
            "HTTP_X_RANDOVANIA_API_VERSION": "2",
            "HTTP_X_RANDOVANIA_PRESET_VERSION": "10",
            "HTTP_X_RANDOVANIA_PERMALINK_VERSION": "7",
            "HTTP_X_RANDOVANIA_DESCRIPTION_VERSION": "2",
        }
    )
    assert result is not None


@pytest.mark.parametrize(["mode", "client_version", "server_version", "expected"], [
    (client_check.ClientVersionCheck.STRICT, "1.0", "1.0", True),
    (client_check.ClientVersionCheck.STRICT, "1.0", "1.0.1", False),
    (client_check.ClientVersionCheck.STRICT, "1.0", "1.1", False),
    (client_check.ClientVersionCheck.MATCH_MAJOR_MINOR, "1.0", "1.0", True),
    (client_check.ClientVersionCheck.MATCH_MAJOR_MINOR, "1.0", "1.0.1", True),
    (client_check.ClientVersionCheck.MATCH_MAJOR_MINOR, "1.0", "1.1", False),
    (client_check.ClientVersionCheck.IGNORE, "1.0", "1.0", True),
    (client_check.ClientVersionCheck.IGNORE, "1.0", "1.0.1", True),
    (client_check.ClientVersionCheck.IGNORE, "1.0", "1.1", True),
])
def test_check_client_version(mode, client_version, server_version, expected):
    result = client_check.check_client_version(mode, client_version, server_version)

    if expected:
        assert result is None
    else:
        assert result is not None
