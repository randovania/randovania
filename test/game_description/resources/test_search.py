from randovania.game_description.resources import search
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo


def test_search_find_simple() -> None:
    r1 = SimpleResourceInfo(1, "Resource1", "R1", ResourceType.MISC)
    r2 = SimpleResourceInfo(2, "Resource2", "R2", ResourceType.MISC)
    r3 = SimpleResourceInfo(3, "Resource3", "R3", ResourceType.MISC)
    db = [r1, r2, r3]

    result = search.find_resource_info_with_id(db, "R2", ResourceType.MISC)
    assert result is r2


def test_search_find_item() -> None:
    r1 = ItemResourceInfo(1, "Resource1", "R1", 1)
    r2 = ItemResourceInfo(2, "Resource2", "R2", 2)
    r3 = ItemResourceInfo(3, "Resource3", "R3", 1)
    db = [r1, r2, r3]

    result = search.find_resource_info_with_id(db, "R2", ResourceType.ITEM)
    assert result is r2
