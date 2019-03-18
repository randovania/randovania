from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resource_type import ResourceType
from randovania.game_description.resources import SimpleResourceInfo, PickupEntry, ConditionalResources
from randovania.resolver import state


def test_add_pickup_to_state():
    # Starting State
    s = state.State({}, None, None, None, None)

    resource_a = SimpleResourceInfo(1, "A", "A", ResourceType.ITEM)
    resource_b = SimpleResourceInfo(2, "B", "B", ResourceType.ITEM)
    p = PickupEntry("B", 2, ItemCategory.SUIT,
                    (
                        ConditionalResources(None, None, ((resource_a, 1),)),
                        ConditionalResources(None, resource_a, ((resource_b, 1),)),
                    ))

    # Run
    state.add_pickup_to_state(s, p)
    state.add_pickup_to_state(s, p)

    # Assert
    assert s.resources == {
        resource_a: 1,
        resource_b: 1,
    }
