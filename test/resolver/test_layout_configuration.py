import pickle
from typing import Tuple, Dict

import pytest

import randovania
from randovania.resolver.layout_configuration import LayoutTrickLevel, LayoutConfiguration
from randovania.resolver.layout_description import LayoutDescription, SolverPath, _item_locations_to_pickup_assignment
from randovania.resolver.patcher_configuration import PatcherConfiguration
from randovania.resolver.permalink import Permalink


@pytest.mark.parametrize("value", LayoutTrickLevel)
def test_pickle_trick_level(value: LayoutTrickLevel):
    assert pickle.loads(pickle.dumps(value)) == value


@pytest.mark.parametrize("permalink", [
    Permalink(
        seed_number=1000,
        spoiler=True,
        patcher_configuration=PatcherConfiguration.default(),
        layout_configuration=LayoutConfiguration.default(),
    )
])
@pytest.mark.parametrize("item_locations", [
    {}
])
@pytest.mark.parametrize("solver_path", [
    tuple()
])
def test_round_trip_default(permalink: Permalink,
                            item_locations: Dict[str, Dict[str, str]],
                            solver_path: Tuple[SolverPath, ...]
                            ):
    original = LayoutDescription(
        version=randovania.VERSION,
        permalink=permalink,
        pickup_assignment=_item_locations_to_pickup_assignment(item_locations),
        solver_path=solver_path,
    )

    # Run
    decoded = LayoutDescription.from_json_dict(original.as_json)

    # Assert
    assert decoded == original
