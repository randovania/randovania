import functools

from randovania.game_description import data_reader
from randovania.game_description.data_reader import read_resource_database, read_pickup_database
from randovania.game_description.game_description import GameDescription
from randovania.game_description.resources import ResourceDatabase, PickupDatabase
from randovania.games.prime import default_data


@functools.lru_cache()
def default_prime2_resource_database() -> ResourceDatabase:
    return read_resource_database(default_data.decode_default_prime2()["resource_database"])


@functools.lru_cache()
def default_prime2_pickup_database() -> PickupDatabase:
    return read_pickup_database(default_data.decode_default_prime2()["pickup_database"],
                                default_prime2_resource_database())


def default_prime2_game_description(add_self_as_requirement_to_resources: bool = True,
                                    ) -> GameDescription:
    return data_reader.decode_data(default_data.decode_default_prime2(), add_self_as_requirement_to_resources)
