import pytest

from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import PickupEntry, PickupModel
from randovania.games.game import RandovaniaGame


def test_extra_resources_maximum():
    item = ItemResourceInfo(0, "Item", "Item", 2, None)
    msg = "Attempt to give 5 of Item, more than max capacity"

    with pytest.raises(ValueError, match=msg):
        PickupEntry(
            name="broken",
            model=PickupModel(RandovaniaGame.METROID_PRIME_ECHOES, "Nothing"),
            item_category=ItemCategory.ETM,
            broad_category=ItemCategory.MISSILE,
            progression=(),
            extra_resources=(
                (item, 5),
            )
        )
