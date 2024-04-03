import collections
import json
import math
import string
import typing
from pathlib import Path

import networkx

_techs_to_ignore = [
    # custom tech
    "long-handed-inserter",
    "oil-cracking",
    "solid-fuel",
    "light-armor",
    "big-electric-pole",
    "inserter",
    "steam-power",
    "automation-science-pack",
    "regular-inserter-capacity-bonus",
    # repeatable upgrade tech
    *[f"refined-flammables-{i + 1}" for i in range(2, 6)],
    *[f"energy-weapons-damage-{i + 1}" for i in range(2, 6)],
    *[f"stronger-explosives-{i + 1}" for i in range(2, 6)],
    *[f"laser-shooting-speed-{i + 1}" for i in range(2, 7)],
    *[f"follower-robot-count-{i + 1}" for i in range(2, 6)],
    *[f"weapon-shooting-speed-{i + 1}" for i in range(2, 6)],
    *[f"physical-projectile-damage-{i + 1}" for i in range(2, 6)],
    *[f"inserter-capacity-bonus-{i + 1}" for i in range(2, 7)],
    *[f"braking-force-{i + 1}" for i in range(2, 7)],
]

trivial_req = {"type": "and", "data": {"comment": None, "items": []}}
areas = {
    "Tech Tree": {
        "default_node": None,
        "extra": {},
        "nodes": {
            "Spawn Point": {
                "node_type": "generic",
                "heal": False,
                "coordinates": None,
                "description": "",
                "layers": ["default"],
                "extra": {},
                "valid_starting_location": True,
                "connections": {},
            }
        },
    }
}


def make_node_base(extra=None):
    return {
        "heal": False,
        "coordinates": None,
        "description": "",
        "layers": ["default"],
        "extra": extra or {},
        "valid_starting_location": False,
    }


def make_dock(target_area: str, target_node: str, connections=None):
    return {
        "node_type": "dock",
        **make_node_base(),
        "dock_type": "Connection",
        "default_connection": {"region": "Tech", "area": target_area, "node": target_node},
        "default_dock_weakness": "Standard",
        "exclude_from_dock_rando": False,
        "incompatible_dock_weaknesses": [],
        "override_default_open_requirement": None,
        "override_default_lock_requirement": None,
        "connections": connections or {},
    }


current_pickup_index = -1


def make_pickup(*, is_major: bool = False, connections=None) -> dict[str, typing.Any]:
    global current_pickup_index
    current_pickup_index += 1
    return {
        "node_type": "pickup",
        **make_node_base(),
        "pickup_index": current_pickup_index,
        "location_category": "major" if is_major else "minor",
        "connections": connections or {},
    }


def get_letter_combo(index: int) -> str:
    first = index // len(string.ascii_lowercase)
    second = index % len(string.ascii_lowercase)
    return string.ascii_lowercase[first] + string.ascii_lowercase[second]


def complexity_for(tech: dict) -> int:
    pack_count = len(tech["unit"]["ingredients"])
    raw_cost = math.floor(tech["unit"]["count"] * tech["unit"]["time"] * math.sqrt(pack_count))
    return math.floor(math.log(raw_cost)) - 3


def main():
    factorio_path = Path(r"F:/Factorio_1.1.91-rdv-mod")
    rdv_factorio_path = Path(__file__).parents[2].joinpath("randovania/games/factorio")
    region_path = rdv_factorio_path.joinpath("logic_database/Tech.json")

    raw_dump_path = factorio_path.joinpath("script-output/data-raw-dump.json")

    with raw_dump_path.open() as f:
        raw_dump: dict[str, dict[str, typing.Any]] = json.load(f)

    techs_raw = {key: value for key, value in raw_dump["technology"].items() if not key.startswith("randovania-")}

    graph = networkx.DiGraph()
    techs_by_pack = collections.defaultdict(int)
    pack_for_tech = {}
    last_letter_for_pack_combo = {}
    pickup_nodes = {}

    for tech_name, tech in techs_raw.items():
        if tech_name in _techs_to_ignore:
            continue

        packs = tuple(sorted(it[0] for it in tech["unit"]["ingredients"]))
        if "space-science-pack" in packs:
            continue

        graph.add_node(tech_name)

        pack_for_tech[tech_name] = packs
        for it in tech.get("prerequisites", []):
            graph.add_edge(it, tech_name)

    for tech_name in networkx.topological_sort(graph):
        pack = pack_for_tech[tech_name]
        pack_letters = "".join(it[0] for it in pack)
        letter = get_letter_combo(techs_by_pack[pack])
        techs_by_pack[pack] += 1

        last_letter_for_pack_combo[pack_letters] = letter
        pickup_nodes[tech_name] = {
            "node_name": f"Pickup ({pack_letters.upper()} {techs_by_pack[pack]})",
            "tech_name": f"randovania-{pack_letters.lower()}-{letter}",
            "complexity": complexity_for(techs_raw[tech_name]),
        }

    def requirement_for_tech(n: str):
        # code = "".join(it[0] for it in pack_for_tech[n]).upper()
        # print(f"{n:40} {cost_complexity:10d} -- {code:>6} x{tech['unit']['count']:<6} @ {tech['unit']['time']}s")

        items = [{"type": "template", "data": f"craft-{pack.lower()}"} for pack in pack_for_tech[n]]
        complexity = pickup_nodes[n]["complexity"]
        items.append({"type": "template", "data": f"tech-tier-{complexity}"})

        return {
            "type": "and",
            "data": {
                "comment": None,
                "items": items,
            },
        }

    # count_per_tier = collections.defaultdict(int)
    #
    # for tech_name in sorted(pickup_nodes, key=lambda it: pickup_nodes[it]["complexity"]):
    #     tech = techs_raw[tech_name]
    #     base = pickup_nodes[tech_name]["complexity"]
    #     cost_complexity = math.floor(math.log(base)) - 3
    #     code = "".join(it[0] for it in pack_for_tech[tech_name]).upper()
    #     count_per_tier[cost_complexity] += 1
    #     unit = tech['unit']
    #     print(f"{tech_name:40} {base:10d} ({cost_complexity:2d}) -- {code:>6} x{unit['count']:<6} @ {unit['time']}s")
    #
    # pprint.pp(dict(count_per_tier.items()), width=10)

    the_area = areas["Tech Tree"]
    nodes: dict[str, dict[str, typing.Any]] = the_area["nodes"]

    for tech_name in networkx.topological_sort(graph):
        node_details = pickup_nodes[tech_name]
        node = make_pickup(is_major=True)
        node["extra"]["original_tech"] = tech_name
        node["extra"]["tech_name"] = node_details["tech_name"]
        node["extra"]["count"] = techs_raw[tech_name]["unit"]["count"]
        node["extra"]["time"] = techs_raw[tech_name]["unit"]["time"]
        node["extra"]["ingredients"] = pack_for_tech[tech_name]
        nodes[node_details["node_name"]] = node

    for tech_name in networkx.topological_sort(graph):
        node_name = pickup_nodes[tech_name]["node_name"]
        node = nodes[node_name]

        if "prerequisites" in techs_raw[tech_name]:
            previous_nodes = [pickup_nodes[it]["node_name"] for it in techs_raw[tech_name]["prerequisites"]]
        else:
            previous_nodes = ["Spawn Point"]

        requirement = requirement_for_tech(tech_name)
        if len(previous_nodes) > 1:
            requirement["data"]["items"].extend(
                [{"type": "node", "data": {"region": "Tech", "area": "Tech Tree", "node": it}} for it in previous_nodes]
            )

        for previous_node in previous_nodes:
            node["connections"][previous_node] = trivial_req
            nodes[previous_node]["connections"][node_name] = requirement

    with region_path.open("w") as f:
        json.dump(
            {
                "name": "Tech",
                "extra": {},
                "areas": areas,
            },
            f,
            indent=4,
        )


if __name__ == "__main__":
    main()
