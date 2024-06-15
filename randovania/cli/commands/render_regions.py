from __future__ import annotations

import argparse
from argparse import ArgumentParser
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace


def render_region_graph_logic(args: Namespace) -> None:
    import hashlib
    import re

    import graphviz  # type: ignore

    from randovania.game_description import default_database
    from randovania.game_description.db.dock_node import DockNode
    from randovania.game_description.db.pickup_node import PickupNode
    from randovania.game_description.requirements.base import Requirement
    from randovania.games.game import RandovaniaGame

    gd = default_database.game_description_for(RandovaniaGame(args.game))

    regions = list(gd.region_list.regions)

    single_image: bool = args.single_image
    added_edges = set()
    vulnerabilities_colors = {
        "Normal Door": None,
        "Morph Ball Door": None,
        "Other Door": None,
        "Scan Portal": None,
        "Missile": "#ff1919",
        "Super Missile": "#38c914",
        "Seeker Launcher": "#b233e8",
        "Power Bomb": "#dfe833",
        "Wave Door": "#a30af5",
        "Ice Door": "#7cdede",
        "Plasma Door": "#870f0f",
        "Light Door": "#bfd9d9",
        "Dark Door": "#3b3647",
        "Annihilator Door": "#616969",
        "Light Portal": "#bfd9d9",
        "Dark Portal": "#3b3647",
    }

    def _weakness_name(s: str) -> str:
        return re.sub(r"\([^)]*\)", "", s).replace(" Blast Shield", "").strip()

    def _hash_to_color(s: str) -> str:
        h = hashlib.blake2b(s.encode("utf-8"), digest_size=3).digest()
        return "#{:06x}".format(int.from_bytes(h, "big"))

    def _add_connection(dot: graphviz.Digraph, dock_node: DockNode) -> None:
        the_region = gd.region_list.nodes_to_region(dock_node)
        source_area = gd.region_list.nodes_to_area(dock_node)
        target_node = gd.region_list.node_by_identifier(dock_node.default_connection)
        target_area = gd.region_list.nodes_to_area(target_node)

        if dock_node.default_dock_weakness.requirement == Requirement.impossible():
            return

        if dock_node.identifier in added_edges:
            return

        weak_name = _weakness_name(dock_node.default_dock_weakness.name)
        direction = None
        if isinstance(target_node, DockNode) and _weakness_name(target_node.default_dock_weakness.name) == weak_name:
            direction = "both"
            added_edges.add(target_node.identifier)

        color = vulnerabilities_colors.get(weak_name, _hash_to_color(weak_name))
        dot.edge(
            f"{the_region.name}-{source_area.name}",
            f"{the_region.name}-{target_area.name}",
            weak_name,
            dir=direction,
            color=color,
            fontcolor=color,
        )
        added_edges.add(dock_node.identifier)

    def _add_teleporter(dot: graphviz.Digraph, teleporter_node: DockNode) -> None:
        source_region = gd.region_list.nodes_to_region(teleporter_node)
        source_area = gd.region_list.nodes_to_area(teleporter_node)
        target_node = gd.region_list.node_by_identifier(teleporter_node.default_connection)
        target_region = gd.region_list.nodes_to_region(target_node)
        target_area = gd.region_list.nodes_to_area(target_node)
        weak_name = _weakness_name(teleporter_node.default_dock_weakness.name)
        color = vulnerabilities_colors.get(weak_name, _hash_to_color(weak_name))

        dot.edge(
            f"{source_region.name}-{source_area.name}",
            f"{target_region.name}-{target_area.name}",
            weak_name,
            color=color,
            fontcolor=color,
        )

    def _cross_region_dock(node: DockNode) -> bool:
        return node.default_connection.region != node.identifier.region

    per_game_colors = {
        RandovaniaGame.METROID_PRIME_ECHOES: {
            "Agon Wastes": "#ffc61c",
            "Torvus Bog": "#20ff1c",
            "Sanctuary Fortress": "#3d62ff",
            "Temple Grounds": "#c917ff",
            "Great Temple": "#c917ff",
        },
    }
    colors = per_game_colors.get(gd.game)
    if colors is None:
        colors = {region.name: _hash_to_color(region.name) for region in gd.region_list.regions}

    dark_colors = {
        "Agon Wastes": "#a88332",
        "Torvus Bog": "#149612",
        "Sanctuary Fortress": "#112991",
        "Temple Grounds": "#7d2996",
        "Great Temple": "#7d2996",
    }

    if single_image:
        full_dot = graphviz.Digraph(name=gd.game.short_name, comment=gd.game.long_name)
    else:
        full_dot = None
    per_region_dot = {}

    for region in regions:
        if single_image:
            this_dot = full_dot
        else:
            this_dot = graphviz.Digraph(name=region.name)

        per_region_dot[region.name] = this_dot

        for area in region.areas:
            shape = None
            if any(isinstance(node, DockNode) and _cross_region_dock(node) for node in area.nodes):
                shape = "polygon"

            c = (dark_colors if area.in_dark_aether else colors)[region.name]
            fillcolor = "".join(f"{max(0, int(c[i * 2 + 1:i * 2 + 3], 16) - 64):02x}" for i in range(3))
            this_dot.node(
                f"{region.name}-{area.name}",
                area.name,
                color=c,
                fillcolor=f"#{fillcolor}",
                style="filled",
                fontcolor="#ffffff",
                shape=shape,
                penwidth="3.0",
            )

            for node in area.nodes:
                if args.include_pickups and isinstance(node, PickupNode):
                    re_result = re.search(r"Pickup [^(]*\(([^)]+)\)", node.name)
                    assert re_result is not None
                    this_dot.node(str(node.pickup_index), re_result.group(1), shape="house")
                    this_dot.edge(f"{region.name}-{area.name}", str(node.pickup_index))

    for region in regions:
        print(f"Adding docks for {region.name}")
        for area in region.areas:
            for node in area.nodes:
                if isinstance(node, DockNode) and not _cross_region_dock(node):
                    _add_connection(per_region_dot[region.name], node)
                elif isinstance(node, DockNode) and _cross_region_dock(node) and args.include_teleporters:
                    _add_teleporter(per_region_dot[region.name], node)

    if single_image:
        full_dot.render(format="png", view=True, cleanup=True)
    else:
        for name, this_dot in per_region_dot.items():
            this_dot.render(format="png", view=True, cleanup=True)


def render_regions_graph(sub_parsers: argparse._SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser(
        "render-region-graph",
        help="Renders an image with all area connections",
        formatter_class=argparse.MetavarTypeHelpFormatter,
    )
    parser.add_argument("--include-teleporters", action="store_true")
    parser.add_argument("--include-pickups", action="store_true")
    parser.add_argument("--single-image", action="store_true")

    parser.set_defaults(func=render_region_graph_logic)
