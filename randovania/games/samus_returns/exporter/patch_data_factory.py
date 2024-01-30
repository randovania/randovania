from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.exporter import item_names, pickup_exporter
from randovania.exporter.hints import credits_spoiler
from randovania.exporter.hints.hint_exporter import HintExporter
from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.pickup.pickup_entry import PickupModel
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.games.game import RandovaniaGame
from randovania.games.samus_returns.exporter.hint_namer import MSRHintNamer
from randovania.generator.pickup_pool import pickup_creator

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.exporter.pickup_exporter import ExportedPickupDetails
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.pickup.pickup_entry import ConditionalResources, PickupEntry
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.games.samus_returns.layout.msr_configuration import MSRConfiguration

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

    def _encode_hints(self) -> list[dict]:
        namer = MSRHintNamer(self.description.all_patches, self.players_config)
        exporter = HintExporter(namer, self.rng, ["A joke hint."])

        return [
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

        return text

    def _credits_spoiler(self) -> dict[str, str]:
        return credits_spoiler.generic_credits(
            self.configuration.standard_pickup_configuration,
            self.description.all_patches,
            self.players_config,
            MSRHintNamer(self.description.all_patches, self.players_config),
        )

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
                "nerf_super_missiles": self.configuration.nerf_super_missiles,
                "remove_elevator_grapple_blocks": self.configuration.elevator_grapple_blocks,
                "remove_grapple_block_area3_interior_shortcut": self.configuration.area3_interior_shortcut_no_grapple,
                "patch_surface_crumbles": self.configuration.surface_crumbles,
                "patch_area1_crumbles": self.configuration.area1_crumbles,
                "reverse_area8": self.configuration.reverse_area8,
            },
            "text_patches": self._static_text_changes(),
            "spoiler_log": self._credits_spoiler() if self.description.has_spoiler else {},
            "hints": self._encode_hints(),
            "configuration_identifier": self.description.shareable_hash,
        }


class MSRAcquiredMemo(dict):
    def __missing__(self, key: str) -> str:
        return f"{key} acquired."

    @classmethod
    def with_expansion_text(cls) -> MSRAcquiredMemo:
        result = cls()
        result["Missile Tank"] = "Missile Tank acquired.\nMissile capacity increased by {Missile}."
        result["Super Missile Tank"] = (
            "Super Missile Tank acquired.\nSuper Missile capacity increased by {Super Missile}."
        )
        result["Power Bomb Tank"] = "Power Bomb Tank acquired.\nPower Bomb capacity increased by {Power Bomb}."
        result["Energy Tank"] = "Energy Tank acquired.\nEnergy capacity increased by 100."
        result["Aeion Tank"] = "Aeion Tank acquired.\nAeion Gauge expanded."
        return result
