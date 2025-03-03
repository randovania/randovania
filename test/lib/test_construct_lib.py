import construct
import pytest
from construct import Construct, CString, Default, Int32ul, Struct

from randovania.lib.construct_lib import DefaultsAdapter


@pytest.mark.parametrize("subcon", [Int32ul, CString])
def test_defaults_adapter_bad_subcon(subcon: Construct):
    with pytest.raises(TypeError, match=f"subcon should be a Struct; got {type(subcon)}"):
        DefaultsAdapter(subcon)


@pytest.fixture
def defaults_adapter() -> DefaultsAdapter:
    return DefaultsAdapter(
        Struct(
            foo=Int32ul,
            bar=Default(Int32ul, 2403),
        )
    )


DEFAULTS_ADAPTER_DATA = [
    ({"foo": 0, "bar": 0}, {"foo": 0, "bar": 0}),
    ({"foo": 2403, "bar": 2403}, {"foo": 2403}),
]


@pytest.mark.parametrize(("data_encoded", "data_decoded"), DEFAULTS_ADAPTER_DATA)
def test_defaults_adapter_encode(data_encoded: dict, data_decoded: dict, defaults_adapter):
    encoded = defaults_adapter._encode(data_decoded, construct.Container(), "")
    assert encoded == data_encoded


@pytest.mark.parametrize(("data_encoded", "data_decoded"), DEFAULTS_ADAPTER_DATA)
def test_defaults_adapter_decode(data_encoded: dict, data_decoded: dict, defaults_adapter):
    decoded = defaults_adapter._decode(data_encoded, construct.Container(), "")
    assert decoded == data_decoded
