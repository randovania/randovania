from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.exporter import item_names, pickup_exporter
from randovania.exporter.hints import credits_spoiler, guaranteed_item_hint
from randovania.exporter.hints.hint_exporter import HintExporter
from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.pickup.pickup_entry import PickupModel
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.games.game import RandovaniaGame
from randovania.games.samus_returns.exporter.hint_namer import MSRHintNamer
from randovania.games.samus_returns.exporter.joke_hints import JOKE_HINTS
from randovania.games.samus_returns.layout.hint_configuration import ItemHintMode
from randovania.generator.pickup_pool import pickup_creator

if TYPE_CHECKING:
    from collections.abc import Iterator
    from random import Random

    from randovania.exporter.pickup_exporter import ExportedPickupDetails
    from randovania.game_description.db.area import Area
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.pickup.pickup_entry import ConditionalResources, PickupEntry
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.games.samus_returns.layout.msr_configuration import MSRConfiguration
    from randovania.games.samus_returns.layout.msr_cosmetic_patches import MSRCosmeticPatches

_ALTERNATIVE_MODELS = {
    PickupModel(RandovaniaGame.METROID_SAMUS_RETURNS, "Nothing"): ["itemsphere"],
    PickupModel(RandovaniaGame.METROID_SAMUS_RETURNS, "PROGRESSIVE_BEAM"): [
        "powerup_wavebeam",
        "powerup_spazerbeam",
        "powerup_plasmabeam",
    ],
    PickupModel(RandovaniaGame.METROID_SAMUS_RETURNS, "PROGRESSIVE_JUMP"): [
        "powerup_highjumpboots",
        "powerup_spacejump",
    ],
    PickupModel(RandovaniaGame.METROID_SAMUS_RETURNS, "PROGRESSIVE_SUIT"): ["powerup_variasuit", "powerup_gravitysuit"],
}


def get_item_id_for_item(item: ResourceInfo) -> str:
    assert isinstance(item, ItemResourceInfo)
    if "item_capacity_id" in item.extra:
        return item.extra["item_capacity_id"]
    try:
        return item.extra["item_id"]
    except KeyError as e:
        raise KeyError(f"{item.long_name} has no item ID.") from e


def get_export_item_id_for_item(item: ResourceInfo) -> str:
    assert isinstance(item, ItemResourceInfo)
    if "item_export_id" in item.extra:
        return item.extra["item_export_id"]
    return get_item_id_for_item(item)


def convert_conditional_resource(res: ConditionalResources) -> Iterator[dict]:
    if not res.resources:
        yield {"item_id": "ITEM_NONE", "quantity": 0}
        return

    for resource in reversed(res.resources):
        item_id = get_export_item_id_for_item(resource[0])
        quantity = resource[1]

        yield {"item_id": item_id, "quantity": quantity}


def get_resources_for_details(
    pickup: PickupEntry, conditional_resources: list[ConditionalResources], other_player: bool
) -> list[list[dict]]:
    resources = [
        list(convert_conditional_resource(conditional_resource))
        for conditional_resource in conditional_resources
        if conditional_resource.item is None or not pickup.respects_lock  # skip over temporary items
    ]

    # don't add more resources for multiworld items
    if other_player:
        return resources

    if pickup.resource_lock is not None and not pickup.respects_lock and not pickup.unlocks_resource:
        # Add the lock resource into the pickup in addition to the expansion's resources
        assert len(resources) == 1
        # prepend the main item
        resources[0].insert(
            0,
            {
                "item_id": get_export_item_id_for_item(pickup.resource_lock.locked_by),
                "quantity": 1,
            },
        )

    return resources


class MSRPatchDataFactory(PatchDataFactory):
    cosmetic_patches: MSRCosmeticPatches
    configuration: MSRConfiguration

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memo_data = MSRAcquiredMemo.with_expansion_text()

        tank = self.configuration.energy_per_tank
        self.memo_data["Energy Tank"] = f"Energy Tank acquired.\nEnergy capacity increased by {tank:g}."

    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.METROID_SAMUS_RETURNS

    def _calculate_starting_inventory(self, resources: ResourceCollection) -> dict[str, int]:
        result = {}
        resource_gain = [
            (resource, quantity)
            for resource, quantity in resources.as_resource_gain()
            if not resource.long_name.startswith("Locked")
        ]
        for resource, quantity in resource_gain:
            try:
                result[get_export_item_id_for_item(resource)] = quantity
            except KeyError:
                print(f"Skipping {resource} for starting inventory: no item id")
                continue
        result["ITEM_MAX_LIFE"] = self.configuration.starting_energy
        result["ITEM_MAX_SPECIAL_ENERGY"] = result.pop("ITEM_MAX_SPECIAL_ENERGY", 0) + self.configuration.starting_aeion
        return result

    def _starting_inventory_text(self) -> list[str]:
        result = ["Random starting items:"]
        items = item_names.additional_starting_equipment(self.configuration, self.game, self.patches)
        if not items:
            return []
        result.extend(items)
        return result

    def _start_point_ref_for(self, node: Node) -> dict:
        region = self.game.region_list.nodes_to_region(node)
        level_name: str = region.extra["scenario_id"]

        if "start_point_actor_name" in node.extra:
            return {
                "scenario": level_name,
                "actor": node.extra["start_point_actor_name"],
            }
        else:
            return {}

    def _key_error_for_node(self, node: Node, err: KeyError) -> KeyError:
        return KeyError(f"{self.game.region_list.node_name(node, with_region=True)} has no extra {err}")

    def _level_name_for(self, node: Node) -> str:
        region = self.game.region_list.nodes_to_region(node)
        return region.extra["scenario_id"]

    def _teleporter_ref_for(self, node: Node, actor_key: str = "actor_name") -> dict:
        try:
            return {
                "scenario": self._level_name_for(node),
                "actor": node.extra[actor_key],
            }
        except KeyError as e:
            raise self._key_error_for_node(node, e)

    def _callback_ref_for(self, node: Node) -> dict:
        try:
            return {
                "scenario": self._level_name_for(node),
                "spawngroup": node.extra["spawngroup"],
            }
        except KeyError as e:
            raise KeyError(f"{node} has no extra {e}")

    def _pickup_detail_for_target(self, detail: ExportedPickupDetails) -> dict | None:
        alt_model = _ALTERNATIVE_MODELS.get(detail.model, [detail.model.name])
        model_names = alt_model

        resources = get_resources_for_details(detail.original_pickup, detail.conditional_resources, detail.other_player)

        pickup_node = self.game.region_list.node_from_pickup_index(detail.index)
        pickup_type = pickup_node.extra.get("pickup_type", "actor")

        # FIXME: Wild hack. This actually requires a patcher change to be able to export the locked text
        # and the unlocked text
        hud_text = detail.collection_text[0]
        if hud_text.startswith("Locked"):
            hud_text = detail.collection_text[1]
        elif len(set(detail.collection_text)) > 1:
            hud_text = self.memo_data[detail.original_pickup.name]

        details = {"pickup_type": pickup_type, "caption": hud_text, "resources": resources}

        if pickup_type == "actor":
            pickup_actor = self._teleporter_ref_for(pickup_node)
            details.update(
                {
                    "pickup_actor": pickup_actor,
                    "model": model_names,
                }
            )
        else:
            details["metroid_callback"] = self._callback_ref_for(pickup_node)

        return details

    def _encode_hints(self, rng: Random) -> list[dict]:
        namer = MSRHintNamer(self.description.all_patches, self.players_config)
        exporter = HintExporter(namer, self.rng, ["A joke hint."])

        hints = [
            {
                "accesspoint_actor": self._teleporter_ref_for(logbook_node),
                "text": exporter.create_message_for_hint(
                    self.patches.hints[self.game.region_list.identifier_for_node(logbook_node)],
                    self.description.all_patches,
                    self.players_config,
                    True,
                ),
            }
            for logbook_node in self.game.region_list.iterate_nodes()
            if isinstance(logbook_node, HintNode)
        ]

        artifacts = [self.game.resource_database.get_item(f"Metroid DNA {i + 1}") for i in range(39)]
        dna_hint_mapping = {}
        hint_config = self.configuration.hints
        if hint_config.artifacts != ItemHintMode.DISABLED:
            dna_hint_mapping = guaranteed_item_hint.create_guaranteed_hints_for_resources(
                self.description.all_patches,
                self.players_config,
                MSRHintNamer(self.description.all_patches, self.players_config),
                hint_config.artifacts == ItemHintMode.HIDE_AREA,
                artifacts,
                False,
            )
        else:
            dna_hint_mapping = {k: f"{k.long_name} is hidden somewhere on SR388." for k in artifacts}

        # Shuffle DNA hints
        hint_texts = list(dna_hint_mapping.values())
        rng.shuffle(hint_texts)
        dna_hint_mapping = dict(zip(artifacts, hint_texts))

        dud_hint = "This Chozo Seal did not give any useful DNA hints."
        actor_to_amount_map = [
            ("s010_area1", "LE_RandoDNA", 0, 4),
            ("s020_area2", "LE_RandoDNA", 4, 9),
            ("s033_area3b", "LE_RandoDNA", 9, 15),
            ("s050_area5", "LE_RandoDNA", 15, 19),
            ("s065_area6b", "LE_RandoDNA", 19, 24),
            ("s070_area7", "LE_RandoDNA_001", 24, 27),
            ("s070_area7", "LE_RandoDNA_002", 27, 30),
            ("s090_area9", "LE_RandoDNA", 30, 33),
            ("s100_area10", "LE_RandoDNA", 33, 38),
            ("s110_surfaceb", "LE_RandoDNA", 38, 39),
        ]

        for scenario, actor, start, end in actor_to_amount_map:
            shuffled_hints = list(dna_hint_mapping.values())[start:end]
            shuffled_hints = [hint for hint in shuffled_hints if "Hunter already started with" not in hint]
            if not shuffled_hints:
                shuffled_hints = [rng.choice(JOKE_HINTS + [dud_hint])]
            hints.append(
                {"accesspoint_actor": {"scenario": scenario, "actor": actor}, "text": "\n".join(shuffled_hints) + "\n"}
            )

        return hints

    def _node_for(self, identifier: NodeIdentifier) -> Node:
        return self.game.region_list.node_by_identifier(identifier)

    def _static_text_changes(self) -> dict[str, str]:
        full_hash = f"{self.description.shareable_word_hash} ({self.description.shareable_hash})"
        text = {}
        difficulty_labels = {
            "GUI_MSG_NEW_FILE_CREATION",
            "GUI_MSG_NEW_GAME_CONFIRMATION",
            "GUI_MSG_NEW_GAME_CONFIRMATION_NORMAL",
            "GUI_MSG_NEW_GAME_CONFIRMATION_HARD",
            "GUI_MSG_NEW_GAME_CONFIRMATION_FUSION",
        }
        for difficulty in difficulty_labels:
            text[difficulty] = full_hash

        text["GUI_SAMUS_DATA_TITLE"] = "<version>"

        location_text = ""
        if self.configuration.artifacts.prefer_anywhere:
            location_text = "at any location"
        else:
            restricted_text = []
            if self.configuration.artifacts.prefer_metroids:
                restricted_text.append("on Standard Metroids")
            if self.configuration.artifacts.prefer_stronger_metroids:
                restricted_text.append("on Stronger Metroids")
            if self.configuration.artifacts.prefer_bosses:
                restricted_text.append("on Bosses")
            location_text = "{}{}{}".format(
                ", ".join(restricted_text[:-1]), " and " if len(restricted_text) > 1 else "", restricted_text[-1]
            )

        # Intro Text
        text[
            "GUI_CUTSCENE_OPENING_1"
        ] = "Welcome to the Metroid: Samus Returns Randomizer!|Here are some useful tips to help you on your journey."
        text["GUI_CUTSCENE_OPENING_2"] = (
            "All of the hazardous liquid has been drained. You can thus freely explore the planet.|"
            "Metroids now also drop items."
        )
        text["GUI_CUTSCENE_OPENING_3"] = (
            "In this randomizer, you need to collect all Metroid DNA, find the Baby, "
            "and then fight Proteus Ridley at your ship to leave the planet."
        )
        text["GUI_CUTSCENE_OPENING_4"] = (
            f"With your current configuration, you need to find {self.configuration.artifacts.required_artifacts} DNA. "
            f"It can be found {location_text}."
        )
        text["GUI_CUTSCENE_OPENING_5"] = (
            "You may freely travel between Surface and Area 8.|"
            "Once you have collected all the required DNA, "
            "going from Area 8 to Surface will force a confrontation with Proteus Ridley."
        )
        text["GUI_CUTSCENE_OPENING_6"] = (
            "All the Chozo Seals have been repurposed to give hints on the region where a specific item is located.|"
            "Additionally, more distinct Chozo Seals have been placed that give hints on DNA locations."
        )
        text[
            "GUI_CUTSCENE_OPENING_7"
        ] = "If you're interested in knowing more on how the DNA Seals work, you can check the Hint page in Randovania."
        text["GUI_CUTSCENE_OPENING_8"] = (
            "Some other helpful tips:|You can warp to your starting location by cancelling the save at a Save Station.|"
            "Scan Pulse can be used to reveal more of your map."
        )
        text[
            "GUI_CUTSCENE_OPENING_9"
        ] = "If you still have more questions, check out the FAQ and Differences pages in Randovania."
        text["GUI_CUTSCENE_OPENING_10"] = "Good luck and have fun!"

        return text

    def _credits_spoiler(self) -> dict[str, str]:
        return credits_spoiler.generic_credits(
            self.configuration.standard_pickup_configuration,
            self.description.all_patches,
            self.players_config,
            MSRHintNamer(self.description.all_patches, self.players_config),
        )

    def _static_room_name_fixes(self, scenario_name: str, area: Area) -> tuple[str, str]:
        # static fixes for some rooms
        cc_name = area.extra["asset_id"]
        if scenario_name == "s025_area2b":
            if cc_name == "collision_camera011":
                return cc_name, "Varia Suit Chamber & Interior Intersection Terminal"

        if scenario_name == "s065_area6b":
            if cc_name == "collision_camera_014":
                return cc_name, "Gamma+ Arena & Access"

        if scenario_name == "s100_area10":
            if cc_name == "collision_camera_008":
                return cc_name, "Metroid Nest Foyer & Hallway South"

        return cc_name, area.name

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

        return all_dict

    def _create_cosmetics(self) -> dict:
        c = self.cosmetic_patches
        cosmetic_patches: dict = {}
        # Game needs each color component in [0-1] range
        if self.cosmetic_patches.use_laser_color:
            cosmetic_patches["laser_locked_color"] = [x / 255 for x in c.laser_locked_color]
            cosmetic_patches["laser_unlocked_color"] = [x / 255 for x in c.laser_unlocked_color]

        if self.cosmetic_patches.use_grapple_laser_color:
            cosmetic_patches["grapple_laser_locked_color"] = [x / 255 for x in c.grapple_laser_locked_color]
            cosmetic_patches["grapple_laser_unlocked_color"] = [x / 255 for x in c.grapple_laser_unlocked_color]

        if self.cosmetic_patches.use_energy_tank_color:
            cosmetic_patches["energy_tank_color"] = [x / 255 for x in c.energy_tank_color]

        if self.cosmetic_patches.use_aeion_bar_color:
            cosmetic_patches["aeion_bar_color"] = [x / 255 for x in c.aeion_bar_color]

        if self.cosmetic_patches.use_ammo_hud_color:
            cosmetic_patches["ammo_hud_color"] = [x / 255 for x in c.ammo_hud_color]

        cosmetic_patches["enable_room_name_display"] = c.show_room_names.value
        cosmetic_patches["camera_names_dict"] = self._build_area_name_dict()

        return cosmetic_patches

    def create_data(self) -> dict:
        starting_location = self._start_point_ref_for(self._node_for(self.patches.starting_location))
        starting_items = self._calculate_starting_inventory(self.patches.starting_resources())
        starting_text = self._starting_inventory_text()

        useless_target = PickupTarget(
            pickup_creator.create_nothing_pickup(self.game.resource_database), self.players_config.player_index
        )

        pickup_list = pickup_exporter.export_all_indices(
            self.patches,
            useless_target,
            self.game.region_list,
            self.rng,
            self.configuration.pickup_model_style,
            self.configuration.pickup_model_data_source,
            exporter=pickup_exporter.create_pickup_exporter(self.memo_data, self.players_config, self.game_enum()),
            visual_nothing=pickup_creator.create_visual_nothing(self.game_enum(), "Nothing"),
        )

        energy_per_tank = self.configuration.energy_per_tank

        return {
            "starting_location": starting_location,
            "starting_items": starting_items,
            "starting_text": starting_text,
            "pickups": [
                data for pickup_item in pickup_list if (data := self._pickup_detail_for_target(pickup_item)) is not None
            ],
            "energy_per_tank": energy_per_tank,
            "reserves_per_tank": {
                "life_tank_size": self.configuration.life_tank_size,
                "aeion_tank_size": self.configuration.aeion_tank_size,
                "missile_tank_size": self.configuration.missile_tank_size,
                "super_missile_tank_size": self.configuration.super_missile_tank_size,
            },
            "game_patches": {
                "charge_door_buff": self.configuration.charge_door_buff,
                "beam_door_buff": self.configuration.beam_door_buff,
                "beam_burst_buff": self.configuration.beam_burst_buff,
                "nerf_super_missiles": self.configuration.nerf_super_missiles,
                "remove_elevator_grapple_blocks": self.configuration.elevator_grapple_blocks,
                "remove_grapple_block_area3_interior_shortcut": self.configuration.area3_interior_shortcut_no_grapple,
                "patch_surface_crumbles": self.configuration.surface_crumbles,
                "patch_area1_crumbles": self.configuration.area1_crumbles,
                "reverse_area8": self.configuration.reverse_area8,
            },
            "text_patches": self._static_text_changes(),
            "spoiler_log": self._credits_spoiler() if self.description.has_spoiler else {},
            "hints": self._encode_hints(self.rng),
            "cosmetic_patches": self._create_cosmetics(),
            "configuration_identifier": self.description.shareable_hash,
        }


class MSRAcquiredMemo(dict):
    def __missing__(self, key: str) -> str:
        return f"{key} acquired."

    @classmethod
    def with_expansion_text(cls) -> MSRAcquiredMemo:
        result = cls()
        result["Missile Tank"] = "Missile Tank acquired.\nMissile capacity increased by {Missile}."
        result[
            "Super Missile Tank"
        ] = "Super Missile Tank acquired.\nSuper Missile capacity increased by {Super Missile}."
        result["Power Bomb Tank"] = "Power Bomb Tank acquired.\nPower Bomb capacity increased by {Power Bomb}."
        result["Energy Tank"] = "Energy Tank acquired.\nEnergy capacity increased by 100."
        result["Aeion Tank"] = "Aeion Tank acquired.\nAeion Gauge expanded."
        return result
