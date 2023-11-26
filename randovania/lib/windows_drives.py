import string
import sys
from collections.abc import Iterator
from pathlib import Path


def get_windows_drives() -> Iterator[tuple[str, str, Path]]:
    try:
        if sys.platform == "win32":
            from ctypes import windll

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
        else:
            yield from []
            return
    except ImportError:
        if sys.platform == "win32":
            raise
