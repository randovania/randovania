import pytest

from randovania.lib import version_lib


@pytest.mark.parametrize(
    ("expected", "raw"),
    [
        (version_lib.Version("1.1"), "1.1.0-dirty"),
        (version_lib.Version("1.1"), "1.1.0"),
        (version_lib.Version("1.1.1"), "1.1.1.dev50"),
    ],
)
def test_parse_string(expected: version_lib.Version, raw: str) -> None:
    assert version_lib.parse_string(raw) == expected
