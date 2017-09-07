

class Reach:
    def __init__(self, world):
        self.world = world
        self.reach = frozenset([world.starting_point])

    def expand(self, items):
        items = frozenset(items)
        points_to_check = set(self.reach)
        checked_rooms = set()

        print("Starting with points:", points_to_check)
        while points_to_check:
            point = points_to_check.pop()
            print("Loop start", point, checked_rooms)
            checked_rooms |= {point}
            for path in self.world.paths_for_point(point):
                print("Possible path", path)
                if path.target in checked_rooms:
                    # This path is a loop, ignore
                    continue
                if path.requirements <= items:
                    points_to_check |= {path.target}

        assert checked_rooms >= self.reach, "Expand call should not reduce reachability"
        self.reach = frozenset(checked_rooms)

    def accessible_items(self):
        items = set()
        for point in self.reach:
            items |= set(self.world.items_for_point(point))
        return items

