from unittest.mock import MagicMock, call, ANY

import pytest

from randovania.game_description.hint import Hint, HintType, PrecisionPair, HintLocationPrecision, HintItemPrecision, \
    HintDarkTemple
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.games.game import RandovaniaGame
from randovania.games.prime2.generator.hint_distributor import EchoesHintDistributor
from randovania.generator.hint_distributor import PreFillParams


@pytest.mark.parametrize("is_multiworld", [False, True])
async def test_add_default_hints_to_patches(echoes_game_description, empty_patches, is_multiworld):
    # Setup
    layout_configuration = MagicMock()
    layout_configuration.game = RandovaniaGame.METROID_PRIME_ECHOES
    rng = MagicMock()
    hint_distributor = EchoesHintDistributor()

    def _light_suit_location_hint(number: int):
        return Hint(HintType.LOCATION, PrecisionPair(HintLocationPrecision.LIGHT_SUIT_LOCATION,
                                                     HintItemPrecision.DETAILED, include_owner=False),
                    PickupIndex(number))

    def _guardian_hint(number: int):
        return Hint(HintType.LOCATION, PrecisionPair(HintLocationPrecision.GUARDIAN,
                                                     HintItemPrecision.DETAILED, include_owner=False),
                    PickupIndex(number))

    def _keybearer_hint(number: int):
        return Hint(HintType.LOCATION, PrecisionPair(HintLocationPrecision.KEYBEARER,
                                                     HintItemPrecision.BROAD_CATEGORY,
                                                     include_owner=True),
                    PickupIndex(number))

    expected = {
        # Keybearer
        'Temple Grounds/Landing Site/Keybearer Corpse (M-Dhe)': _keybearer_hint(11),
        'Temple Grounds/Industrial Site/Keybearer Corpse (J-Fme)': _keybearer_hint(15),
        'Temple Grounds/Storage Cavern A/Keybearer Corpse (D-Isl)': _keybearer_hint(19),
        # Agon
        'Agon Wastes/Central Mining Station/Keybearer Corpse (J-Stl)': _keybearer_hint(45),
        'Agon Wastes/Main Reactor/Keybearer Corpse (B-Stl)': _keybearer_hint(53),
        # Torvus
        'Torvus Bog/Torvus Lagoon/Keybearer Corpse (S-Dly)': _keybearer_hint(68),
        'Torvus Bog/Catacombs/Keybearer Corpse (G-Sch)': _keybearer_hint(91),
        # Sanctuary
        'Sanctuary Fortress/Sanctuary Entrance/Keybearer Corpse (S-Jrs)': _keybearer_hint(117),
        'Sanctuary Fortress/Dynamo Works/Keybearer Corpse (C-Rch)': _keybearer_hint(106),

        # Locations with hints
        'Sanctuary Fortress/Sanctuary Energy Controller/Lore Scan': _light_suit_location_hint(24),
        'Sanctuary Fortress/Main Gyro Chamber/Lore Scan': _guardian_hint(43),
        'Sanctuary Fortress/Watch Station/Lore Scan': _guardian_hint(79),
        'Sanctuary Fortress/Main Research/Lore Scan': _guardian_hint(115),

        # Dark Temple hints
        'Sanctuary Fortress/Hall of Combat Mastery/Lore Scan': Hint(
            HintType.RED_TEMPLE_KEY_SET, None, dark_temple=HintDarkTemple.AGON_WASTES
        ),
        'Sanctuary Fortress/Sanctuary Entrance/Lore Scan': Hint(
            HintType.RED_TEMPLE_KEY_SET, None, dark_temple=HintDarkTemple.TORVUS_BOG
        ),
        'Torvus Bog/Catacombs/Lore Scan': Hint(
            HintType.RED_TEMPLE_KEY_SET, None, dark_temple=HintDarkTemple.SANCTUARY_FORTRESS
        ),

        # Jokes
        'Torvus Bog/Gathering Hall/Lore Scan': Hint(HintType.JOKE, None),
        'Torvus Bog/Training Chamber/Lore Scan': Hint(HintType.JOKE, None),
    }
    expected = {
        NodeIdentifier.from_string(ident_s): hint
        for ident_s, hint in expected.items()
    }

    # Run
    result = await hint_distributor.assign_pre_filler_hints(
        empty_patches,
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
