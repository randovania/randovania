from __future__ import annotations

import dataclasses
import uuid
from random import Random

import pytest

from randovania.games.am2r.generator.base_patches_factory import AM2RBasePatchesFactory
from randovania.games.am2r.layout.am2r_configuration import AM2RConfiguration
from randovania.layout import filtered_database

_save_door_mapping = {
    37: "Normal Door",
    41: "Normal Door",
    305: "Normal Door",
    342: "Normal Door",
    495: "Normal Door",
    498: "Normal Door",
    1051: "Normal Door",
    1057: "Normal Door",
    1058: "Normal Door",
    1062: "Normal Door",
    1185: "Normal Door",
    1190: "Normal Door",
    1191: "Normal Door",
    1194: "Normal Door",
    1277: "Normal Door",
    1302: "Normal Door",
    1303: "Normal Door",
    1306: "Normal Door",
    1339: "Normal Door",
    1343: "Normal Door",
    1345: "Normal Door",
    1348: "Normal Door",
    1736: "Normal Door",
    1740: "Normal Door",
    1741: "Normal Door",
    1745: "Normal Door",
    1764: "Normal Door",
    1769: "Normal Door",
    1770: "Normal Door",
    1775: "Normal Door",
    1776: "Normal Door",
    1779: "Normal Door",
    1780: "Normal Door",
    1787: "Normal Door",
    1788: "Normal Door",
    1796: "Normal Door",
    1797: "Normal Door",
    1804: "Normal Door",
    1805: "Normal Door",
    1808: "Normal Door",
    1889: "Normal Door",
    1894: "Normal Door",
}

_lab_door_mapping: dict = {}


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
        base_configuration, blue_save_doors=force_blue_saves, force_blue_labs=force_blue_saves
    )
    game_description = filtered_database.game_description_for_layout(base_configuration)

    # Run
    result = AM2RBasePatchesFactory().create_base_patches(base_configuration, Random(0), game_description, False, 0)

    # Assert
    if force_blue_saves:
        for num, value in _save_door_mapping.items():
            assert result.dock_weakness[num] is not None
            assert result.dock_weakness[num].name == value

    if force_blue_labs:
        for num, value in _lab_door_mapping.items():
            assert result.dock_weakness[num] is not None
            assert result.dock_weakness[num].name == value
