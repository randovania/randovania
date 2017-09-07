import collections
import json

PointOfInterest = collections.namedtuple("PointOfInterest", ["paths", "items"])
Path = collections.namedtuple("Path", ["target", "requirements"])


requirement_for_connection_type = {
    "cutscene": frozenset([]),
    "blue_door": frozenset([]),
}


class World:
    def __init__(self, points_of_interest, starting_point):
        self.points_of_interest = points_of_interest
        self.starting_point = starting_point

    @classmethod
    def from_file(cls, filepath):
        with open(filepath) as f:
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
                    frozenset(location.get("items", []))
                )

        return cls(points, "TempleHub/01_Temple_LandingSite/ship")

    def paths_for_point(self, point):
        return self.points_of_interest[point].paths

    def items_for_point(self, point):
        return self.points_of_interest[point].items
