import pytest

from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import PickupEntry, PickupModel
from randovania.games.game import RandovaniaGame


def test_extra_resources_maximum(generic_item_category):
    item = ItemResourceInfo(0, "Item", "Item", 2, None)
    msg = "Attempt to give 5 of Item, more than max capacity"

    with pytest.raises(ValueError, match=msg):
        PickupEntry(
            name="broken",
            model=PickupModel(RandovaniaGame.METROID_PRIME_ECHOES, "Nothing"),
            item_category=generic_item_category,
            broad_category=generic_item_category,
            progression=(),
            extra_resources=(
                (item, 5),
            )
        )
