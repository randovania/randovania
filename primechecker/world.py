import collections
import json

PointOfInterest = collections.namedtuple("PointOfInterest", ["paths", "items"])
Path = collections.namedtuple("Path", ["target", "requirements"])


requirement_for_connection_type = {
    "cutscene": frozenset([]),
    "blue_door": frozenset([]),
}


def item_for_slot(item_slot):
    return item_slot


class World:
    def __init__(self, points_of_interest, starting_point):
        if starting_point not in points_of_interest:
            raise Exception("Starting point is not a valid point of interest.")
        self.points_of_interest = points_of_interest
        self.starting_point = starting_point

    @classmethod
    def from_file(cls, game_data_file):
        with open(game_data_file) as f:
            data = json.load(f)

        points = {}
        for room_name, room in data["rooms"].items():
            for location_name, location in room["locations"].items():
                paths = []
                for target_location, requirement_options in location["paths"].items():
                    for requirement in requirement_options:
                        paths.append(Path(
                            "{}/{}".format(room_name, target_location),
                            frozenset(requirement["requirements"])
                        ))
                if "connects_to" in location:
                    paths.append(Path(
                        location["connects_to"],
                        requirement_for_connection_type[location["type"]],
                    ))
                points["{}/{}".format(room_name, location_name)] = PointOfInterest(
                    paths,
                    frozenset([
                        item_for_slot(item_slot)
                        for item_slot in location.get("items", [])
                    ])
                )

        return cls(points, data["starting_point"])

    def paths_for_point(self, point):
        return self.points_of_interest[point].paths

    def items_for_point(self, point):
        return self.points_of_interest[point].items
