import copy
from distutils.version import StrictVersion

import pytest

from randovania.interface_common import update_checker
from randovania.interface_common.update_checker import VersionDescription

_CUSTOM_CHANGE_LOGS = {
    4: "\n- *Major* - Foo\n",
    5: "\n- *Major* - Foo\n- Something\n",
    6: "\n- Bar\n",
}
_CUSTOM_EXPECTED_LOG = copy.copy(_CUSTOM_CHANGE_LOGS)
_CUSTOM_EXPECTED_LOG[5] = "\n- *Major* - Foo\n\n---\nFor more details, check the Change Log tab."


@pytest.mark.parametrize(["current_version", "last_changelog_version", "expected_display"], [
    (5, 5, 10),
    (5, 4, 10),
    (5, 3, 10),
    (10, 3, None),

])
def test_versions_to_display_for_releases(current_version, last_changelog_version, expected_display,
                                          ):
    # Setup
    releases = [
        {"tag_name": "v0.{}.0".format(i),
         "body": "Changelog v0.{}.0{}".format(i, _CUSTOM_CHANGE_LOGS.get(i, "")),
         "html_url": "url"}
        for i in reversed(range(1, 11))
    ]

    # Run
    all_change_logs, change_logs, version_to_display = update_checker.versions_to_display_for_releases(
        StrictVersion("0.{}.0".format(current_version)),
        StrictVersion("0.{}.0".format(last_changelog_version)),
        releases)

    # Assert
    if expected_display is None:
        assert version_to_display is None
    else:
        assert version_to_display == VersionDescription("v0.{}.0".format(expected_display),
                                                        "Changelog v0.{}.0".format(expected_display),
                                                        "url")
    assert change_logs == [
        "## v0.{0}.0\n\nChangelog v0.{0}.0{1}".format(i, _CUSTOM_EXPECTED_LOG.get(i, ""))
        for i in reversed(range(last_changelog_version + 1, current_version + 1))
    ]
    assert all_change_logs == [
        "## v0.{0}.0\n\nChangelog v0.{0}.0{1}".format(i, _CUSTOM_CHANGE_LOGS.get(i, ""))
        for i in reversed(range(1, current_version + 1))
    ]
