import dataclasses
import os
from collections import Counter
from pathlib import Path

from open_prime_rando.echoes.dock_lock_rando.dock_type_database import DOCK_TYPES
from open_prime_rando.patcher_editor import IsoFileProvider, PatcherEditor
from retro_data_structures.enums.echoes import Message, State
from retro_data_structures.formats.scan import Scan
from retro_data_structures.formats.script_object import Connection, ScriptInstance
from retro_data_structures.game_check import Game
from retro_data_structures.properties.echoes.objects import Actor, Dock, PointOfInterest, ScannableObjectInfo

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import data_writer, default_database, pretty_print
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.db.node import NodeLocation
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.editor import Editor
from randovania.games.prime2.exporter.patch_data_factory import _asset_id_for_region

patcher_editor = PatcherEditor(IsoFileProvider(Path(os.environ["PRIME2_ISO"])), Game.ECHOES)


game = default_database.game_description_for(RandovaniaGame.METROID_PRIME_ECHOES_OPR)
db_editor = Editor(game)

results: dict[NodeIdentifier, NodeLocation] = {}

door_type = DOCK_TYPES["Normal"]


def get_location(instance: ScriptInstance) -> NodeLocation:
    x, y, z = instance.editor_properties.transform.position
    return NodeLocation(x, y, z)


for region, area, node in game.iterate_nodes_of_type(DockNode, PickupNode, HintNode):
    print(node.identifier)

    mlvl_id = _asset_id_for_region(game.region_list, region)
    mrea_id = area.extra["asset_id"]

    rds_area = patcher_editor.get_area(mlvl_id, mrea_id)

    if isinstance(node, DockNode):
        if "dock_name" in node.extra:
            dock_name = node.extra["dock_name"]
            dock = next(inst for inst in rds_area.all_instances if inst.script_type == Dock and inst.name == dock_name)
            results[node.identifier] = get_location(dock)
        elif "teleporter_instance_id" in node.extra:
            teleporter = rds_area.get_instance(node.extra["teleporter_instance_id"])
            results[node.identifier] = get_location(teleporter)

    elif isinstance(node, PickupNode):
        if node.location is not None:
            continue
        try:
            pickup_id = node.extra["location_data"]["instances"]["pickup"]
        except KeyError:
            continue
        pickup = rds_area.get_instance(pickup_id)
        results[node.identifier] = get_location(pickup)

    elif isinstance(node, HintNode):
        if "string_asset_id" not in node.extra:
            continue
        strg_id = node.extra["string_asset_id"]
        for instance in rds_area.all_instances:
            position_instance: ScriptInstance

            if instance.script_type == Actor:
                actor = instance.get_properties_as(Actor)
                position_instance = instance
                scan_asset = actor.actor_information.scannable.scannable_info0

            elif instance.script_type == PointOfInterest:
                poi = instance.get_properties_as(PointOfInterest)
                position_instance = instance
                scan_asset = poi.scan_info.scannable_info0
                actor_inst = next(
                    (
                        inst
                        for inst in rds_area.all_instances
                        if Connection(State.ScanSource, Message.Attach, instance.id) in inst.connections
                    ),
                    None,
                )
                if actor_inst is None:
                    position_instance = actor_inst
            else:
                continue

            if scan_asset == 0xFFFFFFFF:
                continue

            scan = patcher_editor.get_file(scan_asset, Scan)
            scan_info = scan.scannable_object_info.get_properties_as(ScannableObjectInfo)
            if scan_info.string == strg_id:
                results[node.identifier] = get_location(position_instance)
                break


for identifier, location in results.items():
    node = game.node_by_identifier(identifier)
    area = game.area_from_node(node)

    db_editor.replace_node(
        area,
        node,
        dataclasses.replace(
            node,
            location=location,
        ),
    )


data = data_writer.write_game_description(game)
data_path = RandovaniaGame.METROID_PRIME_ECHOES_OPR.data_path.joinpath("logic_database")

data_path.with_suffix("").mkdir(exist_ok=True)
data_writer.write_as_split_files(data, data_path.with_suffix(""))

pretty_print.write_human_readable_game(game, data_path.with_suffix(""))
default_database.game_description_for.cache_clear()

nodes_with_location: Counter[str] = Counter()
nodes_without_location: Counter[str] = Counter()

for _, _, node in game.node_iterator():
    if node.location is None:
        nodes_without_location[node.__class__.__name__] += 1
    else:
        nodes_with_location[node.__class__.__name__] += 1


print("Nodes without location:", nodes_without_location)
print("Nodes with location:", nodes_with_location)

coverage = sum(nodes_with_location.values()) / (
    sum(nodes_with_location.values()) + sum(nodes_without_location.values())
)
print(f"Location coverage: {coverage:.2%}")
