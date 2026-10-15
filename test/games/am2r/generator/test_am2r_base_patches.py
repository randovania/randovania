from __future__ import annotations

import dataclasses
import uuid
from random import Random

import pytest

from randovania.game_description.db.dock import DockWeakness
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.games.am2r.generator.base_patches_factory import AM2RBasePatchesFactory
from randovania.games.am2r.layout.am2r_configuration import AM2RConfiguration
from randovania.layout import filtered_database

_save_door_list = [
    "Main Caves/Surface Pond/Door to Surface Pond Save Station",
    "Main Caves/Surface Pond Save Station/Door to Surface Pond",
    "Golden Temple/Golden Temple Exterior/Door to Inner Temple Save Station",
    "Golden Temple/Inner Temple Save Station/Door to Golden Temple Exterior",
    "Hydro Station/Arachnus Save Station/Door to Arachnus Arena",
    "Hydro Station/Arachnus Arena/Door to Arachnus Save Station",
    "The Tower/Inner Save Station East Access/Door to Inner Save Station",
    "The Tower/Inner Save Station/Door to Inner Save Station East Access",
    "The Tower/Inner Save Station/Door to Inner Save Station West Access",
    "The Tower/Inner Save Station West Access/Door to Inner Save Station",
    "Distribution Center/Robomine Prison/Door to Energy Distribution Entrance Save Station",
    "Distribution Center/Energy Distribution Entrance Save Station/Door to Energy Distribution Tower West",
    "Distribution Center/Energy Distribution Entrance Save Station/Door to Robomine Prison",
    "Distribution Center/Energy Distribution Tower West/Door to Energy Distribution Entrance Save Station",
    "Distribution Center/Distribution Facility Tower East/Door to Distribution Facility Save Station",
    "Distribution Center/Distribution Facility Save Station/Door to Distribution Facility Tower East",
    "Distribution Center/Distribution Facility Save Station/Door to Distribution Facility Intersection",
    "Distribution Center/Distribution Facility Intersection/Door to Distribution Facility Save Station",
    "Distribution Center/Waterblob Habitat/Door to Facility Storage Save Station",
    "Distribution Center/Facility Storage Save Station/Door to Facility Storage Intersection East",
    "Distribution Center/Facility Storage Save Station/Door to Waterblob Habitat",
    "Distribution Center/Facility Storage Intersection East/Door to Facility Storage Save Station",
    "Genetics Laboratory/Laboratory Save Station Access/Door to Laboratory Save Station",
    "Genetics Laboratory/Laboratory Save Station/Door to Laboratory Entrance",
    "Genetics Laboratory/Laboratory Save Station/Door to Laboratory Save Station Access",
    "Genetics Laboratory/Laboratory Entrance/Door to Laboratory Save Station",
    "GFS Thoth/Thoth Save Station Access/Door to Thoth West Lift",
    "GFS Thoth/Thoth West Lift/Door to Thoth Save Station Access",
]

_lab_door_list = [
    "Genetics Laboratory/Laboratory Foyer/Door to Laboratory Small Shaft East",
    "Genetics Laboratory/Laboratory Small Shaft East/Door to Laboratory Foyer",
    "Genetics Laboratory/Laboratory Small Shaft East/Door to Laboratory Corridor",
    "Genetics Laboratory/Laboratory Corridor/Door to Laboratory Small Shaft East",
    "Genetics Laboratory/Laboratory Corridor/Door to Laboratory Long Shaft",
    "Genetics Laboratory/Laboratory Long Shaft/Door to Laboratory Corridor",
    "Genetics Laboratory/Laboratory Long Shaft/Door to Laboratory Spiked Hall",
    "Genetics Laboratory/Laboratory Spiked Hall/Door to Laboratory Arena",
    "Genetics Laboratory/Laboratory Spiked Hall/Door to Laboratory Long Shaft",
    "Genetics Laboratory/Laboratory Arena/Door to Laboratory Spiked Hall",
    "Genetics Laboratory/Laboratory Arena/Door to Laboratory Small Shaft West",
    "Genetics Laboratory/Laboratory Small Shaft West/Door to Laboratory Arena",
    "Genetics Laboratory/Laboratory Small Shaft West/Door to Queen Arena Access",
    "Genetics Laboratory/Queen Arena Access/Door to Laboratory Small Shaft West",
]


@pytest.mark.parametrize(
    ("force_blue_saves", "force_blue_labs"),
    [
        (False, False),
        (False, True),
        (True, False),
        (True, True),
    ],
)
def test_base_patches(am2r_game_description, preset_manager, force_blue_saves, force_blue_labs) -> None:
    # Setup
    game = am2r_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    base_configuration = preset.configuration
    assert isinstance(base_configuration, AM2RConfiguration)
    base_configuration = dataclasses.replace(
        base_configuration, blue_save_doors=force_blue_saves, force_blue_labs=force_blue_labs
    )
    game_description = filtered_database.game_description_for_layout(base_configuration)

    # Run
    result = AM2RBasePatchesFactory().create_base_patches(base_configuration, Random(0), game_description, False, 0)

    # Assert
    door_count = 0
    if force_blue_saves:
        for num in _save_door_list:
            weakness = result.get_dock_weakness_for(
                game_description.typed_node_by_identifier(NodeIdentifier.from_string(num), DockNode)
            )
            assert weakness.name == "Normal Door (Forced)"
            door_count += 1

    if force_blue_labs:
        for num in _lab_door_list:
            weakness = result.get_dock_weakness_for(
                game_description.typed_node_by_identifier(NodeIdentifier.from_string(num), DockNode)
            )
            assert isinstance(weakness, DockWeakness)
            assert weakness.name == "Normal Door (Forced)"
            door_count += 1

    get_amount_of_nones = len([door for door in result.dock_weakness if door is None])
    assert (len(result.dock_weakness) - get_amount_of_nones) == door_count
