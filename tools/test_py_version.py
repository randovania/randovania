from __future__ import annotations

import struct
import sys

REQUIRED_VERSION_MAJOR = 3
REQUIRED_VERSION_MINOR = 11
REQUIRED_WORD_SIZE_BITS = 64

_REQUIRED_VERSION = (REQUIRED_VERSION_MAJOR, REQUIRED_VERSION_MINOR, REQUIRED_WORD_SIZE_BITS)
_REQUIRED_VERSIONS = [_REQUIRED_VERSION, (3, 10, REQUIRED_WORD_SIZE_BITS)]


def version_str(major, minor, bits):
    version = "Python %d.%d (%d-bit)" % (major, minor, bits)
    return version


major = sys.version_info.major
minor = sys.version_info.minor
bits = struct.calcsize("P") * 8

expected_ver = version_str(*_REQUIRED_VERSION)
actual_ver = version_str(major, minor, bits)

if (major, minor, bits) not in _REQUIRED_VERSIONS:
    error_msg = f"Default python installation must be {expected_ver}; Found {actual_ver}"
    raise Exception(error_msg)

print("Using " + actual_ver)
