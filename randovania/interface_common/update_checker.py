from distutils.version import StrictVersion
from typing import NamedTuple

from randovania import VERSION


class VersionDescription(NamedTuple):
    tag_name: str
    change_log: str
    html_url: str

    @property
    def as_strict_version(self) -> StrictVersion:
        return StrictVersion(self.tag_name[1:])


def strict_version_for_version_string(version_name: str) -> StrictVersion:
    try:
        return StrictVersion(version_name)
    except ValueError:
        if ".dev" not in version_name:
            raise
        return StrictVersion(version_name.split(".dev")[0])


def strict_current_version() -> StrictVersion:
    return strict_version_for_version_string(VERSION)


def get_version_for_release(release: dict) -> VersionDescription:
    return VersionDescription(release["tag_name"], release["body"], release["html_url"])


MAJOR_ENTRY = "- **Major** "


def _get_major_entries(log: str) -> str:
    result = []
    last_added_header = None
    current_found_header = None

    def finish_entry():
        pass

    for s in log.split("\n"):
        if s.startswith(MAJOR_ENTRY):
            if current_found_header != last_added_header:
                result.append(current_found_header)
                last_added_header = current_found_header

            result.append(s.replace(MAJOR_ENTRY, "", 1))

        elif s.startswith("#"):
            finish_entry()
            if s.startswith("### "):
                current_found_header = s

    return "\n".join(result)


def versions_to_display_for_releases(current_version: StrictVersion,
                                     last_changelog_version: StrictVersion,
                                     releases: list[dict],
                                     ) -> tuple[dict[str, str], list[str], VersionDescription | None]:
    all_change_logs = {}
    new_change_logs = []
    displayed_new_version = False
    version_to_display = None

    for release in releases:
        version = get_version_for_release(release)
        strict_version = version.as_strict_version

        if strict_version > current_version:
            if not displayed_new_version:
                version_to_display = version
                displayed_new_version = True

        else:
            log = f"## {version.tag_name}\n\n{version.change_log}"
            all_change_logs[version.tag_name] = log

            if strict_version > last_changelog_version:
                if MAJOR_ENTRY in log:
                    log = "## {} - Major Changes\n---\n\n{}\n\n---\nFor more details, check the Change Log tab.".format(
                        version.tag_name,
                        _get_major_entries(log),
                    )
                new_change_logs.append(log)

    return all_change_logs, new_change_logs, version_to_display
