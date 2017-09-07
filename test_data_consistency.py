import json
import re


class Validator:
    def __init__(self, paths):
        self.paths = paths
        self.pretty_names = {}
        self.errors = []

    def validate_name(self, room_name):
        if not re.match(r"^[a-zA-Z0-9_]+/[a-zA-Z0-9_]+$", room_name):
            self.errors.append("Invalid room name: {}".format(room_name))

    def validate_pretty_name(self, room_name, pretty_name):
        if pretty_name is None:
            self.errors.append("Room {} is missing pretty_name.".format(room_name))
        elif pretty_name in self.pretty_names:
            self.errors.append("Conflicting pretty_name '{0}': Rooms '{1}' and '{2}'".format(
                pretty_name,
                self.pretty_names[pretty_name],
                room_name))
        else:
            self.pretty_names[pretty_name] = room_name

    def validate_location(self, room_name, location_name, location_config):
        connects_to = location_config.get("connects_to")
        if connects_to:
            match = re.match(r"^([a-zA-Z0-9_]+/[a-zA-Z0-9_]+)/([a-zA-Z0-9_]+)$", connects_to)
            if match:
                target_room, target_location = match.group(1, 2)
                target_room_config = self.paths["rooms"].get(target_room)
                if target_room_config:
                    if target_location not in target_room_config["locations"]:
                        self.errors.append(
                            "Room '{0}' has no location '{1}', required by connection in room '{2}'.".format(
                                target_room, target_location, room_name
                            ))
                else:
                    self.errors.append("Room '{0}', location '{1}' connects to unknown room '{2}'.".format(
                        room_name, location_name, target_room
                    ))
            else:
                self.errors.append("Room '{0}', location '{1}' has invalid connects_to '{2}'.".format(
                    room_name, location_name, connects_to
                ))

    def validate_room(self, room_name, room_config):
        self.validate_name(room_name)
        self.validate_pretty_name(room_name, room_config.get("pretty_name"))
        for location_name, location_config in room_config["locations"].items():
            self.validate_location(room_name, location_name, location_config)


def main():
    with open("paths.json") as f:
        paths = json.load(f)

    validator = Validator(paths)
    for room_name, room_config in paths["rooms"].items():
        validator.validate_room(room_name, room_config)

    if validator.errors:
        print("Found errors in config:\n* {}".format(
            "\n* ".join(validator.errors)
        ))
    else:
        print("No error found.")


if __name__ == "__main__":
    main()
