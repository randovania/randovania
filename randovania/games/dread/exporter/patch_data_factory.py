import logging
import os
from typing import Optional, Union

from randovania.exporter import pickup_exporter, item_names
from randovania.exporter.hints.hint_exporter import HintExporter
from randovania.exporter.patch_data_factory import BasePatchDataFactory
from randovania.exporter.pickup_exporter import ExportedPickupDetails
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import ConditionalResources
from randovania.game_description.resources.resource_info import ResourceCollection
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.logbook_node import LogbookNode
from randovania.game_description.world.node import Node
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.games.dread.exporter.hint_namer import DreadHintNamer
from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.games.dread.layout.dread_cosmetic_patches import DreadCosmeticPatches
from randovania.games.game import RandovaniaGame
from randovania.generator.item_pool import pickup_creator

_ALTERNATIVE_MODELS = {
    "powerup_slide": "itemsphere",
    "powerup_hyperbeam": "powerup_plasmabeam",
    "powerup_metroidsuit": "powerup_gravitysuit",

    "PROGRESSIVE_BEAM": "powerup_widebeam",
    "PROGRESSIVE_CHARGE": "powerup_chargebeam",
    "PROGRESSIVE_MISSILE": "powerup_supermissile",
    "PROGRESSIVE_SUIT": "powerup_variasuit",
    "PROGRESSIVE_BOMB": "powerup_bomb",
    "PROGRESSIVE_SPIN": "powerup_doublejump",
}


def _get_item_id_for_item(item: ItemResourceInfo) -> str:
    if "item_capacity_id" in item.extra:
        return item.extra["item_capacity_id"]
    try:
        return item.extra["item_id"]
    except KeyError as e:
        raise KeyError(f"{item.long_name} has no item ID.") from e


class DreadPatchDataFactory(BasePatchDataFactory):
    cosmetic_patches: DreadCosmeticPatches
    configuration: DreadConfiguration

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memo_data = DreadAcquiredMemo.with_expansion_text()

        self.memo_data[
            "Energy Tank"] = f"Energy Tank acquired.\nEnergy capacity increased by {self.configuration.energy_per_tank:g}."
        if self.configuration.immediate_energy_parts:
            self.memo_data[
                "Energy Part"] = f"Energy Part acquired.\nEnergy capacity increased by {self.configuration.energy_per_tank / 4:g}."

    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.METROID_DREAD

    def _calculate_starting_inventory(self, resources: ResourceCollection):
        result = {}
        for resource, quantity in resources.as_resource_gain():
            try:
                result[_get_item_id_for_item(resource)] = quantity
            except KeyError:
                print(f"Skipping {resource} for starting inventory: no item id")
                continue
        return result

    def _starting_inventory_text(self, resources: ResourceCollection):
        result = [r"{c1}Random starting items:{c0}"]
        items = item_names.additional_starting_items(self.configuration, self.game.resource_database, resources)
        if not items:
            return []
        result.extend(items)
        return result

    def _node_for(self, identifier: Union[AreaIdentifier, NodeIdentifier]) -> Node:
        if isinstance(identifier, NodeIdentifier):
            return self.game.world_list.node_by_identifier(identifier)
        else:
            area = self.game.world_list.area_by_area_location(identifier)
            node = area.node_with_name(area.default_node)
            assert node is not None
            return node

    def _key_error_for_node(self, node: Node, err: KeyError):
        return KeyError(f"{self.game.world_list.node_name(node, with_world=True)} has no extra {err}")

    def _start_point_ref_for(self, node: Node) -> dict:
        world = self.game.world_list.nodes_to_world(node)
        level_name: str = os.path.splitext(os.path.split(world.extra["asset_id"])[1])[0]

        try:
            return {
                "scenario": level_name,
                "actor": node.extra["start_point_actor_name"],
            }
        except KeyError as e:
            raise self._key_error_for_node(node, e)

    def _level_name_for(self, node: Node) -> str:
        world = self.game.world_list.nodes_to_world(node)
        return os.path.splitext(os.path.split(world.extra["asset_id"])[1])[0]

    def _teleporter_ref_for(self, node: Node, actor_key: str = "actor_name") -> dict:
        try:
            return {
                "scenario": self._level_name_for(node),
                "layer": node.extra.get("actor_layer", "default"),
                "actor": node.extra[actor_key],
            }
        except KeyError as e:
            raise self._key_error_for_node(node, e)

    def _callback_ref_for(self, node: Node) -> dict:
        try:
            return {
                "scenario": self._level_name_for(node),
                "function": node.extra["callback_function"],
                "args": node.extra.get("callback_args", 0)
            }
        except KeyError as e:
            raise KeyError(f"{node} has no extra {e}")

    def _pickup_detail_for_target(self, detail: ExportedPickupDetails) -> Optional[dict]:
        # target.

        if detail.model.game != RandovaniaGame.METROID_DREAD:
            map_icon = {
                # TODO: more specific icons for pickups in other games
                "custom_icon": {
                    "label": detail.model.name.upper(),
                }
            }
            model_name = "itemsphere"
        else:
            map_icon = {
                "icon_id": detail.model.name
            }
            model_name = _ALTERNATIVE_MODELS.get(detail.model.name, detail.model.name)

        ammoconfig = self.configuration.ammo_configuration.items_state
        pbammo = self.item_db.ammo["Power Bomb Tank"]

        def get_resource(res: ConditionalResources) -> dict:
            item_id = "ITEM_NONE"
            quantity = 1
            ids = [_get_item_id_for_item(r) for r, q in res.resources]
            for r, q in res.resources:
                try:
                    item_id = _get_item_id_for_item(r)
                    quantity = q
                    break
                except KeyError:
                    continue

            if "ITEM_WEAPON_POWER_BOMB" in ids:
                item_id = "ITEM_WEAPON_POWER_BOMB"

            # non-required mains
            if (item_id == "ITEM_WEAPON_POWER_BOMB_MAX"
                    and not ammoconfig[pbammo].requires_major_item):
                item_id = "ITEM_WEAPON_POWER_BOMB"

            return {"item_id": item_id, "quantity": quantity}

        # ugly hack
        resources = [get_resource(res) for res in detail.conditional_resources]
        if resources[0]["item_id"] == "ITEM_WEAPON_POWER_BOMB_MAX":
            resources = [resources[-1]]

        pickup_node = self.game.world_list.node_from_pickup_index(detail.index)
        pickup_type = pickup_node.extra.get("pickup_type", "actor")

        hud_text = detail.hud_text[0]
        if len(set(detail.hud_text)) > 1:
            hud_text = self.memo_data[detail.original_pickup.name]

        details = {
            "pickup_type": pickup_type,
            "caption": hud_text,
            "resources": resources
        }

        try:
            if pickup_type == "actor":
                if "map_icon_actor" in pickup_node.extra:
                    map_icon.update({
                        "original_actor": self._teleporter_ref_for(pickup_node, "map_icon_actor")
                    })
                details.update({
                    "pickup_actor": self._teleporter_ref_for(pickup_node),
                    "model": model_name,
                    "map_icon": map_icon,
                })
            else:
                details["pickup_lua_callback"] = self._callback_ref_for(pickup_node)
                if pickup_type != "cutscene":
                    details.update({
                        "pickup_actordef": pickup_node.extra["actor_def"],
                        "pickup_string_key": pickup_node.extra["string_key"],
                    })

            return details
        except KeyError as e:
            logging.warning(e)
            return None

    def _encode_hints(self) -> list[dict]:
        namer = DreadHintNamer(self.description.all_patches, self.players_config)
        exporter = HintExporter(namer, self.rng, ["A joke hint."])

        return [
            {
                "accesspoint_actor": self._teleporter_ref_for(logbook_node),
                "hint_id": logbook_node.extra["hint_id"],
                "text": exporter.create_message_for_hint(
                    self.patches.hints[self.game.world_list.identifier_for_node(logbook_node)],
                    self.description.all_patches, self.players_config, True
                ),
            }
            for logbook_node in self.game.world_list.iterate_nodes()
            if isinstance(logbook_node, LogbookNode)
        ]

    def _static_text_changes(self) -> dict[str, str]:
        full_hash = f"{self.description.shareable_word_hash} ({self.description.shareable_hash})"
        text = {}
        difficulty_labels = {
            "GUI_DIFSELECTOR_LABEL_DESCRIPTOR_HARD_UNLOCKED",
            "GUI_DIFSELECTOR_LABEL_DESCRIPTOR_NORMAL",
            "GUI_DIFSELECTOR_LABEL_DESCRIPTOR_EASY",
            "GUI_DIFSELECTOR_LABEL_DESCRIPTOR_EXPERT"
        }
        for difficulty in difficulty_labels:
            text[difficulty] = full_hash

        text["GUI_COMPANY_TITLE_SCREEN"] = "|".join([
            "<versions>",
            full_hash
        ])

        # Warning message for continuing a non-rando game file
        text["GUI_WARNING_NOT_RANDO_GAME_1"] = "|".join([
            r"{c2}Error!{c0}",
            "This save slot was created using a different Randomizer mod.",
        ])
        text["GUI_WARNING_NOT_RANDO_GAME_2"] = "|".join([
            "You must start a New Game from a blank save slot. Returning to title screen.",
        ])

        return text

    def _cosmetic_patch_data(self) -> dict:
        c = self.cosmetic_patches
        return {
            "config": {
                "AIManager": {
                    "bShowBossLifebar": c.show_boss_lifebar,
                    "bShowEnemyLife": c.show_enemy_life,
                    "bShowEnemyDamage": c.show_enemy_damage,
                    "bShowPlayerDamage": c.show_player_damage
                }
            }
        }

    def _door_patches(self):
        wl = self.game.world_list

        result = []
        used_actors = {}

        for identifier, weakness in self.patches.dock_weakness.items():
            if "type" not in weakness.extra:
                raise ValueError(f"Unable to change door {identifier} into {weakness.name}: incompatible door weakness")

            result.append({
                "actor": (actor := self._teleporter_ref_for(wl.node_by_identifier(identifier))),
                "door_type": (door_type := weakness.extra["type"]),
            })
            actor_idef = str(actor)
            if used_actors.get(actor_idef, door_type) != door_type:
                raise ValueError(f"Door for {identifier} ({actor}) previously "
                                 f"patched to use {used_actors[actor_idef]}, tried to change to {door_type}.")
            used_actors[actor_idef] = door_type

        return result

    def create_data(self) -> dict:
        starting_location = self._start_point_ref_for(self._node_for(self.patches.starting_location))
        starting_items = self._calculate_starting_inventory(self.patches.starting_items)
        starting_text = [self._starting_inventory_text(self.patches.starting_items)]

        useless_target = PickupTarget(pickup_creator.create_nothing_pickup(self.game.resource_database),
                                      self.players_config.player_index)

        pickup_list = pickup_exporter.export_all_indices(
            self.patches,
            useless_target,
            self.game.world_list,
            self.rng,
            self.configuration.pickup_model_style,
            self.configuration.pickup_model_data_source,
            exporter=pickup_exporter.create_pickup_exporter(self.game, self.memo_data, self.players_config),
            visual_etm=pickup_creator.create_visual_etm(),
        )

        energy_per_tank = self.configuration.energy_per_tank if self.configuration.immediate_energy_parts else 100.0

        return {
            "configuration_identifier": self.description.shareable_hash,
            "starting_location": starting_location,
            "starting_items": starting_items,
            "starting_text": starting_text,
            "pickups": [
                data
                for pickup_item in pickup_list
                if (data := self._pickup_detail_for_target(pickup_item)) is not None
            ],
            "elevators": [
                {
                    "teleporter": self._teleporter_ref_for(self._node_for(source)),
                    "destination": self._start_point_ref_for(self._node_for(target)),
                }
                for source, target in self.patches.elevator_connection.items()
            ],
            "hints": self._encode_hints(),
            "text_patches": self._static_text_changes(),
            "cosmetic_patches": self._cosmetic_patch_data(),
            "energy_per_tank": energy_per_tank,
            "immediate_energy_parts": self.configuration.immediate_energy_parts,
            "game_patches": {
                "consistent_raven_beak_damage_table": True,
                "remove_grapple_blocks_hanubia_shortcut": self.configuration.hanubia_shortcut_no_grapple,
                "remove_grapple_block_path_to_itorash": self.configuration.hanubia_easier_path_to_itorash,
                "default_x_released": self.configuration.x_starts_released,
            },
            "door_patches": self._door_patches(),
        }


class DreadAcquiredMemo(dict):
    def __missing__(self, key):
        return "{} acquired.".format(key)

    @classmethod
    def with_expansion_text(cls):
        result = cls()
        result["Missile Tank"] = "Missile Tank acquired.\nMissile capacity increased by {Missiles}."
        result["Missile+ Tank"] = "Missile+ Tank acquired.\nMissile capacity increased by {Missiles}."
        result["Power Bomb Tank"] = "Power Bomb Tank acquired.\nPower Bomb capacity increased by {Power Bombs}."
        result["Energy Part"] = "Energy Part acquired.\nCollect 4 to increase energy capacity."
        result["Energy Tank"] = "Energy Tank acquired.\nEnergy capacity increased by 100."
        result["Locked Power Bomb Tank"] = result["Power Bomb Tank"]
        return result
