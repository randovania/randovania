import logging
import os

from randovania.exporter import pickup_exporter, item_names
from randovania.exporter.hints import credits_spoiler, guaranteed_item_hint
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
    "Nothing": ["itemsphere"],

    "powerup_slide": ["itemsphere"],
    "powerup_hyperbeam": ["powerup_plasmabeam"],
    "powerup_metroidsuit": ["powerup_gravitysuit"],

    "PROGRESSIVE_BEAM": ["powerup_widebeam", "powerup_plasmabeam", "powerup_wavebeam"],
    "PROGRESSIVE_CHARGE": ["powerup_chargebeam", "powerup_diffusionbeam"],
    "PROGRESSIVE_MISSILE": ["powerup_supermissile", "powerup_icemissile"],
    "PROGRESSIVE_SUIT": ["powerup_variasuit", "powerup_gravitysuit"],
    "PROGRESSIVE_BOMB": ["powerup_bomb", "powerup_crossbomb"],
    "PROGRESSIVE_SPIN": ["powerup_doublejump", "powerup_spacejump"],
}


def get_item_id_for_item(item: ItemResourceInfo) -> str:
    if "item_capacity_id" in item.extra:
        return item.extra["item_capacity_id"]
    try:
        return item.extra["item_id"]
    except KeyError as e:
        raise KeyError(f"{item.long_name} has no item ID.") from e


def convert_conditional_resource(respects_lock: bool, res: ConditionalResources) -> dict:
    if not res.resources:
        return {"item_id": "ITEM_NONE", "quantity": 0}

    item_id = get_item_id_for_item(res.resources[0][0])
    quantity = res.resources[0][1]

    # only main pbs have 2 elements in res.resources, everything else is just 1
    if len(res.resources) != 1:
        item_id = get_item_id_for_item(res.resources[1][0])
        assert item_id == "ITEM_WEAPON_POWER_BOMB"
        assert len(res.resources) == 2

    # non-required mains
    if item_id == "ITEM_WEAPON_POWER_BOMB_MAX" and not respects_lock:
        item_id = "ITEM_WEAPON_POWER_BOMB"

    return {"item_id": item_id, "quantity": quantity}


def get_resources_for_details(detail: ExportedPickupDetails) -> list[dict]:
    return [
        convert_conditional_resource(detail.original_pickup.respects_lock, res)
        for res in detail.conditional_resources
    ]


class DreadPatchDataFactory(BasePatchDataFactory):
    cosmetic_patches: DreadCosmeticPatches
    configuration: DreadConfiguration

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memo_data = DreadAcquiredMemo.with_expansion_text()

        tank = self.configuration.energy_per_tank
        self.memo_data["Energy Tank"] = f"Energy Tank acquired.\nEnergy capacity increased by {tank:g}."
        if self.configuration.immediate_energy_parts:
            self.memo_data["Energy Part"] = f"Energy Part acquired.\nEnergy capacity increased by {tank / 4:g}."

    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.METROID_DREAD

    def _calculate_starting_inventory(self, resources: ResourceCollection):
        result = {}
        for resource, quantity in resources.as_resource_gain():
            try:
                result[get_item_id_for_item(resource)] = quantity
            except KeyError:
                print(f"Skipping {resource} for starting inventory: no item id")
                continue
        return result

    def _starting_inventory_text(self, resources: ResourceCollection):
        result = [r"{c1}Random starting items:{c0}"]
        items = item_names.additional_starting_items(self.configuration, self.game, resources)
        if not items:
            return []
        result.extend(items)
        return result

    def _node_for(self, identifier: AreaIdentifier | NodeIdentifier) -> Node:
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

    def _pickup_detail_for_target(self, detail: ExportedPickupDetails) -> dict | None:
        # target.

        alt_model = _ALTERNATIVE_MODELS.get(detail.model.name, [detail.model.name])

        if detail.model.game != RandovaniaGame.METROID_DREAD or alt_model[0] == "itemsphere":
            map_icon = {
                # TODO: more specific icons for pickups in other games
                "custom_icon": {
                    "label": detail.original_pickup.name.upper(),
                }
            }
            model_names = ["itemsphere"]
        else:
            map_icon = {
                "icon_id": detail.model.name
            }
            model_names = alt_model

        resources = get_resources_for_details(detail)

        pickup_node = self.game.world_list.node_from_pickup_index(detail.index)
        pickup_type = pickup_node.extra.get("pickup_type", "actor")

        hud_text = detail.collection_text[0]
        if len(set(detail.collection_text)) > 1:
            hud_text = self.memo_data[detail.original_pickup.name]

        details = {
            "pickup_type": pickup_type,
            "caption": hud_text,
            "resources": resources,
        }

        if pickup_type == "actor":
            pickup_actor = self._teleporter_ref_for(pickup_node)

            # Progressive models currently crash when placed in Hanubia.
            # See https://github.com/randovania/open-dread-rando/issues/141
            if pickup_actor["scenario"] == "s080_shipyard":
                model_names = [model_names[0]]

            if "map_icon_actor" in pickup_node.extra:
                map_icon.update({
                    "original_actor": self._teleporter_ref_for(pickup_node, "map_icon_actor")
                })
            details.update({
                "pickup_actor": pickup_actor,
                "model": model_names,
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
    
    def _credits_spoiler(self) -> dict[str, str]:
        return credits_spoiler.generic_credits(
            self.configuration.major_items_configuration,
            self.description.all_patches,
            self.players_config,
            DreadHintNamer(self.description.all_patches, self.players_config),
        )

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

        for node, weakness in self.patches.all_dock_weaknesses():
            if "type" not in weakness.extra:
                raise ValueError(
                    f"Unable to change door {wl.node_name(node)} into {weakness.name}: incompatible door weakness")

            if "actor_name" not in node.extra:
                print(f"Invalid door (no actor): {node}")
                continue
            
            result.append({
                "actor": (actor := self._teleporter_ref_for(node)),
                "door_type": (door_type := weakness.extra["type"]),
            })
            actor_idef = str(actor)
            if used_actors.get(actor_idef, door_type) != door_type:
                raise ValueError(f"Door for {wl.node_name(node)} ({actor}) previously "
                                 f"patched to use {used_actors[actor_idef]}, tried to change to {door_type}.")
            used_actors[actor_idef] = door_type

        return result

    def _objective_patches(self) -> dict:
        if self.configuration.artifacts.required_artifacts == 0:
            return {
                "required_artifacts": 0,
                "hints": []
            }

        artifacts = [self.game.resource_database.get_item(f"Artifact{i + 1}") for i in range(12)]
        artifact_hints = guaranteed_item_hint.create_guaranteed_hints_for_resources(
            self.description.all_patches,
            self.players_config,
            DreadHintNamer(self.description.all_patches, self.players_config),
            True,
            artifacts,
            True
        )

        hint_text = []
        for group in (artifacts[:3], artifacts[3:6], artifacts[6:9], artifacts[9:]):
            text = "|".join(artifact_hints[a] for a in group if artifact_hints[a])
            if text:
                hint_text.append(text)

        return {
            "required_artifacts": self.configuration.artifacts.required_artifacts,
            "hints": hint_text,
        }

    def _tilegroup_patches(self):
        return [
            # beam blocks -> speedboost blocks in Artaria EMMI zone speedbooster puzzle to prevent softlock
            dict(
                actor=dict(scenario="s010_cave",layer="breakables",actor="breakabletilegroup_060"),
                tiletype="SPEEDBOOST"
            )
        ]

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
                    "teleporter": self._teleporter_ref_for(source),
                    "destination": self._start_point_ref_for(self._node_for(target)),
                }
                for source, target in self.patches.all_elevator_connections()
            ],
            "hints": self._encode_hints(),
            "text_patches": self._static_text_changes(),
            "spoiler_log": self._credits_spoiler(),
            "cosmetic_patches": self._cosmetic_patch_data(),
            "energy_per_tank": energy_per_tank,
            "immediate_energy_parts": self.configuration.immediate_energy_parts,
            "constant_environment_damage": {
                "heat": self.configuration.constant_heat_damage,
                "cold": self.configuration.constant_cold_damage,
                "lava": self.configuration.constant_lava_damage,
            },
            "game_patches": {
                "consistent_raven_beak_damage_table": True,
                "remove_grapple_blocks_hanubia_shortcut": self.configuration.hanubia_shortcut_no_grapple,
                "remove_grapple_block_path_to_itorash": self.configuration.hanubia_easier_path_to_itorash,
                "default_x_released": self.configuration.x_starts_released,
            },
            "door_patches": self._door_patches(),
            "tile_group_patches": self._tilegroup_patches(),
            "objective": self._objective_patches(),
        }


class DreadAcquiredMemo(dict):
    def __missing__(self, key):
        return f"{key} acquired."

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
