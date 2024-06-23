import json
import math
import re
import typing
from pathlib import Path

import networkx

from tools.factorio import util
from tools.factorio.util import and_req, tech_req, template_req

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


_k_tier_requirements = [
    [],  # 1
    [],
    [template_req("craft-transport-belt")],
    [
        template_req("craft-assembling-machine-1"),
        template_req("craft-inserter"),
        template_req("has-electricity"),
    ],  # TODO: electric lab, drills
    [
        template_req("craft-fast-transport-belt"),
        template_req("craft-fast-inserter"),
        tech_req("railway"),
    ],  # TODO: fast smelting
    [tech_req("construction-robotics"), template_req("craft-assembling-machine-2")],
    [template_req("craft-stack-inserter")],
    [tech_req("research-speed-6"), template_req("craft-assembling-machine-3")],
    [tech_req("logistic-system")],
    [tech_req("productivity-module-3")],
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
        "ui_custom_name": None,
        "connections": connections or {},
    }


for tier, req in enumerate(_k_tier_requirements):
    areas["Tech Tree"]["nodes"][f"Connection to Tier {tier + 1}"] = make_dock(
        f"Tier {tier + 1}", "Connection to Tech Tree", {"Spawn Point": trivial_req}
    )
    areas["Tech Tree"]["nodes"]["Spawn Point"]["connections"][f"Connection to Tier {tier + 1}"] = and_req(req)
    areas[f"Tier {tier + 1}"] = {
        "default_node": None,
        "extra": {},
        "nodes": {"Connection to Tech Tree": make_dock("Tech Tree", f"Connection to Tier {tier + 1}")},
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
            all_areas = json.load(f)["areas"]
    except FileNotFoundError:
        return {}

    result = {}

    for area in all_areas.values():
        for node_data in area["nodes"].values():
            if node_data["node_type"] == "pickup":
                result[node_data["extra"]["original_tech"]] = node_data["pickup_index"]

    return result


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

    for tech_name in networkx.topological_sort(graph):
        node_details = pickup_nodes[tech_name]
        if tech_name in existing_ids:
            new_id = existing_ids[tech_name]
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
        areas[f"Tier {node_details['complexity']}"]["nodes"][node_details["node_name"]] = node

    for tech_name in networkx.topological_sort(graph):
        node_name = pickup_nodes[tech_name]["node_name"]
        nodes = areas[f"Tier {pickup_nodes[tech_name]['complexity']}"]["nodes"]
        node = nodes[node_name]

        if "prerequisites" in techs_raw[tech_name]:
            previous_nodes = [pickup_nodes[it] for it in techs_raw[tech_name]["prerequisites"]]
        else:
            previous_nodes = []

        requirement = requirement_for_tech(tech_name)
        requirement["data"]["items"].extend(
            [
                {
                    "type": "node",
                    "data": {"region": "Tech", "area": f"Tier {it['complexity']}", "node": it["node_name"]},
                }
                for it in previous_nodes
            ]
        )

        node["connections"]["Connection to Tech Tree"] = trivial_req
        nodes["Connection to Tech Tree"]["connections"][node_name] = requirement

    for area in areas.values():
        node_order = list(area["nodes"])
        for node in area["nodes"].values():
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
