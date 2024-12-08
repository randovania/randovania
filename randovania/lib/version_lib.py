from distutils.version import StrictVersion

import randovania

Version = StrictVersion


def parse_string(version_name: str) -> Version:
    version_name = version_name.replace("-dirty", "")
    try:
        return StrictVersion(version_name)
    except ValueError:
        if ".dev" not in version_name:
            raise
        return StrictVersion(version_name.split(".dev")[0])


def current_version() -> Version:
    return parse_string(randovania.VERSION)


__all__ = ["Version", "parse_string"]
