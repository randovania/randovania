from distutils.version import StrictVersion
from typing import NamedTuple, List, Tuple, Optional

from randovania import VERSION


class VersionDescription(NamedTuple):
    tag_name: str
    change_log: str
    html_url: str

    @property
    def as_strict_version(self) -> StrictVersion:
        return StrictVersion(self.tag_name[1:])


def strict_current_version() -> StrictVersion:
    return StrictVersion(VERSION)


def get_version_for_release(release: dict) -> VersionDescription:
    return VersionDescription(release["tag_name"], release["body"], release["html_url"])


def versions_to_display_for_releases(current_version: StrictVersion,
                                     last_changelog_version: StrictVersion,
                                     releases: List[dict],
                                     ) -> Tuple[List[str], Optional[VersionDescription]]:
    change_logs = []
    displayed_new_version = False
    version_to_display = None

    for release in releases:
        version = get_version_for_release(release)
        strict_version = version.as_strict_version

        if strict_version > current_version:
            if not displayed_new_version:
                version_to_display = version
                displayed_new_version = True

        elif strict_version > last_changelog_version:
            change_logs.append("## {}\n\n{}".format(version.tag_name, version.change_log))

    return change_logs, version_to_display
