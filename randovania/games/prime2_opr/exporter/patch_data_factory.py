from __future__ import annotations

import functools
from collections import defaultdict
from collections.abc import Callable, Iterable
from random import Random
from typing import TYPE_CHECKING, Literal, NotRequired, TypedDict, override

from randovania.exporter import pickup_exporter
from randovania.exporter.hints.temple_key_hint import create_temple_key_hint
from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.db.dock import DockType
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.db.region import Region
from randovania.game_description.hint import HintDarkTemple
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.games.common import elevators
from randovania.games.prime2.exporter import hints
from randovania.games.prime2.exporter.hint_namer import EchoesHintNamer
from randovania.games.prime2.exporter.joke_hints import ECHOES_JOKE_HINTS
from randovania.games.prime2.exporter.patch_data_factory import (
    _ELEVATOR_ROOMS_MAP_ASSET_IDS,
    akul_testament_string_patch,
    default_prime2_memo_data,
    echoes_raw_pickup_list,
    pretty_name_for_elevator,
    simplified_prime2_memo_data,
)
from randovania.games.prime2_opr.layout import EchoesOPRConfiguration, EchoesOPRCosmeticPatches
from randovania.layout.base.hint_configuration import SpecificPickupHintMode
from randovania.layout.base.pickup_model import PickupModelStyle
from randovania.layout.lib.teleporters import TeleporterShuffleMode
from randovania.lib import frozen_lib

if TYPE_CHECKING:
    from randovania.exporter.hints.hint_namer import HintNamer
    from randovania.exporter.patch_data_factory import PatcherDataMeta

type SoundType = Literal["standard", "expansion", "key"]


class AreaChange(TypedDict):
    mrea_id: NotRequired[int]

    pickups: NotRequired[list[dict]]
    translator_gates: NotRequired[list[dict]]
    door_locks: NotRequired[list[dict]]
    elevators: NotRequired[list[dict]]
    portals: NotRequired[list[dict]]
    new_name: NotRequired[str]


class WorldChange(TypedDict):
    mlvl_id: NotRequired[int]

    other_world_to_copy_in_mapu: NotRequired[int]
    area_changes: list[AreaChange]


class EchoesOPRPatchDataFactory(PatchDataFactory[EchoesOPRConfiguration, EchoesOPRCosmeticPatches]):
    @override
    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_ECHOES_OPR

    @override
    def create_game_specific_data(self, randovania_meta: PatcherDataMeta) -> dict:
        # header data
        data = {
            "title_screen_text": "",
            "game_title": f"Echoes OPR - {self.description.shareable_word_hash}"[:64],
            "seed": self.description.get_seed_for_world(self.players_config.player_index),
            "world_uuid": str(self.players_config.get_own_uuid()),
        }

        # starting location/items
        data["starting_area"] = self._area_reference_from_identifier(self.patches.starting_location.area_identifier)
        data["starting_items"] = self.create_starting_items_data()

        # world changes
        data["world_changes"] = self.create_world_changes()

        # string changes
        data["string_changes"] = self.create_string_changes()

        # other settings
        data["practice_mod"] = "full" if self.configuration.practice_mod else "disabled"
        data["two_way_portals"] = self.configuration.portal_rando
        data["inverted_mode"] = self.configuration.inverted_mode
        data["auto_enabled_elevators"] = self._should_auto_enable_elevators()
        data["beam_configuration"] = self.configuration.beam_configuration.as_json
        data["damage_changes"] = self.create_damage_changes()
        data["custom_items"] = self.create_custom_items_config()

        # cosmetic settings
        data["game_options_defaults"] = self.cosmetic_patches.user_preferences.as_json
        data["map_visibility"] = self.create_map_visibility()
        data["suit_replacement"] = self.create_suit_mapping()
        data["hud_color"] = self.create_hud_color()

        return data

    @override
    @classmethod
    def hint_namer_type(cls) -> type[HintNamer]:
        return EchoesHintNamer

    def _asset_id_for_region(self, region: Region) -> int:
        """Gets the MLVL asset ID for this region."""
        if "asset_id" in region.extra:
            return region.extra["asset_id"]
        else:
            light_region = self.game.region_list.region_with_name(region.extra["associated_region"])
            return light_region.extra["asset_id"]

    def _asset_ids_for_area(self, identifier: AreaIdentifier) -> tuple[int, int]:
        """Gets the MLVL asset ID for this area's region, and the MREA asset ID for this area."""
        region, area = self.game.region_list.region_and_area_by_area_identifier(identifier)
        return self._asset_id_for_region(region), area.extra["asset_id"]

    def _area_reference_from_identifier(self, identifier: AreaIdentifier) -> dict:
        """Returns a patcher-format dict for the given area."""
        mlvl_id, mrea_id = self._asset_ids_for_area(identifier)
        return {
            "mlvl_id": mlvl_id,
            "mrea_id": mrea_id,
        }

    def create_starting_items_data(self) -> list[dict]:
        """Returns a patcher-format dict for starting items."""
        result = []

        for item, amount in self.patches.starting_resources().as_resource_gain():
            assert isinstance(item, ItemResourceInfo)
            item_id = item.extra["item_id"]

            result.append(
                {
                    "item": item_id,
                    "capacity": amount,
                }
            )

        return result

    def _populate_area_changes(
        self,
        area_changes: dict[tuple[int, int], AreaChange],
        field_name: Literal["pickups", "translator_gates", "door_locks", "elevators", "portals"],
        area_change_factory: Callable[[], Iterable[tuple[int, int, dict]]],
    ) -> None:
        """Populates `area_changes` with the results from the given change factory."""
        for mlvl_id, mrea_id, change in area_change_factory():
            container = area_changes[mlvl_id, mrea_id]
            if field_name not in container:
                container[field_name] = []
            container[field_name].append(change)

    def create_world_changes(self) -> list[dict]:
        """
        Returns a patcher-format dict for world changes.
        This includes pickups, translator gates, and door locks.
        """

        def _area_change() -> AreaChange:
            return AreaChange()

        # (MLVL, MREA) -> AreaChange
        area_changes: dict[tuple[int, int], AreaChange] = defaultdict(_area_change)

        # populate area changes
        self._populate_area_changes(area_changes, "pickups", self.create_pickups)
        self._populate_area_changes(area_changes, "translator_gates", self.create_translator_gates)
        self._populate_area_changes(area_changes, "door_locks", self.create_door_locks)
        self._populate_area_changes(area_changes, "elevators", self.create_elevators)
        self._populate_area_changes(area_changes, "portals", self.create_portals)

        # associate area changes with their world
        def _world_change() -> WorldChange:
            return WorldChange(area_changes=[])

        world_changes: dict[int, WorldChange] = defaultdict(_world_change)
        for (mlvl_id, mrea_id), area_change in area_changes.items():
            world_changes[mlvl_id]["area_changes"].append(
                {
                    "mrea_id": mrea_id,
                    **area_change,
                }
            )

        self.change_worlds_for_elevators(world_changes)

        # return world changes formatted for the patcher
        return [
            {
                "mlvl_id": mlvl_id,
                **world_change,
            }
            for mlvl_id, world_change in world_changes.items()
        ]

    def _get_memo_data(self) -> dict[str, str]:
        """Memo data to use when exporting pickups."""
        if self.cosmetic_patches.disable_hud_popup:
            return simplified_prime2_memo_data()

        else:
            result = default_prime2_memo_data()

            # TODO: add preset settings for this and adjust dynamically
            result["Massive Damage"] = "Massive Damage acquired!\nDamage dealt increased by 100%."

            return result

    @functools.cached_property
    def sound_data(self) -> dict[SoundType, int]:
        """Which sound ID to use for given SoundType."""
        return {
            "standard": 10057,
            "expansion": 10057,
            "key": 1075,
        }

    @functools.cached_property
    def jingle_data(self) -> dict[SoundType, dict]:
        """Which jingle to use for given SoundType."""
        return {
            "standard": {"file_name": "/audio/itm_x_long_00.dsp", "volume": 71},
            "expansion": {"file_name": "/audio/itm_x_short_00.dsp", "volume": 55},
            "key": {"file_name": "/audio/skytenkey-jin-short32.dsp", "volume": 110},
        }

    def _get_sound_type(self, model_name: str) -> SoundType:
        """Which SoundType to use for a given model."""
        sound_type: SoundType = "standard"

        if model_name in {
            "SkyTempleKey",
            "DarkTempleKey",
            # "AgonTempleKey",
            # "TorvusTempleKey",
            # "HiveTempleKey",
            "EnergyTransferModule",
        }:
            sound_type = "key"

        elif model_name in {
            "MissileExpansion",
            "MissileExpansionLarge",
            "MissileExpansionPrime1",
            "PowerBombExpansion",
            "DarkBeamAmmoExpansion",
            "LightBeamAmmoExpansion",
            "BeamAmmoExpansion",
            "EnergyTank",
            "EnergyTankSmall",
        }:
            sound_type = "expansion"

        return sound_type

    @property
    def _progressive_model_data(self) -> dict[str, tuple[str, tuple[str, ...]]]:
        """
        Maps model names to their progressive model data, if necessary.
        Standalone string is the model to use for offworld pickups.
        Tuple of strings is the model to use for each stage of this
        progressive pickup, when local.
        """
        return {
            "ProgressiveSuit": ("VariaSuit", ("DarkSuit", "LightSuit")),
            "ProgressiveGrapple": ("GrappleBeam", ("GrappleBeam", "ScrewAttack")),
        }

    @property
    def _door_dock_type(self) -> DockType:
        return self.game.dock_weakness_database.find_type("door")

    @property
    def _elevator_dock_type(self) -> DockType:
        return self.game.dock_weakness_database.find_type("elevator")

    @property
    def _portal_dock_type(self) -> DockType:
        return self.game.dock_weakness_database.find_type("portal")

    def _get_pickup_appearance(self, exported_pickup: pickup_exporter.ExportedPickupDetails, index: int) -> dict:
        """Returns a patcher-format dict for this pickup stage's appearance."""
        model_name = exported_pickup.model.name
        scan = f"{exported_pickup.name}. {exported_pickup.description}".strip()

        if model_name in self._progressive_model_data:
            default_model, progressive_models = self._progressive_model_data[model_name]

            if (
                self.configuration.pickup_model_style != PickupModelStyle.ALL_VISIBLE
                or exported_pickup.is_for_remote_player
            ):
                # fall back to the default model, since the local pickup may not be progressive!
                model_name = default_model

            else:
                # use the correct model for each stage of the pickup
                model_name = progressive_models[index]
                name = exported_pickup.conditional_resources[index].name
                scan = f"{name}."

        sound_type = self._get_sound_type(model_name)

        return {
            "model_data": model_name,
            "sound": self.sound_data[sound_type],
            "jingle": self.jingle_data[sound_type],
            "hud_text": exported_pickup.collection_text[index],
            "scan": scan,
        }

    def _get_pickup_resources(self, exported_pickup: pickup_exporter.ExportedPickupDetails, index: int) -> list[dict]:
        """Returns a patcher-format dict for this pickup stage's resources."""
        # TODO: multiworld

        conditional = exported_pickup.conditional_resources[index]

        return [
            {
                "item": resource.extra["item_id"],
                "amount": quantity,
            }
            for resource, quantity in conditional.resources
            if quantity != 0
        ]

    def _get_pickup_stage(self, exported_pickup: pickup_exporter.ExportedPickupDetails, index: int) -> dict:
        """
        Returns a patcher-format dict for this pickup stage,
        not including a progressive stage's item requirement.
        """

        return {
            "resources": self._get_pickup_resources(exported_pickup, index),
            "appearance": self._get_pickup_appearance(exported_pickup, index),
            "conversion": [
                {
                    "from_item": conversion.source.extra["item_id"],
                    "to_item": conversion.target.extra["item_id"],
                }
                for conversion in exported_pickup.conversion
            ],
        }

    def _get_location_data(self, pickup_node: PickupNode) -> dict:
        """Returns a patcher-format dict for this pickup node's location data."""
        result = {}
        result.update(frozen_lib.unwrap(pickup_node.extra["location_data"]))
        if "instances" in result:
            result.update(result.pop("instances"))

        if "connections" in result:
            for con in result["connections"]:
                con["state"] = "ZERO"

        if result["type"] == "custom":
            assert pickup_node.location is not None
            result["position"] = {
                "x": pickup_node.location.x,
                "y": pickup_node.location.y,
                "z": pickup_node.location.z,
            }

        return result

    def create_pickups(self) -> Iterable[tuple[int, int, dict]]:
        """Creates the pickup changes, in a format usable for `_populate_area_changes`"""
        pickup_list = echoes_raw_pickup_list(
            self._get_memo_data(),
            self.configuration,
            self.game,
            self.patches,
            self.players_config,
            self.rng,
        )

        for exported_pickup in pickup_list:
            pickup_node = self.game.region_list.node_from_pickup_index(exported_pickup.index)
            mlvl, mrea = self._asset_ids_for_area(pickup_node.identifier.area_identifier)

            pickup = {
                "location": self._get_location_data(pickup_node),
                "primary_stage": self._get_pickup_stage(exported_pickup, 0),
                "progressive_stages": [
                    {
                        **self._get_pickup_stage(exported_pickup, i + 1),
                        "required_item": conditional.item.extra["item_id"],
                    }
                    for i, conditional in enumerate(exported_pickup.conditional_resources[1:])
                    if conditional.item is not None
                ],
            }
            yield mlvl, mrea, pickup

    def create_translator_gates(self) -> Iterable[tuple[int, int, dict]]:
        """Creates the translator gate changes, in a format usable for `_populate_area_changes`"""
        for identifier, requirement in self.patches.game_specific["translator_gates"].items():
            node = self.game.region_list.node_by_identifier(NodeIdentifier.from_string(identifier))
            mlvl, mrea = self._asset_ids_for_area(node.identifier.area_identifier)

            if requirement == "removed":
                requirement = "unlocked"

            gate = {
                "translator": requirement,
                **node.extra.get("gate_instances", {}),
            }
            yield mlvl, mrea, gate

    def create_door_locks(self) -> Iterable[tuple[int, int, dict]]:
        """Creates the door lock changes, in a format usable for `_populate_area_changes`"""
        for dock, weakness in self.patches.all_dock_weaknesses(self.game, self._door_dock_type):
            mlvl, mrea = self._asset_ids_for_area(dock.identifier.area_identifier)

            door_lock = {
                "dock_name": dock.extra["dock_name"],
                "old_door_type": dock.default_dock_weakness.extra["door_type"],
                "new_door_type": weakness.extra["door_type"],
            }

            yield mlvl, mrea, door_lock

    def _should_auto_enable_elevators(self) -> bool:
        """Elevators are automatically enabled when the player doesn't start with Scan Visor."""
        pickup_config = self.configuration.standard_pickup_configuration
        scan_pickup = pickup_config.get_pickup_with_name("Scan Visor")
        return pickup_config.pickups_state[scan_pickup].num_included_in_starting_pickups == 0

    def create_elevators(self) -> Iterable[tuple[int, int, dict]]:
        """Creates the elevator target changes, in a format usable for `_populate_area_changes`"""
        for node, connection in self.patches.all_dock_connections(self.game, self._elevator_dock_type):
            mlvl, mrea = self._asset_ids_for_area(node.identifier.area_identifier)

            elevator = {
                "elevator_id": node.extra["teleporter_instance_id"],
                "target": self._area_reference_from_identifier(connection.identifier.area_identifier),
                "scan_strg": node.extra["scan_asset_id"],
                "target_name": elevators.get_elevator_or_area_name(connection, True),
            }

            yield mlvl, mrea, elevator

    def create_portals(self) -> Iterable[tuple[int, int, dict]]:
        """Creates the portal target changes, in a format usable for `_populate_area_changes`"""
        for node, connection in self.patches.all_dock_connections(self.game, self._portal_dock_type):
            target_dock = self.game.typed_node_by_identifier(connection.identifier, DockNode)

            mlvl, mrea = self._asset_ids_for_area(node.identifier.area_identifier)

            change = {
                "source_dock_name": node.extra["dock_name"],
                "target_mrea_id": self._asset_ids_for_area(target_dock.identifier.area_identifier)[1],
                "target_dock_name": target_dock.extra["dock_name"],
                "portal_scan_destination": target_dock.identifier.area,
            }
            yield mlvl, mrea, change

    def change_worlds_for_elevators(self, world_changes: dict[int, WorldChange]) -> None:
        """Sets the other fields in the WorldChanges and AreaChanges based on the elevator layout."""
        # update room names
        for node, connection in self.patches.all_dock_connections(self.game, self._elevator_dock_type):
            mlvl, mrea = self._asset_ids_for_area(node.identifier.area_identifier)
            world_change = world_changes[mlvl]
            area_change = next(area for area in world_change["area_changes"] if area["mrea_id"] == mrea)
            area_change["new_name"] = pretty_name_for_elevator(
                self.game, self.game.region_list, node, connection.identifier, use_ui_name_when_vanilla=True
            )

        # move regions on world map
        if self.configuration.teleporters.mode == TeleporterShuffleMode.ECHOES_SHUFFLED:

            def tg_elevator(area: str, node: str) -> DockNode:
                id_ = NodeIdentifier.create("Temple Grounds", area, node)
                return self.game.region_list.typed_node_by_identifier(id_, DockNode)

            tg_elevators = {
                tg_elevator("Temple Transport A", "Elevator to Great Temple"): "Great Temple",
                tg_elevator("Transport to Agon Wastes", "Elevator to Agon Wastes"): "Agon Wastes",
                tg_elevator("Transport to Torvus Bog", "Elevator to Torvus Bog"): "Torvus Bog",
                tg_elevator("Transport to Sanctuary Fortress", "Elevator to Sanctuary Fortress"): "Sanctuary Fortress",
            }
            for elevator, og_region_name in tg_elevators.items():
                og_region = self.game.region_list.region_with_name(og_region_name)
                target = self.patches.get_dock_connection_for(elevator)
                new_region = self.game.region_list.region_with_name(target.region)

                world_changes[self._asset_id_for_region(new_region)]["other_world_to_copy_in_mapu"] = (
                    self._asset_id_for_region(og_region)
                )

    def create_damage_changes(self) -> dict:
        """Returns a patcher-format dict for various damage changes."""
        varia_damage = self.configuration.varia_suit_damage
        dark_damage = self.configuration.dark_suit_damage

        if not varia_damage:
            raise ZeroDivisionError("Varia Suit damage cannot be 0!")

        return {
            "energy_per_tank": self.configuration.energy_per_tank,
            "safe_zone_heal_per_second": self.configuration.safe_zone.heal_per_second,
            "dangerous_energy_tanks": self.configuration.dangerous_energy_tank,
            "dark_world_damage": varia_damage,
            "dark_suit_protection": dark_damage / varia_damage,
        }

    def _get_string_change(self, strg_id: int, strings: list[str]) -> dict:
        """Return a patcher-format dict for a given string change."""
        return {
            "strg_id": strg_id,
            "strings": strings,
        }

    def _create_stk_hints(self, namer: EchoesHintNamer) -> list[dict]:
        """Returns a list of string changes to apply for the STK hints."""
        stk_mode = self.configuration.hints.specific_pickup_hints["sky_temple_keys"]
        if stk_mode == SpecificPickupHintMode.DISABLED:
            return hints.hide_stk_hints(namer)
        else:
            return hints.create_stk_hints(
                self.description.all_patches,
                self.players_config,
                self.game.get_resource_database_view(),
                namer,
                hide_area=(stk_mode == SpecificPickupHintMode.HIDE_AREA),
            )

    def _create_red_key_hints(self, namer: EchoesHintNamer) -> list[dict]:
        """Returns a list of string changes to apply for the Dark Temple Key hints."""
        red_key_mode = self.configuration.hints.specific_pickup_hints["dark_temple_keys"]

        strg_ids = {
            HintDarkTemple.AGON_WASTES: 0xE858FBB5,
            HintDarkTemple.TORVUS_BOG: 0x706A874F,
            HintDarkTemple.SANCTUARY_FORTRESS: 0x7D3C74C2,
        }

        key_hints = []

        for temple, strg_id in strg_ids.items():
            if red_key_mode == SpecificPickupHintMode.DISABLED:
                temple_name = namer.format_temple_name(temple.name, with_color=True)
                hint = f"The keys to {temple_name} are hidden somewhere."
            else:
                hint = create_temple_key_hint(
                    self.description.all_patches,
                    self.players_config.player_index,
                    temple,
                    namer,
                    with_color=True,
                )

            key_hints.append(hints.create_simple_logbook_hint(strg_id, hint))

        return key_hints

    def create_string_changes(self) -> list[dict]:
        """Returns a patcher-format list of string changes to apply."""
        string_patches = []

        hint_exporter = self.create_hint_exporter(ECHOES_JOKE_HINTS)
        namer = hint_exporter.namer
        assert isinstance(namer, EchoesHintNamer)

        # tournament champions
        string_patches.extend(akul_testament_string_patch(hint_exporter.namer))

        # hints
        string_patches.extend(hints.create_patches_hints(self.patches, hint_exporter))
        string_patches.extend(self._create_stk_hints(namer))
        string_patches.extend(self._create_red_key_hints(namer))

        # convert old patcher format to new format
        return [
            self._get_string_change(
                patch["asset_id"],
                patch["strings"],
            )
            if "asset_id" in patch
            else patch
            for patch in string_patches
        ]

    def create_map_visibility(self) -> dict:
        """Returns a patcher-format dict for minimap visibility changes."""
        if not self.configuration.teleporters.is_vanilla:
            exclude_map_ids = _ELEVATOR_ROOMS_MAP_ASSET_IDS
        else:
            exclude_map_ids = []

        return {
            "reveal_map_at_start": self.cosmetic_patches.open_map,
            "unvisited_room_names": self.cosmetic_patches.open_map,
            "areas_to_never_reveal": exclude_map_ids,
            "unvisited_map_icons": self.cosmetic_patches.reveal_all_map_icons,
        }

    def create_suit_mapping(self) -> dict:
        """Returns a patcher-format dict for custom suit changes."""
        suit_rng = Random(self.description.get_seed_for_world(self.players_config.player_index))

        suits = self.cosmetic_patches.suit_colors.randomized(suit_rng).as_json
        suits.pop("randomize_separately")

        return suits

    def _percent_and_max_count_for_custom_pickup(self, pickup_name: str, percentage_field: str) -> tuple[float, int]:
        """Gets the percentage modifier and the maximum count for this custom item."""
        pickup_config = self.configuration.standard_pickup_configuration.pickups_state
        pickup = self.game.get_pickup_database().standard_pickups[pickup_name]
        max_count = pickup_config[pickup].num_shuffled_pickups

        percent = getattr(self.configuration, percentage_field) / 100.0

        return percent, max_count

    def create_custom_items_config(self) -> dict:
        """Returns a patcher-format dict for custom item changes."""

        defense_up = self._percent_and_max_count_for_custom_pickup("Defense Up", "damage_reduction_per_defense_up")
        massive_damage = self._percent_and_max_count_for_custom_pickup(
            "Massive Damage", "damage_increase_per_massive_damage"
        )

        return {
            "defense_up_config": {
                "damage_reduction_multiplier": defense_up[0],
                "max_count": max(defense_up[1], 1),
            },
            "massive_damage_config": {
                "damage_increase_multiplier": massive_damage[0],
                "max_count": max(massive_damage[1], 1),
            },
        }

    def create_hud_color(self) -> dict:
        """Returns a patcher-format dict for HUD color changes."""

        color: tuple[float, float, float] = self.cosmetic_patches.hud_color
        r, g, b = color
        r /= 255
        g /= 255
        b /= 255

        return {
            "main_color": [r, g, b],
            "change_text_color": self.cosmetic_patches.apply_hud_color_to_text,
            "change_beam_visor_select_color": self.cosmetic_patches.apply_hud_color_to_beams_visors,
        }
