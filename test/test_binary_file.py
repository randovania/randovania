import io
from typing import BinaryIO

from randovania.binary_file import BinarySource, BinaryWriter


def test_read_a():
    b = io.BytesIO(b"\x05aaax\x00?\x80\x00\x00TP\x06@")  # type: BinaryIO
    source = BinarySource(b)

    assert source.read_byte() == 5
    assert source.read_string() == "aaax"
    assert source.read_float() == 1
    source.skip(1)
    assert source.read_bool()
    assert source.read_short() == 1600


def test_write():
    b = io.BytesIO()
    b_io = b  # type: BinaryIO
    writer = BinaryWriter(b_io)

    writer.write_string("foo")
    writer.write_byte(5)
    writer.write_short(1505)
    writer.write_bool(False)

    assert b.getvalue() == b"foo\x00\x05\x05\xe1\x00"
