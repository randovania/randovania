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


class BinaryWriter:
    file: BinaryIO

    def __init__(self, file: BinaryIO):
        self.file = file

    def write_byte(self, byte: int):
        self.file.write(struct.pack("!B", byte))

    def write_short(self, short: int):
        self.file.write(struct.pack("!H", short))

    def write_uint(self, uint: int):
        self.file.write(struct.pack("!I", uint))

    def write_float(self, n: float):
        self.file.write(struct.pack("!f", n))

    def write_bool(self, b: bool):
        self.file.write(struct.pack("!?", b))

    def write_string(self, s: str):
        """Writes a string encoded as UTF-8, NULL terminated"""
        self.file.write(s.encode("UTF-8"))
        self.write_byte(0)
