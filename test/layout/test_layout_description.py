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
        b'RDVG\x01\xd5\x04x\x9c\xb5S\xdbN\x1b1\x10\xed\xa7X~j\xa5\x85@\x12"\xc8\x1b'
        b"(\xb4\xb4$\\\x03\xa5Ehevg\x13\xb3^\xdb\xd8\xde\x844\xca\xbfw\xbc"
        b"\x97\x92\x08\xaa\xa4\x0f}\xf3\x8c\xcf93\xf6\xcc\x99S\x1b\x8d!c"
        b"\xe1\x04\x8c\xe5J\xd2ns?\xa0\\&\x8av\xe7\xd40\x19\xab\t\x93|\xe9\x9e"
        b"\xeem\xefn\xefl\xc70\xe9\xb4i\xf0\x0e$\x1cq\x87\xb0\x16c\xcdv\x9c\x1c"
        b" F\x83\xc9\x98\xe02\xc5t\x8f\x9d\x9c5\xb7\xeeZ7\xbf\x9e\xf90I\x07\x97\xb1fW."
        b"\xf9q\xbb3\xd57\xe7\xa7\x83\xc3/O-\xa4\x8c\x99\r\xadV\\\x80\xa1]g"
        b"r\x08\xa8\x05\x88i\xb7\xd3\xde\xdd;h\xb5\xf7\xdb\x05f\x8c\x8a?\xef\xce:\xfd"
        b"\xbd\xe6\x10YSe\xe2\xb0J\xf7\x95\xb5\x02\xac%\x9f\xb9\xe0\x8f\xb9u`\xc8\x85"
        b"Q\x16\x9b\xe1nF\x17\x01\x1d\xb1\x0c\xc2L\xc5<\xe1\x11s\xd8\xb9\xa5\xdd\xfby"
        b"\x91F\xfe\xa3`\xd80\x96u\xcc8.G!<\xe7\\g \x9d\xff\x19\xee C\xf8|\xb1XB\x08U"
        b"\xea \xfb\xabtF5\xae\xab\x1brh\x805\xae5\x9bJr\xa18J\x044VQ\x1aFJJ\x88\xaa"
        b"\xda\xf3E\x95\x9d\x02K%\xb6^\xa6jU\x1f\x96\xba\xfep\xc4\xa2t\xeb\\\x8a"
        b"\x19\xe9#\x85\\)\x955.x\x94\xe6\x9a|<~q\x86\x91S\x98}\xc2Nny\xe4\x94"
        b"\x99\xf9\x10\xab\x1e\x89\x1c\xfcq\x95Pg=\xfe;0\x8dO\x08\xe8\xf1\x8b\x16\xca"
        b"\xf2\t\x90\x1eh\xe5\x96\xd4\xab\xbcG\xd7L\xc4\x9f\x00s\x10\xaf\ncN\xb8\xb1"
        b"\x07\x1eK0\xa3\x19\x19\xe2\xbe\xd8\x04G1Pq.\x00i}\x88G\xb0\xca\xea"
        b"\xa9\xfcQ\x00\xf9\x96g\xfa_\xa9k9\xab#\xa9i\x03n-\xee\x1a\xc1\xb7!"
        b"\x01?\xbb\xd0\xa8\x1f\xfaWZ\xf9W\x1e\xfbF\x80\xfa\xcd\x18\xe3\xa8_\xc7\xd68"
        b"\xc1\xb0l\xb78M\xb9\x1b\x97\x1d\n\x86#\xf28O\x08\xddL\xfb\x05|R\xa9"
        b"\xaf\xac\rD\xbc\xb4\x9e\xcc\x85\x08(v2\x02WG13i\x88\xcb\xa8\xf1uE\n\xcb\xbe"
        b"[M\xaa\xffP\xabv\x11\xba*\xf26*\x1c\xf1\x10\x14\xf6\x08\xd1\x8c\xde\xbd\xf7"
        b"\xafK\xc7\x1c){\xdb`\xb7\x96\x17\xf0\x0fo\xe3\xe9\x05o'\xf2\xaa\xb2\xa1w"
        b"\x82\xca\x0b\xeb\xca\xd7[\x10,{m\xa9\xda\x1a\xcb=,>\xfc\x06K\xab\xe9\xc1"
    )
