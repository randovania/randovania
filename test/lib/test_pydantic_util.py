import pydantic
import pytest

import randovania

try:
    from randovania.lib import pydantic_util
except ImportError:
    # This will fail in executables, so leaving it explicitly broken!
    pass


class CustomModelForTests(pydantic.BaseModel):
    a: int
    b: str | None
    c: int = 10
    d: dict[str, int]


@pytest.mark.xfail(randovania.is_frozen(), reason="pydantic_util is excluded")
def test_encode_small():
    source = CustomModelForTests(a=0, b=None, d={"foo": 1})
    encoded = pydantic_util.encode_model(source)
    assert encoded == b'RDVM\x032(\xb5/\xfd )I\x01\x00("{\\"a\\":0,\\"b\\":null,\\"d\\":{\\"foo\\":1}}"'

    assert pydantic_util.decode_model(encoded, CustomModelForTests) == source


@pytest.mark.xfail(randovania.is_frozen(), reason="pydantic_util is excluded")
def test_encode_big():
    source = CustomModelForTests(a=35000, b="bar" * 50, d={"foo": 1234})
    encoded = pydantic_util.encode_model(source)
    assert encoded == (
        b'RDVM\x03E(\xb5/\xfd \xc7\xe5\x01\x00D\x03\xc5\x01"{\\"a\\":35000,\\"b\\":\\'
        b'"bar\\",\\"d\\":{\\"foo\\":1234}}"\x01\x00C\xa4\xdc\x18'
    )
    assert pydantic_util.decode_model(encoded, CustomModelForTests) == source
