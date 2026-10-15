from __future__ import annotations

import contextlib
import copy
import pickle
import uuid
from typing import TYPE_CHECKING

import pytest

from randovania.interface_common.worlds_configuration import is_uuid_multiworld
from randovania.layout import description_migration
from randovania.layout.base.trick_level import LayoutTrickLevel
from randovania.layout.layout_description import InvalidLayoutDescription, LayoutDescription
from randovania.layout.versioned_preset import VersionedPreset

if TYPE_CHECKING:
    from conftest import TestFilesDir


@pytest.mark.parametrize("value", LayoutTrickLevel)
def test_pickle_trick_level(value: LayoutTrickLevel) -> None:
    assert pickle.loads(pickle.dumps(value)) == value


@pytest.fixture
def multiworld_rdvgame(test_files_dir: TestFilesDir) -> dict:
    return test_files_dir.read_json("log_files", "multi-oldechoes.rdvgame")


def test_load_multiworld(multiworld_rdvgame: dict) -> None:
    input_data = copy.deepcopy(multiworld_rdvgame)

    expected = description_migration.convert_to_current_version(copy.deepcopy(input_data))

    # Run
    result = LayoutDescription.from_json_dict(input_data)
    expected["schema_version"] = description_migration.CURRENT_VERSION

    as_json = result.as_json()
    del expected["info"]
    del as_json["info"]

    input_layouts = []
    for mods in expected["game_modifications"]:
        input_layouts.append(mods.pop("locations"))
    json_layouts = []
    for mods in as_json["game_modifications"]:
        json_layouts.append(mods.pop("locations"))

    # Assert
    assert len(input_layouts) == len(json_layouts)
    for i in range(len(input_layouts)):
        assert sorted(input_layouts[i], key=lambda d: d["index"]) == sorted(json_layouts[i], key=lambda d: d["index"])
    assert as_json == expected


def _layout_with_seed(rdvgame: dict, seed_number: int) -> LayoutDescription:
    data = copy.deepcopy(rdvgame)
    data["info"]["seed"] = seed_number
    return LayoutDescription.from_json_dict(data)


def test_identifiers_are_salted_by_seed(multiworld_rdvgame: dict) -> None:
    first = _layout_with_seed(multiworld_rdvgame, 1000)
    second = _layout_with_seed(multiworld_rdvgame, 2000)

    assert first.as_json()["game_modifications"] == second.as_json()["game_modifications"]
    assert first.shareable_hash != second.shareable_hash
    assert first.seed_uuid != second.seed_uuid
    assert _layout_with_seed(multiworld_rdvgame, 1000).seed_uuid == first.seed_uuid


def test_seed_uuid_is_a_valid_uuid(multiworld_rdvgame: dict) -> None:
    seed_uuid = _layout_with_seed(multiworld_rdvgame, 1000).seed_uuid

    assert seed_uuid.version == 8
    assert seed_uuid.variant == uuid.RFC_4122
    assert not is_uuid_multiworld(seed_uuid)


@pytest.mark.parametrize("seed_number", [0, 1, 1000, 2**31 - 1])
def test_shareable_hash_is_a_prefix_of_seed_uuid(multiworld_rdvgame: dict, seed_number: int) -> None:
    """A given uuid must always imply a given shareable hash."""
    layout = _layout_with_seed(multiworld_rdvgame, seed_number)

    assert layout.seed_uuid.bytes[:5] == layout.shareable_hash_bytes


@pytest.mark.parametrize("reason", ["ok", "bad_secret", "bad_info"])
def test_round_trip_no_spoiler(obfuscator_test_secret: None, multiworld_rdvgame: dict, reason: str) -> None:
    input_data = copy.deepcopy(multiworld_rdvgame)
    input_data = description_migration.convert_to_current_version(input_data)
    input_data["info"]["has_spoiler"] = False
    layout = LayoutDescription.from_json_dict(input_data)

    # Encode
    encoded = layout.as_json()
    assert set(encoded.keys()) & {"game_modifications", "item_order"} == set()

    expectation = pytest.raises(InvalidLayoutDescription, match="Unable to read details of a race game file")
    if reason == "bad_secret":
        encoded["secret"] = "bad"
    elif reason == "bad_info":
        encoded["info"]["has_spoiler"] = True
    else:
        expectation = contextlib.nullcontext()

    with expectation:
        result = LayoutDescription.from_json_dict(encoded)
        assert result == layout


def test_no_spoiler_encode(obfuscator_no_secret: None, multiworld_rdvgame: dict) -> None:
    input_data = copy.deepcopy(multiworld_rdvgame)
    input_data = description_migration.convert_to_current_version(input_data)
    input_data["info"]["has_spoiler"] = False
    layout = LayoutDescription.from_json_dict(input_data)

    # Encode
    encoded = layout.as_json()

    assert set(encoded.keys()) & {"game_modifications", "item_order", "secret"} == set()


def test_round_trip_binary_normal(multiworld_rdvgame: dict) -> None:
    layout = LayoutDescription.from_json_dict(multiworld_rdvgame)

    assert LayoutDescription.from_bytes(layout.as_binary()) == layout


def test_round_trip_binary_need_preset_decode(multiworld_rdvgame: dict) -> None:
    layout = LayoutDescription.from_json_dict(multiworld_rdvgame)

    encoded = layout.as_binary(include_presets=False)
    with pytest.raises(InvalidLayoutDescription):
        LayoutDescription.from_bytes(encoded)


def test_round_trip_binary_no_presets(multiworld_rdvgame: dict) -> None:
    layout = LayoutDescription.from_json_dict(multiworld_rdvgame)
    presets = [VersionedPreset.with_preset(preset) for preset in layout.all_presets]

    encoded = layout.as_binary(include_presets=False)
    assert LayoutDescription.from_bytes(encoded, presets=presets) == layout
