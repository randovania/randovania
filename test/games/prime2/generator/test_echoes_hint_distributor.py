from unittest.mock import MagicMock, call, ANY

import pytest

from randovania.game_description.hint import Hint, HintType, PrecisionPair, HintLocationPrecision, HintItemPrecision, \
    HintDarkTemple
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_index import PickupIndex
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
        LogbookAsset(0xE3B417BF): _keybearer_hint(11),
        LogbookAsset(0x65206511): _keybearer_hint(15),
        LogbookAsset(0x28E8C41A): _keybearer_hint(19),
        # Agon
        LogbookAsset(0x150E8DB8): _keybearer_hint(45),
        LogbookAsset(0xDE525E1D): _keybearer_hint(53),
        # Torvus
        LogbookAsset(0x58C62CB3): _keybearer_hint(68),
        LogbookAsset(0x939AFF16): _keybearer_hint(91),
        # Sanctuary
        LogbookAsset(0x62CC4DC3): _keybearer_hint(117),
        LogbookAsset(0xA9909E66): _keybearer_hint(106),

        # Locations with hints
        LogbookAsset(1041207119): _light_suit_location_hint(24),
        LogbookAsset(4115881194): _guardian_hint(43),
        LogbookAsset(1948976790): _guardian_hint(79),
        LogbookAsset(3212301619): _guardian_hint(115),

        # Dark Temple hints
        LogbookAsset(67497535): Hint(HintType.RED_TEMPLE_KEY_SET, None, dark_temple=HintDarkTemple.AGON_WASTES),
        LogbookAsset(4072633400): Hint(HintType.RED_TEMPLE_KEY_SET, None, dark_temple=HintDarkTemple.TORVUS_BOG),
        LogbookAsset(0x82919C91): Hint(HintType.RED_TEMPLE_KEY_SET, None,
                                       dark_temple=HintDarkTemple.SANCTUARY_FORTRESS),

        # Jokes
        LogbookAsset(0x49CD4F34): Hint(HintType.JOKE, None),
        LogbookAsset(0x9F94AC29): Hint(HintType.JOKE, None),
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

