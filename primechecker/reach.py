

def expand_reach(world, items, current_reach):
    items = frozenset(items)
    points_to_check = set(current_reach)
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
    items = set()
    for point in reach:
        items |= set(world.items_for_point(point))
    return items

