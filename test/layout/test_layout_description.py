from __future__ import annotations

import contextlib
import copy
import pickle
from typing import TYPE_CHECKING

import pytest

from randovania.layout import description_migration
from randovania.layout.base.trick_level import LayoutTrickLevel
from randovania.layout.layout_description import InvalidLayoutDescription, LayoutDescription
from randovania.layout.versioned_preset import VersionedPreset

if TYPE_CHECKING:
    from conftest import TestFilesDir


@pytest.mark.parametrize("value", LayoutTrickLevel)
def test_pickle_trick_level(value: LayoutTrickLevel):
    assert pickle.loads(pickle.dumps(value)) == value


@pytest.fixture()
def multiworld_rdvgame(test_files_dir):
    return test_files_dir.read_json("log_files", "multi-oldechoes.rdvgame")


def test_load_multiworld(multiworld_rdvgame):
    input_data = copy.deepcopy(multiworld_rdvgame)

    # Run
    result = LayoutDescription.from_json_dict(input_data)
    input_data["schema_version"] = description_migration.CURRENT_VERSION

    # Assert
    as_json = result.as_json()
    del input_data["info"]
    del as_json["info"]

    assert as_json == input_data


@pytest.mark.parametrize("reason", ["ok", "bad_secret", "bad_info"])
def test_round_trip_no_spoiler(obfuscator_test_secret, multiworld_rdvgame, reason):
    input_data = copy.deepcopy(multiworld_rdvgame)
    input_data = description_migration.convert_to_current_version(input_data)
    input_data["info"]["has_spoiler"] = False
    layout = LayoutDescription.from_json_dict(input_data)

    # Encode
    encoded = layout.as_json()
    assert set(encoded.keys()) & {"game_modifications", "item_order"} == set()

    expectation = pytest.raises(InvalidLayoutDescription)
    if reason == "bad_secret":
        encoded["secret"] = "bad"
    elif reason == "bad_info":
        encoded["info"]["has_spoiler"] = True
    else:
        expectation = contextlib.nullcontext()

    with expectation:
        result = LayoutDescription.from_json_dict(encoded)
        assert result == layout


def test_no_spoiler_encode(obfuscator_no_secret, multiworld_rdvgame):
    input_data = copy.deepcopy(multiworld_rdvgame)
    input_data = description_migration.convert_to_current_version(input_data)
    input_data["info"]["has_spoiler"] = False
    layout = LayoutDescription.from_json_dict(input_data)

    # Encode
    encoded = layout.as_json()

    assert set(encoded.keys()) & {"game_modifications", "item_order", "secret"} == set()


def test_round_trip_binary_normal(multiworld_rdvgame):
    layout = LayoutDescription.from_json_dict(multiworld_rdvgame)

    assert LayoutDescription.from_bytes(layout.as_binary()) == layout


def test_round_trip_binary_need_preset_decode(multiworld_rdvgame):
    layout = LayoutDescription.from_json_dict(multiworld_rdvgame)

    encoded = layout.as_binary(include_presets=False)
    with pytest.raises(InvalidLayoutDescription):
        LayoutDescription.from_bytes(encoded)


def test_round_trip_binary_no_presets(multiworld_rdvgame):
    layout = LayoutDescription.from_json_dict(multiworld_rdvgame)
    presets = [VersionedPreset.with_preset(preset) for preset in layout.all_presets]

    encoded = layout.as_binary(include_presets=False)
    assert LayoutDescription.from_bytes(encoded, presets=presets) == layout


def test_binary_blank(test_files_dir: TestFilesDir) -> None:
    path = test_files_dir.read_json("log_files", "blank", "issue-3717.rdvgame")
    layout = LayoutDescription.from_json_dict(path)

    binary = layout.as_binary(include_presets=False)
    assert binary == (
        b"RDVG\x02\xda\x04x\x9c\xb5SMs\xda0\x10\xfd\x01\xfd\x13\x1a\x9d\xda\x19'$@\x98"
        b"\x84[2\xa1\xa5\r$i\xbe\x9a6\x93\xf1\x08{\x01\xc5\xb2\xa4H2\xc4e8\xf6\x7fwe"
        b"\xe3\x02\x93t\xa0\x87\xde\xb4\xab\xf7\xde\xae\xb4\xfb~\xbd\x9bQ\x1b\x8d"
        b"!e\xe1\x04\x8c\xe5J\xd2v\xfd0\xa0\\\x0e\x15m\xcf\xa8a2V\x13&\xf9\xca==\xd8"
        b"\xdd\xdf\xdd\xdb\x8da\xd2j\xd2\xe0\rH8\xe2\x0ea\r\xc6\xea\xcdxx\x84\x18"
        b"\r&e\x82\xcb\x04\xd3\xa7\xac{^\xdf\xb9o\xdc\xfe|\xe67\xc3\xa4\xff5\xd6"
        b"\xec\xca\r\xbf\xdf\xedM\xf5\xed\xc5Y\xff\xf8\xd3S\x03)cfC\xab\x15\x17`"
        b"h\xdb\x99\x0c\x02j\x01b\xdan5\xf7\x0f\x8e\x1a\xcd\xc3f\x81\x19"
        b"\xa3\xe2\x8f\xfb\xf3V\xef\xa0~\x83\xac\xa92q\xb8H\xf7\x94\xb5\x02"
        b"\xac%\x1f\xb9\xe0\x83\xcc:0\xe4\xd2(\x8b\xcdp\x97\xd3y@G,\x850U1\x1f\xf2\x88"
        b"9\xec\xdc\xd2\xf6\xc3\xacH#\x7f \x186\x8ce\x1d3\x8e\xcbQ\x08\xcf\x19\xd7"
        b")H\xe7\x7f\x86;H\x11>\x9b\xcfW\x10B\x95:\xc8\xfe,\x9dQ\xb5\xeb\xc5\r96\xc0"
        b'j\xd7\x9aM%\xb9T\x1c%\x02\x1a\xab(\t#%%D\x8b\xda\xb3\xf9";\x05\x96Hl'
        b"\xbdLU\xaa>,u\xfd\xe1\x84E\xc9\xce\x85\x149\xe9!\x85\\)\x95\xd6.y\x94d\x9a"
        b"\xbc\xef\xbc8\xc3\xc8\x19\xe4\x1f\xb0\x93;\x1e9er\x1fb\xd5\x13\x91\x81?\xae"
        b"\x13\xaa\xac\xc7\x7f\x03\xa6\xf1\t\x01\xed\xbch\xa1,\x9f\x009\x05\xad"
        b'\xdc\x8a\xfa"\xef\xd1\x15\x13\xf1]`\x0e\xe2ua\xcc\t7\xf6\xc0\x8e\x043\xca'
        b"\xc9\r\xee\x8b\x1d\xe2(\xfa*\xce\x04 \xad\x07\xf1\x08\xd6Y\xa7*\x1b\x08 _"
        b"\xb2T\xff+u#g}$\x15\xad\xcf\xad\xc5]#\xf86$\xe0g\x17\x1a\xd5C\xffJ+"
        b"\xff\xcac_\tP\xbf\x19c\x1c\xf5rl\xb5.\x86e\xbb\xc5i\xca\xdd\xb8\xec"
        b'P0\x1c\x91\xc7yB\xe8r\xed\x17\xf0I%\xbe\xb26\x10\xf1\xd2z2\x13"'
        b"\xa0\xd8\xc9\x08\\\x15\xc5\xcc$!.\xa3\xc6\xd7\x15),\xfbf5\xa9\xfeC\xad"
        b"\xcaE\xe8\xaa\xc8\xdb\xa8p\xc4cP\xd8#D3z\xf7>,\x97\x8e9R\xf6\xb6\xc5n\xad"
        b".\xe0\x1f\xde\xd6\xd3\x0b^Od\xa9\xb2\xa5w\x82\x85\x176\x95\xaf\xb6 X\xf5"
        b"\xdaJ\xb5\r\x96{\x9c\xff\x06}\xef\xeaQ"
    )
