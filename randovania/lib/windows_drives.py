import platform
import string
from collections.abc import Iterator
from pathlib import Path


def get_windows_drives() -> Iterator[tuple[str, str, Path]]:
    try:
        from ctypes import windll
    except ImportError:
        if platform.system() == "Windows":
            raise
        else:
            yield from []
            return

    drive_types = [
        "Not identified",
        "Not Mounted",
        "Removable",
        "HDD",
        "Network",
        "CD-Rom",
        "Ramdisk",
    ]

    drives = []
    bitmask = windll.kernel32.GetLogicalDrives()
    for letter in string.ascii_uppercase:
        if bitmask & 1:
            drives.append(letter)
        bitmask >>= 1

    for drive in drives:
        path = Path(f"{drive}:/")
        type_index = windll.kernel32.GetDriveTypeW(str(path))
        yield drive, drive_types[type_index], path
