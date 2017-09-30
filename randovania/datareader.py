import pprint
import struct
import typing
from typing import List


class RequirementInfo(typing.NamedTuple):
    index: int
    long_name: str
    short_name: str


class DamageReduction(typing.NamedTuple):
    inventory_index: int
    damage_multiplier: float


class DamageRequirementInfo(typing.NamedTuple):
    index: int
    long_name: str
    short_name: str
    reductions: List[DamageReduction]


class IndividualRequirement(typing.NamedTuple):
    requirement_type: int
    requirement_index: int
    amount: int
    negate: bool


class DockWeakness(typing.NamedTuple):
    index: int
    name: str
    requirements_set: List[List[IndividualRequirement]]


def read_byte(file) -> int:
    return struct.unpack("!B", file.read(1))[0]


def read_short(file) -> int:
    return struct.unpack("!H", file.read(2))[0]


def read_float(file) -> float:
    return struct.unpack("!f", file.read(4))[0]


def read_bool(file) -> bool:
    return struct.unpack("!?", file.read(1))[0]


def read_string(file) -> str:
    chars = []
    while True:
        c = file.read(1)
        if c[0] == 0:
            return b"".join(chars).decode("UTF-8")
        chars.append(c)


def read_array(x, item_reader):
    count = read_byte(x)
    return [
        item_reader(x)
        for _ in range(count)
    ]


def read_damage_reduction(x) -> DamageReduction:
    index = read_byte(x)
    multiplier = read_float(x)
    return DamageReduction(index, multiplier)


def read_damage_reductions(x) -> List[DamageReduction]:
    return read_array(x, read_damage_reduction)


def read_requirement_info(x) -> RequirementInfo:
    index = read_byte(x)
    long_name = read_string(x)
    short_name = read_string(x)
    return RequirementInfo(index, long_name, short_name)


def read_requirement_info_array(x) -> List[RequirementInfo]:
    return read_array(x, read_requirement_info)


def read_damagerequirement_info(x) -> DamageRequirementInfo:
    index = read_byte(x)
    long_name = read_string(x)
    short_name = read_string(x)
    return DamageRequirementInfo(index, long_name, short_name, read_damage_reductions(x))


def read_damagerequirement_info_array(x) -> List[DamageRequirementInfo]:
    return read_array(x, read_damagerequirement_info)


def read_individual_requirement(x) -> IndividualRequirement:
    requirement_type = read_byte(x)
    requirement_index = read_byte(x)
    amount = read_short(x)
    negate = read_bool(x)
    return IndividualRequirement(requirement_type, requirement_index, amount, negate)


def read_requirement_list(x) -> List[IndividualRequirement]:
    return read_array(x, read_individual_requirement)


def read_requirement_set(x) -> List[List[IndividualRequirement]]:
    return read_array(x, read_requirement_list)


def read_dock_weakness(x) -> DockWeakness:
    index = read_byte(x)
    name = read_string(x)
    requirement_set = read_requirement_set(x)
    return DockWeakness(index, name, requirement_set)


def read_dock_weakness_list(x) -> List[DockWeakness]:
    return read_array(x, read_dock_weakness)


def read(path):
    with open(path, "rb") as x:
        if x.read(4) != b"Req.":
            raise Exception("Invalid file format.")

        format_version, game = struct.unpack("!IB", x.read(5))
        game_name = read_string(x)

        print("Format Version: {}\nGame: {}\nGame Name: {}".format(
            format_version, game, game_name
        ))

        items = read_requirement_info_array(x)
        events = read_requirement_info_array(x)
        tricks = read_requirement_info_array(x)
        damage = read_damagerequirement_info_array(x)
        difficulty = read_requirement_info_array(x)
        # File seems to have a mistake here.
        read_byte(x)
        read_string(x)
        read_string(x)
        # misc = read_requirement_info_array(x))
        versions = read_requirement_info_array(x)

        # pprint.pprint(items)
        # pprint.pprint(events)
        # pprint.pprint(tricks)
        # pprint.pprint(damage)
        # pprint.pprint(versions)
        # pprint.pprint(misc)
        # pprint.pprint(difficulty)

        door_types = read_dock_weakness_list(x)
        portal_types = read_dock_weakness_list(x)

        # pprint.pprint(door_types)
        # pprint.pprint(portal_types)

        print(x.read(80))
        print(x.read(80))
        print(x.read(80))
        print(x.read(80))


if __name__ == "__main__":
    import sys
    read(sys.argv[1])
