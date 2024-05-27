import json
import math
import re
import typing
from pathlib import Path

import networkx

from tools.factorio import util

_custom_tech = [
    # custom tech
    "long-handed-inserter",
    "longer-handed-inserter",
    "oil-cracking",
    "solid-fuel",
    "light-armor",
    "big-electric-pole",
    "inserter",
    "steam-power",
    "automation-science-pack",
    "regular-inserter-capacity-bonus",
    "stack-inserter-capacity-bonus",
    "research-productivity",
]

_upgrade_techs_templates = {
    "refined-flammables-{}": 6,
    "energy-weapons-damage-{}": 6,
    "stronger-explosives-{}": 6,
    "laser-shooting-speed-{}": 7,
    "follower-robot-count-{}": 6,
    "weapon-shooting-speed-{}": 6,
    "physical-projectile-damage-{}": 6,
    "inserter-capacity-bonus-{}": 7,
    "braking-force-{}": 7,
}
_base_upgrade_tiers = 2
_bonus_upgrade_tech = [
    template.format(i + 1)
    for template, max_tier in _upgrade_techs_templates.items()
    for i in range(_base_upgrade_tiers, max_tier)
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


def make_pickup(index: int, *, is_major: bool = False, connections=None) -> dict[str, typing.Any]:
    return {
        "node_type": "pickup",
        **make_node_base(),
        "pickup_index": index,
        "location_category": "major" if is_major else "minor",
        "connections": connections or {},
    }


def complexity_for(tech: dict) -> int:
    pack_count = len(tech["unit"]["ingredients"])
    raw_cost = math.floor(tech["unit"]["count"] * tech["unit"]["time"] * math.sqrt(pack_count))
    return math.floor(math.log(raw_cost)) - 3


def _load_existing_ids(region_path: Path) -> dict[str, int]:
    try:
        with region_path.open() as f:
            return {
                node: node_data["pickup_index"]
                for node, node_data in json.load(f)["areas"]["Tech Tree"]["nodes"].items()
                if node_data["node_type"] == "pickup"
            }

    except FileNotFoundError:
        return {}


def make_gen_id(existing_ids: dict[str, int]) -> typing.Callable[[], int]:
    used_ids = set(existing_ids.values())

    def gen_id() -> int:
        global current_pickup_index
        current_pickup_index += 1
        while current_pickup_index in used_ids:
            current_pickup_index += 1
        return current_pickup_index

    return gen_id


def main():
    factorio_path = Path(r"F:/Factorio_1.1.91-rdv-mod")
    rdv_factorio_path = Path(__file__).parents[2].joinpath("randovania/games/factorio")
    region_path = rdv_factorio_path.joinpath("logic_database/Tech.json")

    util.read_locales(factorio_path)

    raw_dump_path = factorio_path.joinpath("script-output/data-raw-dump.json")

    with raw_dump_path.open() as f:
        raw_dump: dict[str, dict[str, typing.Any]] = json.load(f)

    techs_raw = {key: value for key, value in raw_dump["technology"].items() if not key.startswith("randovania-")}

    existing_ids = _load_existing_ids(region_path)
    gen_id = make_gen_id(existing_ids)

    graph = networkx.DiGraph()
    pack_for_tech = {}
    pickup_nodes = {}

    for tech_name, tech in techs_raw.items():
        if tech_name in _custom_tech:
            continue

        packs = tuple(sorted(it[0] for it in tech["unit"]["ingredients"]))
        if "space-science-pack" in packs:
            continue

        graph.add_node(tech_name)

        pack_for_tech[tech_name] = packs
        for it in tech.get("prerequisites", []):
            graph.add_edge(it, tech_name)

    for tech_name in networkx.topological_sort(graph):
        new_tech = re.sub(r"-(\d+)$", lambda m: f"-{chr(ord('a') + int(m.group(1)))}", tech_name)

        pickup_nodes[tech_name] = {
            "node_name": f"Pickup ({util.get_localized_name(tech_name)})",
            "tech_name": f"randovania-{new_tech}",
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
        if node_details["node_name"] in existing_ids:
            new_id = existing_ids[node_details["node_name"]]
        else:
            new_id = gen_id()
        node = make_pickup(new_id, is_major=True)
        node["extra"]["original_tech"] = tech_name
        node["extra"]["tech_name"] = node_details["tech_name"]
        node["extra"]["count"] = techs_raw[tech_name]["unit"]["count"]
        node["extra"]["time"] = techs_raw[tech_name]["unit"]["time"]
        node["extra"]["ingredients"] = pack_for_tech[tech_name]
        if tech_name in _bonus_upgrade_tech:
            node["layers"] = ["full_tree"]
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

    node_order = list(nodes)
    for node in nodes.values():
        node["connections"] = {
            target: node["connections"][target]
            for target in sorted(node["connections"], key=lambda n: node_order.index(n))
        }

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
