from __future__ import annotations

import copy
import dataclasses
from random import Random
from typing import TYPE_CHECKING
from unittest.mock import ANY, MagicMock, call

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.hint import (
    HintDarkTemple,
    HintItemPrecision,
    JokeHint,
    LocationHint,
    PrecisionPair,
    RedTempleHint,
    SpecificHintPrecision,
)
from randovania.game_description.hint_features import HintFeature
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.prime2.generator.hint_distributor import EchoesHintDistributor
from randovania.generator.generator import create_player_pool
from randovania.generator.pre_fill_params import PreFillParams
from randovania.layout.base.standard_pickup_state import StandardPickupState
from randovania.resolver import debug

if TYPE_CHECKING:
    from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration


@pytest.mark.parametrize("is_multiworld", [False, True])
async def test_add_default_hints_to_patches(echoes_game_description, echoes_game_patches, is_multiworld):
    # Setup
    layout_configuration = MagicMock()
    layout_configuration.game = RandovaniaGame.METROID_PRIME_ECHOES
    rng = MagicMock()
    hint_distributor = EchoesHintDistributor()

    def precision(loc: str) -> HintFeature:
        return echoes_game_description.hint_feature_database[loc]

    def _light_suit_location_hint(number: int):
        return LocationHint(
            PrecisionPair(precision("specific_hint_2mos"), HintItemPrecision.DETAILED, include_owner=False),
            PickupIndex(number),
        )

    def _guardian_hint(number: int):
        return LocationHint(
            PrecisionPair(precision("specific_hint_guardian"), HintItemPrecision.DETAILED, include_owner=False),
            PickupIndex(number),
        )

    def _keybearer_hint(number: int):
        return LocationHint(
            PrecisionPair(precision("specific_hint_keybearer"), SpecificHintPrecision(0.4), include_owner=True),
            PickupIndex(number),
        )

    expected = {
        # Keybearer
        "Temple Grounds/Landing Site/Keybearer Corpse (M-Dhe)": _keybearer_hint(11),
        "Temple Grounds/Industrial Site/Keybearer Corpse (J-Fme)": _keybearer_hint(15),
        "Temple Grounds/Storage Cavern A/Keybearer Corpse (D-Isl)": _keybearer_hint(19),
        # Agon
        "Agon Wastes/Central Mining Station/Keybearer Corpse (J-Stl)": _keybearer_hint(45),
        "Agon Wastes/Main Reactor/Keybearer Corpse (B-Stl)": _keybearer_hint(53),
        # Torvus
        "Torvus Bog/Torvus Lagoon/Keybearer Corpse (S-Dly)": _keybearer_hint(68),
        "Torvus Bog/Catacombs/Keybearer Corpse (G-Sch)": _keybearer_hint(91),
        # Sanctuary
        "Sanctuary Fortress/Sanctuary Entrance/Keybearer Corpse (S-Jrs)": _keybearer_hint(117),
        "Sanctuary Fortress/Dynamo Works/Keybearer Corpse (C-Rch)": _keybearer_hint(106),
        # Locations with hints
        "Sanctuary Fortress/Sanctuary Energy Controller/Lore Scan": _light_suit_location_hint(24),
        "Sanctuary Fortress/Main Gyro Chamber/Lore Scan": _guardian_hint(43),
        "Sanctuary Fortress/Watch Station/Lore Scan": _guardian_hint(79),
        "Sanctuary Fortress/Main Research/Lore Scan": _guardian_hint(115),
        # Dark Temple hints
        "Sanctuary Fortress/Hall of Combat Mastery/Lore Scan": RedTempleHint(dark_temple=HintDarkTemple.AGON_WASTES),
        "Sanctuary Fortress/Sanctuary Entrance/Lore Scan": RedTempleHint(dark_temple=HintDarkTemple.TORVUS_BOG),
        "Torvus Bog/Catacombs/Lore Scan": RedTempleHint(dark_temple=HintDarkTemple.SANCTUARY_FORTRESS),
        # Jokes
        "Torvus Bog/Gathering Hall/Lore Scan": JokeHint(),
        "Torvus Bog/Training Chamber/Lore Scan": JokeHint(),
    }
    expected = {NodeIdentifier.from_string(ident_s): hint for ident_s, hint in expected.items()}

    # Run
    result = await hint_distributor.assign_pre_filler_hints(
        echoes_game_patches,
        prefill=PreFillParams(
            rng=rng,
            configuration=layout_configuration,
            game=echoes_game_description,
            is_multiworld=is_multiworld,
        ),
    )

    # Assert
    rng.shuffle.assert_has_calls([call(ANY), call(ANY)])
    assert result.hints == expected


@pytest.fixture
def echoes_configuration_everything_shuffled(default_echoes_configuration) -> EchoesConfiguration:
    old_pickups_config = default_echoes_configuration.standard_pickup_configuration
    pickups_state = copy.copy(old_pickups_config.pickups_state)

    for pickup in old_pickups_config.pickups_state:
        if pickup.must_be_starting:
            continue
        pickups_state[pickup] = StandardPickupState(
            num_shuffled_pickups=1, included_ammo=tuple(1 for ammo in pickup.ammo)
        )

    return dataclasses.replace(
        default_echoes_configuration,
        standard_pickup_configuration=dataclasses.replace(
            old_pickups_config,
            pickups_state=pickups_state,
        ),
        ammo_pickup_configuration=dataclasses.replace(
            default_echoes_configuration.ammo_pickup_configuration,
            pickups_state={
                ammo: dataclasses.replace(ammo_state, pickup_count=1)
                for ammo, ammo_state in default_echoes_configuration.ammo_pickup_configuration.pickups_state.items()
            },
        ),
    )


async def test_keybearer_hint_precisions(
    echoes_configuration_everything_shuffled, echoes_game_patches, echoes_pickup_database
):
    # Setup
    rng = Random(0)

    player_pools = [
        await create_player_pool(rng, echoes_configuration_everything_shuffled, 0, 1, "World 1", MagicMock()),
    ]
    pool = player_pools[0]

    hint_distributor = EchoesHintDistributor()

    hint_node = NodeIdentifier.create("Agon Wastes", "Central Mining Station", "Keybearer Corpse (J-Stl)")
    keybearer_precision = (await hint_distributor.get_specific_pickup_precision_pairs())[hint_node]
    hint = LocationHint(keybearer_precision, PickupIndex(0))

    categories = echoes_pickup_database.pickup_categories
    broad_categories = {categories["chozo"], categories["luminoth"], categories["key"], categories["cheat"]}

    pickup_results: dict[str, HintFeature] = {}
    expected_results: dict[str, HintFeature] = {}

    # Run
    for pickup in pool.pickups_in_world:
        expected_results[pickup.name] = next(ft for ft in pickup.hint_features if ft in broad_categories)

        patches = echoes_game_patches.assign_own_pickups([(PickupIndex(0), pickup)])

        with debug.with_level(1):
            precision = hint_distributor.get_hint_precision(hint_node, hint, rng, patches, player_pools)

        assert isinstance(precision.item, HintFeature)
        pickup_results[pickup.name] = precision.item

    # Assert
    assert pickup_results == expected_results
