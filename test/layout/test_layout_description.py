import pickle
from typing import Tuple, Dict

import pytest

import randovania
from randovania.game_description import data_reader
from randovania.game_description.game_patches import GamePatches
from randovania.generator import elevator_distributor
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.layout.layout_description import LayoutDescription, SolverPath
from randovania.layout.patcher_configuration import PatcherConfiguration
from randovania.layout.permalink import Permalink
from randovania.layout.trick_level import LayoutTrickLevel


@pytest.mark.parametrize("value", LayoutTrickLevel)
def test_pickle_trick_level(value: LayoutTrickLevel):
    assert pickle.loads(pickle.dumps(value)) == value


@pytest.mark.skip("loading log from file is broken")
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

    game = data_reader.decode_data(permalink.layout_configuration.game_data)
    original = LayoutDescription(
        version=randovania.VERSION,
        permalink=permalink,
        patches=GamePatches(
            {},
            elevator_distributor.elevator_connections_for_seed_number(permalink.seed_number),
            {}, {}, (), game.starting_location
        ),
        solver_path=solver_path,
    )

    # Run
    decoded = LayoutDescription.from_json_dict(original.as_json)

    # Assert
    assert decoded == original
