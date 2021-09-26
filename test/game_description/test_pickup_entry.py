import pytest

from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import PickupEntry, PickupModel
from randovania.games.game import RandovaniaGame


def test_extra_resources_maximum(echoes_item_database):
    item = ItemResourceInfo(0, "Item", "Item", 2, None)
    msg = "Attempt to give 5 of Item, more than max capacity"

    with pytest.raises(ValueError, match=msg):
        PickupEntry(
            name="broken",
            model=PickupModel(RandovaniaGame.METROID_PRIME_ECHOES, "Nothing"),
            item_category=echoes_item_database.item_categories["missile"],
            broad_category=echoes_item_database.item_categories["missile"],
            progression=(),
            extra_resources=(
                (item, 5),
            )
        )
