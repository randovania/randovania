import collections


def calculate_reach(world, items, origin):
    items = frozenset(items)
    points_to_check = {origin}
    checked_rooms = set()

    while points_to_check:
        point = points_to_check.pop()
        checked_rooms |= {point}
        for path in world.paths_for_point(point):
            if path.target in checked_rooms:
                # This path is a loop, ignore
                continue
            if path.requirements <= items:
                points_to_check |= {path.target}

    return frozenset(checked_rooms)


def accessible_items(world, reach):
    items = collections.defaultdict(set)
    for point in reach:
        for item in world.items_for_point(point):
            items[item] |= {point}
    return {
        item: frozenset(points)
        for item, points in items.items()
    }
