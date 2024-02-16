from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.exporter import item_names
from randovania.game_description import default_database
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.pickup.pickup_entry import (
    ConditionalResources,
    PickupEntry,
    PickupModel,
    ResourceConversion,
)
from randovania.layout.base.pickup_model import PickupModelDataSource, PickupModelStyle

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.assignment import PickupTarget
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.game_description.resources.resource_info import ResourceGainTuple
    from randovania.games.game import RandovaniaGame
    from randovania.interface_common.players_configuration import PlayersConfiguration


def _conditional_resources_for_pickup(pickup: PickupEntry) -> list[ConditionalResources]:
    if len(pickup.progression) > 1:
        assert pickup.resource_lock is None, pickup.name
        return list(pickup.conditional_resources)

    else:
        resources = list(pickup.extra_resources)
        name = pickup.name
        if pickup.progression:
            name = pickup.progression[0][0].long_name
            resources.append(pickup.progression[0])

        lock = pickup.resource_lock
        # A lock that goes to the same item is ignored for the patcher, for simplification
        if (
            pickup.respects_lock
            and not pickup.unlocks_resource
            and lock is not None
            and lock.temporary_item != lock.item_to_lock
        ):
            locked_resources = lock.convert_gain(resources)
            return [
                ConditionalResources(
                    name=f"Locked {name}",
                    item=None,
                    resources=tuple(locked_resources),
                ),
                ConditionalResources(
                    name=name,
                    item=lock.locked_by,
                    resources=tuple(resources),
                ),
            ]
        else:
            return [
                ConditionalResources(
                    name=name,
                    item=None,
                    resources=tuple(resources),
                ),
            ]


def _pickup_description(pickup: PickupEntry) -> str:
    if not pickup.pickup_category.is_expansion:
        if len(pickup.progression) > 1:
            return "Provides the following in order: {}.".format(
                ", ".join(conditional.name for conditional in pickup.conditional_resources)
            )
        else:
            return ""

    ammo_desc = [
        (
            item_names.add_quantity_to_resource(item_names.resource_user_friendly_name(resource), abs(quantity), True),
            quantity < 0,
        )
        for resource, quantity in pickup.extra_resources
    ]
    if ammo_desc:
        positive_items = [name for name, negative in ammo_desc if not negative]
        negative_items = [name for name, negative in ammo_desc if negative]
        text = ""
        # First add all the positive items, then we add all the negative items. For the negative items, if we added
        # positive items before, we include a space character so that the sentence looks nice.
        if positive_items:
            text += _text_for_ammo_description(False, positive_items)
        if negative_items:
            if text:
                text += " "
            text += _text_for_ammo_description(True, negative_items)
        return text
    else:
        return ""


def _text_for_ammo_description(negative: bool, ammo_desc: list[str]) -> str:
    return "{} {}{}{}.".format(
        "Provides" if not negative else "Removes",
        ", ".join(ammo_desc[:-1]),
        " and " if len(ammo_desc) > 1 else "",
        ammo_desc[-1],
    )


def _get_single_hud_text(
    pickup_name: str,
    memo_data: dict[str, str],
    resources: ResourceGainTuple,
) -> str:
    return memo_data[pickup_name].format(
        **{
            **{item_names.resource_user_friendly_name(resource): abs(quantity) for resource, quantity in resources},
            **{
                item_names.resource_user_friendly_delta(resource): "increased" if quantity >= 0 else "decreased"
                for resource, quantity in resources
            },
        }
    )


def _get_all_hud_text(
    conditionals: list[ConditionalResources],
    memo_data: dict[str, str],
) -> list[str]:
    return [_get_single_hud_text(conditional.name, memo_data, conditional.resources) for conditional in conditionals]


def _calculate_collection_text(
    pickup: PickupEntry,
    visual_pickup: PickupEntry,
    model_style: PickupModelStyle,
    memo_data: dict[str, str],
) -> list[str]:
    """
    Calculates what the hud_text for a pickup should be
    :param pickup:
    :param visual_pickup:
    :param model_style:
    :param memo_data:
    :return:
    """

    if model_style == PickupModelStyle.HIDE_ALL:
        # TODO: this might not be correct, in case of custom offworld models for the pickups?
        if visual_pickup.model.game != pickup.model.game:
            memo_data = GenericAcquiredMemo()

        hud_text = _get_all_hud_text(_conditional_resources_for_pickup(visual_pickup), memo_data)
        num_conditional = len(_conditional_resources_for_pickup(pickup))
        if len(hud_text) == num_conditional:
            return hud_text
        else:
            return [hud_text[0]] * num_conditional

    else:
        return _get_all_hud_text(_conditional_resources_for_pickup(pickup), memo_data)


@dataclasses.dataclass(frozen=True)
class ExportedPickupDetails:
    index: PickupIndex
    name: str
    description: str
    collection_text: list[str]
    conditional_resources: list[ConditionalResources]
    conversion: list[ResourceConversion]
    model: PickupModel
    original_model: PickupModel
    other_player: bool
    original_pickup: PickupEntry


class PickupExporter:
    def __init__(self, game: RandovaniaGame) -> None:
        self.game = game

    def create_details(
        self,
        original_index: PickupIndex,
        pickup_target: PickupTarget,
        visual_pickup: PickupEntry,
        model_pickup: PickupEntry,
        model_style: PickupModelStyle,
        name: str,
        description: str,
    ) -> ExportedPickupDetails:
        raise NotImplementedError

    def get_model(self, model_pickup: PickupEntry) -> PickupModel:
        if self.game != model_pickup.model.game:
            return PickupModel(
                model_pickup.model.game,
                model_pickup.offworld_models.get(
                    self.game, default_database.pickup_database_for_game(self.game).default_offworld_model
                ),
            )
        else:
            return model_pickup.model

    def export(
        self,
        original_index: PickupIndex,
        pickup_target: PickupTarget,
        visual_pickup: PickupEntry,
        model_style: PickupModelStyle,
    ) -> ExportedPickupDetails:
        model_pickup = pickup_target.pickup if model_style == PickupModelStyle.ALL_VISIBLE else visual_pickup

        if model_style in {PickupModelStyle.ALL_VISIBLE, PickupModelStyle.HIDE_MODEL}:
            name = pickup_target.pickup.name
            description = _pickup_description(pickup_target.pickup)
        else:
            name = visual_pickup.name
            description = ""

        return self.create_details(
            original_index, pickup_target, visual_pickup, model_pickup, model_style, name, description
        )


class PickupExporterSolo(PickupExporter):
    def __init__(self, memo_data: dict[str, str], game: RandovaniaGame):
        self.memo_data = memo_data
        super().__init__(game)

    def create_details(
        self,
        original_index: PickupIndex,
        pickup_target: PickupTarget,
        visual_pickup: PickupEntry,
        model_pickup: PickupEntry,
        model_style: PickupModelStyle,
        name: str,
        description: str,
    ) -> ExportedPickupDetails:
        pickup = pickup_target.pickup
        return ExportedPickupDetails(
            index=original_index,
            name=name,
            description=description,
            collection_text=_calculate_collection_text(pickup, visual_pickup, model_style, self.memo_data),
            conditional_resources=_conditional_resources_for_pickup(pickup),
            conversion=list(pickup.convert_resources),
            model=self.get_model(model_pickup),
            original_model=model_pickup.model,
            other_player=False,
            original_pickup=pickup,
        )


class PickupExporterMulti(PickupExporter):
    def __init__(self, solo_creator: PickupExporter, players_config: PlayersConfiguration):
        self.solo_creator = solo_creator
        self.players_config = players_config
        super().__init__(self.solo_creator.game)

    def create_details(
        self,
        original_index: PickupIndex,
        pickup_target: PickupTarget,
        visual_pickup: PickupEntry,
        model_pickup: PickupEntry,
        model_style: PickupModelStyle,
        name: str,
        description: str,
    ) -> ExportedPickupDetails:
        """
        Exports a pickup, for a multiworld game.
        If for yourself, use the solo creator but adjust the name to mention it's yours.
        For offworld, create a custom details.
        """
        if pickup_target.player == self.players_config.player_index:
            details = self.solo_creator.create_details(
                original_index, pickup_target, visual_pickup, model_pickup, model_style, name, description
            )
            return dataclasses.replace(details, name=f"Your {details.name}")
        else:
            other_name = self.players_config.player_names[pickup_target.player]
            return ExportedPickupDetails(
                index=original_index,
                name=f"{other_name}'s {name}",
                description=description,
                collection_text=[f"Sent {name} to {other_name}!"],
                conditional_resources=[
                    ConditionalResources(
                        name=None,
                        item=None,
                        resources=(),
                    )
                ],
                conversion=[],
                model=self.get_model(model_pickup),
                original_model=model_pickup.model,
                other_player=True,
                original_pickup=pickup_target.pickup,
            )


def _get_visual_model(
    original_index: int,
    pickup_list: list[PickupTarget],
    data_source: PickupModelDataSource,
    visual_nothing: PickupEntry,
) -> PickupEntry:
    if data_source == PickupModelDataSource.ETM:
        return visual_nothing
    elif data_source == PickupModelDataSource.RANDOM:
        return pickup_list[original_index % len(pickup_list)].pickup
    elif data_source == PickupModelDataSource.LOCATION:
        raise NotImplementedError
    else:
        raise ValueError(f"Unknown data_source: {data_source}")


def export_all_indices(
    patches: GamePatches,
    useless_target: PickupTarget,
    region_list: RegionList,
    rng: Random,
    model_style: PickupModelStyle,
    data_source: PickupModelDataSource,
    exporter: PickupExporter,
    visual_nothing: PickupEntry,
) -> list[ExportedPickupDetails]:
    """
    Creates the patcher data for all pickups in the game
    :param patches:
    :param useless_target:
    :param region_list:
    :param rng:
    :param model_style:
    :param data_source:
    :param exporter:
    :param visual_nothing:
    :return:
    """
    pickup_assignment = patches.pickup_assignment

    pickup_list = list(pickup_assignment.values())
    rng.shuffle(pickup_list)

    indices = sorted(node.pickup_index for node in region_list.iterate_nodes() if isinstance(node, PickupNode))

    pickups = [
        exporter.export(
            index,
            pickup_assignment.get(index, useless_target),
            _get_visual_model(i, pickup_list, data_source, visual_nothing),
            model_style,
        )
        for i, index in enumerate(indices)
    ]

    return pickups


class GenericAcquiredMemo(dict):
    def __missing__(self, key):
        return f"{key} acquired!"


def create_pickup_exporter(memo_data: dict, players_config: PlayersConfiguration, game: RandovaniaGame):
    exporter = PickupExporterSolo(memo_data, game)
    if players_config.is_multiworld:
        exporter = PickupExporterMulti(exporter, players_config)
    return exporter
