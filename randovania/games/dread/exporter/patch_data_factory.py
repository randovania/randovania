from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from randovania.exporter import item_names
from randovania.exporter.hints import credits_spoiler, guaranteed_item_hint
from randovania.exporter.hints.hint_exporter import HintExporter
from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.pickup.pickup_entry import PickupModel
from randovania.games.dread.exporter.hint_namer import DreadHintNamer
from randovania.games.dread.layout.dread_cosmetic_patches import DreadCosmeticPatches, DreadMissileCosmeticType
from randovania.games.game import RandovaniaGame
from randovania.generator.pickup_pool import pickup_creator
from randovania.layout.lib.teleporters import TeleporterShuffleMode

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.exporter.pickup_exporter import ExportedPickupDetails
    from randovania.game_description.db.area import Area
    from randovania.game_description.db.node import Node
    from randovania.game_description.pickup.pickup_entry import ConditionalResources, PickupEntry
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.games.dread.layout.dread_configuration import DreadConfiguration

_ALTERNATIVE_MODELS = {
    PickupModel(RandovaniaGame.METROID_DREAD, "Nothing"): ["itemsphere"],
    PickupModel(RandovaniaGame.METROID_DREAD, "powerup_slide"): ["itemsphere"],
    PickupModel(RandovaniaGame.METROID_DREAD, "powerup_hyperbeam"): ["powerup_plasmabeam"],
    PickupModel(RandovaniaGame.METROID_DREAD, "powerup_metroidsuit"): ["powerup_gravitysuit"],
    PickupModel(RandovaniaGame.METROID_DREAD, "PROGRESSIVE_BEAM"): [
        "powerup_widebeam",
        "powerup_plasmabeam",
        "powerup_wavebeam",
    ],
    PickupModel(RandovaniaGame.METROID_DREAD, "PROGRESSIVE_CHARGE"): ["powerup_chargebeam", "powerup_diffusionbeam"],
    PickupModel(RandovaniaGame.METROID_DREAD, "PROGRESSIVE_MISSILE"): ["powerup_supermissile", "powerup_icemissile"],
    PickupModel(RandovaniaGame.METROID_DREAD, "PROGRESSIVE_SUIT"): ["powerup_variasuit", "powerup_gravitysuit"],
    PickupModel(RandovaniaGame.METROID_DREAD, "PROGRESSIVE_BOMB"): ["powerup_bomb", "powerup_crossbomb"],
    PickupModel(RandovaniaGame.METROID_DREAD, "PROGRESSIVE_SPIN"): ["powerup_doublejump", "powerup_spacejump"],
}


def get_item_id_for_item(item: ItemResourceInfo) -> str:
    if "item_capacity_id" in item.extra:
        return item.extra["item_capacity_id"]
    try:
        return item.extra["item_id"]
    except KeyError as e:
        raise KeyError(f"{item.long_name} has no item ID.") from e


def convert_conditional_resource(res: ConditionalResources) -> Iterator[dict]:
    if not res.resources:
        yield {"item_id": "ITEM_NONE", "quantity": 0}
        return

    for resource in reversed(res.resources):
        item_id = get_item_id_for_item(resource[0])
        quantity = resource[1]

        yield {"item_id": item_id, "quantity": quantity}


def get_resources_for_details(
    pickup: PickupEntry, conditional_resources: list[ConditionalResources], other_player: bool
) -> list[list[dict]]:
    resources = [
        list(convert_conditional_resource(conditional_resource)) for conditional_resource in conditional_resources
    ]

    # don't add more resources for multiworld items
    if other_player:
        return resources

    if pickup.resource_lock is not None and not pickup.respects_lock and not pickup.unlocks_resource:
        # Add the lock resource into the pickup in addition to the expansion's resources
        assert len(resources) == 1
        resources[0].append(
            {
                "item_id": get_item_id_for_item(pickup.resource_lock.locked_by),
                "quantity": 1,
            }
        )

    return resources


def _get_destination_room_for_teleportal(connection: Node):
    return connection.extra.get("transporter_name", f"{connection.identifier.region} - {connection.identifier.area}")


class DreadPatchDataFactory(PatchDataFactory):
    cosmetic_patches: DreadCosmeticPatches
    configuration: DreadConfiguration
    spawnpoint_name_prefix = "SP_RDV_"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_spawn_points: dict[Node, dict] = {}

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

    def _starting_inventory_text(self):
        result = [r"{c1}Random starting items:{c0}"]
        items = item_names.additional_starting_equipment(self.configuration, self.game, self.patches)
        if not items:
            return []
        result.extend(items)
        return result

    def _key_error_for_node(self, node: Node, err: KeyError):
        return KeyError(f"{self.game.region_list.node_name(node, with_region=True)} has no extra {err}")

    def _get_or_create_spawn_point(self, node: Node, level_name: str):
        if node in self.new_spawn_points:
            return self.new_spawn_points[node]["new_actor"]["actor"]
        else:
            assert node.location is not None
            area = self.game.region_list.area_by_area_location(node.identifier.area_identifier)
            collision_camera_name = area.extra["asset_id"]
            new_spawnpoint_name = f"{self.spawnpoint_name_prefix}{len(self.new_spawn_points):03d}"
            self.new_spawn_points[node] = {
                "new_actor": {"actor": new_spawnpoint_name, "scenario": level_name},
                "location": {"x": node.location.x, "y": node.location.y, "z": node.location.z},
                "collision_camera_name": collision_camera_name,
            }
            return new_spawnpoint_name

    def _start_point_ref_for(self, node: Node) -> dict:
        region = self.game.region_list.nodes_to_region(node)
        level_name: str = region.extra["scenario_id"]

        if "start_point_actor_name" in node.extra:
            return {
                "scenario": level_name,
                "actor": node.extra["start_point_actor_name"],
            }
        else:
            return {
                "scenario": level_name,
                "actor": self._get_or_create_spawn_point(node, level_name),
            }

    def _level_name_for(self, node: Node) -> str:
        region = self.game.region_list.nodes_to_region(node)
        return region.extra["scenario_id"]

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
                "args": node.extra.get("callback_args", 0),
            }
        except KeyError as e:
            raise KeyError(f"{node} has no extra {e}")

    def _pickup_detail_for_target(self, detail: ExportedPickupDetails) -> dict | None:
        alt_model = _ALTERNATIVE_MODELS.get(detail.model, [detail.model.name])
        model_names = alt_model

        if detail.other_player:
            if model_names == ["offworld"]:
                base_icon = "unknown"
                model_names = ["itemsphere"]
            else:
                base_icon = detail.model.name

            map_icon = {"custom_icon": {"label": detail.name.upper(), "base_icon": base_icon}}
        elif alt_model[0] == "itemsphere":
            map_icon = {
                "custom_icon": {
                    "label": detail.original_pickup.name.upper(),
                }
            }
        else:
            map_icon = {"icon_id": detail.model.name}

        resources = get_resources_for_details(detail.original_pickup, detail.conditional_resources, detail.other_player)

        pickup_node = self.game.region_list.node_from_pickup_index(detail.index)
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

            if self.cosmetic_patches.missile_cosmetic != DreadMissileCosmeticType.NONE:
                if model_names[0] == "item_missiletank":
                    colors = self.cosmetic_patches.missile_cosmetic.colors
                    new_model = colors[self.rng.randint(0, len(colors) - 1)].value
                    model_names = [new_model]

            # Progressive models currently crash when placed in Hanubia.
            # See https://github.com/randovania/open-dread-rando/issues/141
            if pickup_actor["scenario"] == "s080_shipyard":
                model_names = [model_names[0]]

            if "map_icon_actor" in pickup_node.extra:
                map_icon.update({"original_actor": self._teleporter_ref_for(pickup_node, "map_icon_actor")})
            details.update(
                {
                    "pickup_actor": pickup_actor,
                    "model": model_names,
                    "map_icon": map_icon,
                }
            )
        else:
            details["pickup_lua_callback"] = self._callback_ref_for(pickup_node)
            if pickup_type != "cutscene":
                details.update(
                    {
                        "pickup_actordef": pickup_node.extra["actor_def"],
                        "pickup_string_key": pickup_node.extra["string_key"],
                    }
                )

        return details

    def _encode_hints(self) -> list[dict]:
        namer = DreadHintNamer(self.description.all_patches, self.players_config)
        exporter = HintExporter(namer, self.rng, ["A joke hint."])

        return [
            {
                "accesspoint_actor": self._teleporter_ref_for(hint_node),
                "hint_id": hint_node.extra["hint_id"],
                "text": exporter.create_message_for_hint(
                    self.patches.hints[hint_node.identifier],
                    self.description.all_patches,
                    self.players_config,
                    True,
                ),
            }
            for hint_node in self.game.region_list.iterate_nodes()
            if isinstance(hint_node, HintNode)
        ]

    def _static_text_changes(self) -> dict[str, str]:
        full_hash = f"{self.description.shareable_word_hash} ({self.description.shareable_hash})"
        text = {}
        difficulty_labels = {
            "GUI_DIFSELECTOR_LABEL_DESCRIPTOR_HARD_UNLOCKED",
            "GUI_DIFSELECTOR_LABEL_DESCRIPTOR_NORMAL",
            "GUI_DIFSELECTOR_LABEL_DESCRIPTOR_EASY",
            "GUI_DIFSELECTOR_LABEL_DESCRIPTOR_EXPERT",
        }
        for difficulty in difficulty_labels:
            text[difficulty] = full_hash

        text["GUI_COMPANY_TITLE_SCREEN"] = "|".join(["<versions>", full_hash])

        # Warning message for continuing a non-rando game file
        text["GUI_WARNING_NOT_RANDO_GAME_1"] = "|".join(
            [
                r"{c2}Error!{c0}",
                "This save slot was created using a different Randomizer mod.",
            ]
        )
        text["GUI_WARNING_NOT_RANDO_GAME_2"] = "|".join(
            [
                "You must start a New Game from a blank save slot. Returning to title screen.",
            ]
        )

        return text

    def _credits_spoiler(self) -> dict[str, str]:
        return credits_spoiler.generic_credits(
            self.configuration.standard_pickup_configuration,
            self.description.all_patches,
            self.players_config,
            DreadHintNamer(self.description.all_patches, self.players_config),
        )

    def _static_room_name_fixes(self, scenario_name: str, area: Area):
        # static fixes for some rooms
        cc_name = area.extra["asset_id"]
        area_name = area.name
        if scenario_name == "s040_aqua":
            if cc_name == "collision_camera_010":
                return cc_name, "Burenia Main Hub"
            if cc_name == "collision_camera_023_B":
                return "collision_camera_023", area_name

        if scenario_name == "s050_forest":
            if cc_name == "collision_camera_024":
                return cc_name, "Golzuna Tower"

        if scenario_name == "s060_quarantine":
            if cc_name == "collision_camera_MBL_B":
                return "collision_camera_MBL", area.name

        if scenario_name == "s070_basesanc":
            if cc_name == "collision_camera_038_A":
                return "collision_camera_038", area.name

        return cc_name, area.name

    def _build_teleporter_name_dict(self) -> dict[str, dict[str, str]]:
        cc_dict: dict = {}
        for node, connection in self.patches.all_dock_connections():
            if (
                isinstance(node, DockNode)
                and node.dock_type in self.game.dock_weakness_database.all_teleporter_dock_types
            ):
                src_region, src_area = self.game.region_list.region_and_area_by_area_identifier(
                    node.identifier.area_identifier
                )
                src_cc = src_area.extra["asset_id"]
                dest_name = _get_destination_room_for_teleportal(connection)

                if src_region.extra["scenario_id"] not in cc_dict:
                    cc_dict[src_region.extra["scenario_id"]] = {}
                cc_dict[src_region.extra["scenario_id"]][src_cc] = f"Transport to {dest_name}"

        return cc_dict

    def _build_area_name_dict(self) -> dict[str, dict[str, str]]:
        # generate a 2D dictionary of (scenario, collision camera) => room name
        all_dict: dict = {}
        for region in self.game.region_list.regions:
            scenario = region.extra["scenario_id"]
            region_dict: dict = {}

            for area in region.areas:
                cc_name, area_name = self._static_room_name_fixes(scenario, area)
                region_dict[cc_name] = area_name
            all_dict[scenario] = region_dict

        # rename transporters to the correct transporter rooms
        teleporter_dict = self._build_teleporter_name_dict()
        for k, v in teleporter_dict.items():
            all_dict[k].update(v)

        return all_dict

    def _cosmetic_patch_data(self) -> dict:
        c = self.cosmetic_patches
        cosmetic_dict: dict = {
            "config": {
                "AIManager": {
                    "bShowBossLifebar": c.show_boss_lifebar,
                    "bShowEnemyLife": c.show_enemy_life,
                    "bShowEnemyDamage": c.show_enemy_damage,
                    "bShowPlayerDamage": c.show_player_damage,
                },
                "SoundSystemATK": {
                    "fMusicVolume": c.music_volume / 100,
                    "fSfxVolume": c.sfx_volume / 100,
                    "fEnvironmentStreamsVolume": c.ambience_volume / 100,
                },
            },
            "lua": {
                "custom_init": {
                    "enable_death_counter": c.show_death_counter,
                    "enable_room_name_display": c.show_room_names.value,
                },
            },
            "shield_versions": {
                "ice_missile": c.alt_ice_missile.value,
                "storm_missile": c.alt_storm_missile.value,
                "diffusion_beam": c.alt_diffusion_beam.value,
                "bomb": c.alt_bomb.value,
                "cross_bomb": c.alt_cross_bomb.value,
                "power_bomb": c.alt_power_bomb.value,
                "closed": c.alt_closed.value,
            },
        }

        if c.show_room_names.value != "NEVER":
            cosmetic_dict["lua"]["camera_names_dict"] = self._build_area_name_dict()
        elif not self.configuration.teleporters.is_vanilla:
            cosmetic_dict["lua"]["custom_init"]["enable_room_name_display"] = "ALWAYS"
            cosmetic_dict["lua"]["camera_names_dict"] = self._build_teleporter_name_dict()

        return cosmetic_dict

    def _door_patches(self):
        wl = self.game.region_list

        result = []
        used_actors = {}

        for node, weakness in self.patches.all_dock_weaknesses():
            if "type" not in weakness.extra:
                raise ValueError(
                    f"Unable to change door {wl.node_name(node)} into {weakness.name}: incompatible door weakness"
                )

            if "actor_name" not in node.extra:
                print(f"Invalid door (no actor): {node}")
                continue

            result.append(
                {
                    "actor": (actor := self._teleporter_ref_for(node)),
                    "door_type": (door_type := weakness.extra["type"]),
                }
            )
            actor_idef = str(actor)
            if used_actors.get(actor_idef, door_type) != door_type:
                raise ValueError(
                    f"Door for {wl.node_name(node)} ({actor}) previously "
                    f"patched to use {used_actors[actor_idef]}, tried to change to {door_type}."
                )
            used_actors[actor_idef] = door_type

        return result

    def _objective_patches(self) -> dict:
        if self.configuration.artifacts.required_artifacts == 0:
            return {"required_artifacts": 0, "hints": []}

        artifacts = [self.game.resource_database.get_item(f"Artifact{i + 1}") for i in range(12)]
        artifact_hints = guaranteed_item_hint.create_guaranteed_hints_for_resources(
            self.description.all_patches,
            self.players_config,
            DreadHintNamer(self.description.all_patches, self.players_config),
            True,
            artifacts,
            True,
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
            # beam blocks -> speedboost blocks in Artaria EMMI zone Speed Booster puzzle to prevent softlock
            {
                "actor": {"scenario": "s010_cave", "layer": "breakables", "actor": "breakabletilegroup_060"},
                "tiletype": "SPEEDBOOST",
            }
        ]

    def create_memo_data(self) -> dict:
        """Used to generate pickup collection messages."""
        tank = self.configuration.energy_per_tank
        memo_data = DreadAcquiredMemo.with_expansion_text()
        memo_data["Energy Tank"] = f"Energy Tank acquired.\nEnergy capacity increased by {tank:g}."
        if self.configuration.immediate_energy_parts:
            memo_data["Energy Part"] = f"Energy Part acquired.\nEnergy capacity increased by {tank / 4:g}."
        return memo_data

    def create_visual_nothing(self) -> PickupEntry:
        """The model of this pickup replaces the model of all pickups when PickupModelDataSource is ETM"""
        return pickup_creator.create_visual_nothing(self.game_enum(), "Nothing")

    def create_game_specific_data(self) -> dict:
        starting_location_node = self.game.region_list.node_by_identifier(self.patches.starting_location)
        starting_location = self._start_point_ref_for(starting_location_node)
        starting_items = self._calculate_starting_inventory(self.patches.starting_resources())
        starting_text = [self._starting_inventory_text()]

        pickup_list = self.export_pickup_list()

        energy_per_tank = self.configuration.energy_per_tank if self.configuration.immediate_energy_parts else 100.0

        teleporters = [
            {
                "teleporter": self._teleporter_ref_for(node),
                "destination": self._start_point_ref_for(connection),
                "connection_name": _get_destination_room_for_teleportal(connection),
            }
            for node, connection in self.patches.all_dock_connections()
            if (
                isinstance(node, DockNode)
                and node.dock_type in self.game.dock_weakness_database.all_teleporter_dock_types
                or node.dock_type.extra.get("is_teleportal", False)
            )
        ]

        # special-case the Ghavoran Flipper train to update the map correctly
        flipper_list = [t for t in teleporters if t["teleporter"]["actor"] == "wagontrain_quarantine_with_cutscene_000"]
        if flipper_list:
            other_train = deepcopy(flipper_list[0])
            other_train["teleporter"]["actor"] = "wagontrain_quarantine_000"
            teleporters.append(other_train)

        return {
            "configuration_identifier": self.description.shareable_hash,
            "starting_location": starting_location,
            "starting_items": starting_items,
            "starting_text": starting_text,
            "pickups": [
                data for pickup_item in pickup_list if (data := self._pickup_detail_for_target(pickup_item)) is not None
            ],
            "elevators": teleporters if self.configuration.teleporters.mode != TeleporterShuffleMode.VANILLA else [],
            "hints": self._encode_hints(),
            "text_patches": dict(sorted(self._static_text_changes().items())),
            "spoiler_log": self._credits_spoiler(),
            "cosmetic_patches": self._cosmetic_patch_data(),
            "energy_per_tank": energy_per_tank,
            "immediate_energy_parts": self.configuration.immediate_energy_parts,
            "enable_remote_lua": self.cosmetic_patches.enable_auto_tracker or self.players_config.is_multiworld,
            "constant_environment_damage": {
                "heat": self.configuration.constant_heat_damage,
                "cold": self.configuration.constant_cold_damage,
                "lava": self.configuration.constant_lava_damage,
            },
            "game_patches": {
                "raven_beak_damage_table_handling": self.configuration.raven_beak_damage_table_handling.value,
                "remove_grapple_blocks_hanubia_shortcut": self.configuration.hanubia_shortcut_no_grapple,
                "remove_grapple_block_path_to_itorash": self.configuration.hanubia_easier_path_to_itorash,
                "default_x_released": self.configuration.x_starts_released,
                "nerf_power_bombs": self.configuration.nerf_power_bombs,
                "warp_to_start": self.configuration.warp_to_start,
            },
            "show_shields_on_minimap": not self.configuration.dock_rando.is_enabled(),
            "door_patches": self._door_patches(),
            "tile_group_patches": self._tilegroup_patches(),
            "new_spawn_points": list(self.new_spawn_points.values()),
            "objective": self._objective_patches(),
            "layout_uuid": str(self.players_config.get_own_uuid()),
        }


class DreadAcquiredMemo(dict):
    def __missing__(self, key):
        return f"{key} acquired."

    @classmethod
    def with_expansion_text(cls):
        result = cls()
        result["Missile Tank"] = "Missile Tank acquired.\nMissile capacity {MissilesChanged} by {Missiles}."
        result["Missile+ Tank"] = "Missile+ Tank acquired.\nMissile capacity {MissilesChanged} by {Missiles}."
        result["Power Bomb Tank"] = "Power Bomb Tank acquired.\nPower Bomb capacity increased by {Power Bombs}."
        result["Energy Part"] = "Energy Part acquired.\nCollect 4 to increase energy capacity."
        result["Energy Tank"] = "Energy Tank acquired.\nEnergy capacity increased by 100."
        result["Locked Power Bomb Tank"] = result["Power Bomb Tank"]
        return result
