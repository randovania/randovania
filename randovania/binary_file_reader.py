import struct
from typing import BinaryIO


class BinarySource:
    file: BinaryIO

    def __init__(self, file: BinaryIO):
        self.file = file

    def read_byte(self) -> int:
        return struct.unpack("!B", self.file.read(1))[0]

    def read_short(self) -> int:
        return struct.unpack("!H", self.file.read(2))[0]

    def read_uint(self) -> int:
        return struct.unpack("!I", self.file.read(4))[0]

    def read_float(self) -> float:
        return struct.unpack("!f", self.file.read(4))[0]

    def read_bool(self) -> bool:
        return struct.unpack("!?", self.file.read(1))[0]

    def read_string(self) -> str:
        """Reads a null terminated UTF-8 string"""
        chars = []
        while True:
            c = self.file.read(1)
            if c[0] == 0:
                return b"".join(chars).decode("UTF-8")
            chars.append(c)

    def skip(self, n: int):
        """Skips n bytes"""
        self.file.read(n)
