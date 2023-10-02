from __future__ import annotations

from datetime import datetime
from distutils.version import StrictVersion

import pytest

from randovania.interface_common import update_checker
from randovania.interface_common.update_checker import ChangeLogDetails, VersionDescription

_MORE_DETAILS = "\n\n---\nFor more details, check the Change Log tab."

_RAW_DATE = "2023-09-16T02:39:26Z"

_CUSTOM_CHANGE_LOGS = {
    4: "\n- **Major** - Foo\n",
    5: "\n- Bar\n### Super Game\n- **Major** - Game Stuff\n- Something\n",
    6: "\n- Bar\n",
}
_CUSTOM_EXPECTED_LOG = {
    4: "## v0.4.0 - Major Changes\n---\n\n- Foo" + _MORE_DETAILS,
    5: "## v0.5.0 - Major Changes\n---\n\n### Super Game\n- Game Stuff" + _MORE_DETAILS,
    6: "{}\n\n## v0.6.0\n\nChangelog v0.6.0\n- Bar\n",
}


@pytest.mark.parametrize(
    ("current_version", "last_changelog_version", "expected_display"),
    [
        (5, 5, 10),
        (5, 4, 10),
        (5, 3, 10),
        (10, 3, None),
    ],
)
def test_versions_to_display_for_releases(
    current_version,
    last_changelog_version,
    expected_display,
):
    # Setup
    formatted_date = datetime.strptime(_RAW_DATE, "%Y-%m-%dT%H:%M:%SZ").strftime("%x")

    _CUSTOM_EXPECTED_LOG[6] = _CUSTOM_EXPECTED_LOG[6].format(formatted_date)

    releases = [
        {
            "tag_name": f"v0.{i}.0",
            "body": "Changelog v0.{}.0{}".format(i, _CUSTOM_CHANGE_LOGS.get(i, "")),
            "html_url": "url",
            "published_at": _RAW_DATE,
        }
        for i in reversed(range(1, 11))
    ]

    # Run
    (
        all_change_logs,
        change_logs,
        version_to_display,
    ) = update_checker.versions_to_display_for_releases(
        StrictVersion(f"0.{current_version}.0"), StrictVersion(f"0.{last_changelog_version}.0"), releases
    )

    # Assert
    if expected_display is None:
        assert version_to_display is None
    else:
        change_log_details = ChangeLogDetails(f"Changelog v0.{expected_display}.0", _RAW_DATE)
        assert version_to_display == VersionDescription(f"v0.{expected_display}.0", change_log_details, "url")

    assert change_logs == [
        _CUSTOM_EXPECTED_LOG.get(i, f"{formatted_date}\n\n## v0.{i}.0\n\nChangelog v0.{i}.0")
        for i in reversed(range(last_changelog_version + 1, current_version + 1))
    ]
    assert all_change_logs == {
        f"v0.{i}.0": "{d}\n\n## v0.{v}.0\n\nChangelog v0.{v}.0{m}".format(
            v=i, m=_CUSTOM_CHANGE_LOGS.get(i, ""), d=formatted_date
        )
        for i in reversed(range(1, current_version + 1))
    }
