from packaging.version import Version

import randovania


def parse_string(version_name: str) -> Version:
    version_name = version_name.replace("-dirty", "")
    version = Version(version_name)
    if version.is_devrelease:
        return Version(version.base_version)
    else:
        return version


def current_version() -> Version:
    return parse_string(randovania.VERSION)


__all__ = ["Version", "parse_string"]
