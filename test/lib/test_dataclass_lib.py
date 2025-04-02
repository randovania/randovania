import dataclasses

import pytest

from randovania.lib.dataclass_lib import get_field


@dataclasses.dataclass
class DummyDataclass:
    field: bool = dataclasses.field(default=True, metadata={"foo": "bar"})


@pytest.mark.parametrize("dataclass", [DummyDataclass, DummyDataclass()])
def test_get_field(dataclass):
    # extant field
    assert get_field(dataclass, "field").metadata["foo"] == "bar"

    # non-existent field
    with pytest.raises(AttributeError, match="DummyDataclass has no field 'fake_field'"):
        get_field(dataclass, "fake_field")
