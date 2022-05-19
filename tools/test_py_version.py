import sys, struct 

REQUIRED_VERSION_MAJOR = 3
REQUIRED_VERSION_MINOR = 10
REQUIRED_WORD_SIZE_BITS = 64

def version_str(major, minor, bits):
    version = "Python %d.%d (%d-bit)" % (major, minor, bits)
    return version

major = sys.version_info.major
minor = sys.version_info.minor
bits = struct.calcsize("P")*8 

expected_ver = version_str(REQUIRED_VERSION_MAJOR, REQUIRED_VERSION_MINOR, REQUIRED_WORD_SIZE_BITS)
actual_ver = version_str(major, minor, bits)

if (major, minor, bits) != (REQUIRED_VERSION_MAJOR, REQUIRED_VERSION_MINOR, REQUIRED_WORD_SIZE_BITS):
    error_msg = "Default python installation must be %s; Found %s" % (
            expected_ver,
            actual_ver,
        )
    raise Exception(error_msg)

print("Using " + actual_ver)
