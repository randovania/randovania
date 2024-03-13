from __future__ import annotations

import dataclasses
from random import Random
from unittest.mock import MagicMock

import pytest

from randovania.exporter import pickup_exporter
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.pickup.ammo_pickup import AMMO_PICKUP_CATEGORY
from randovania.game_description.pickup.pickup_category import USELESS_PICKUP_CATEGORY
from randovania.game_description.pickup.pickup_entry import (
    ConditionalResources,
    PickupEntry,
    PickupModel,
    ResourceConversion,
    ResourceLock,
)
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.generator.pickup_pool import pickup_creator
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.base.pickup_model import PickupModelDataSource, PickupModelStyle
from randovania.layout.base.standard_pickup_state import StandardPickupState


def test_get_single_hud_text_all_standard_pickups(echoes_pickup_database, echoes_resource_database):
    from randovania.games.prime2.exporter import patch_data_factory

    memo_data = patch_data_factory.default_prime2_memo_data()

    # Run
    for item in echoes_pickup_database.standard_pickups.values():
        pickup = pickup_creator.create_standard_pickup(
            item, StandardPickupState(included_ammo=tuple(0 for _ in item.ammo)), echoes_resource_database, None, False
        )

        result = pickup_exporter._get_all_hud_text(pickup_exporter._conditional_resources_for_pickup(pickup), memo_data)
        for i, progression in enumerate(pickup.progression):
            assert progression[0].long_name in result[i]
        assert result
        for line in result:
            assert len(line) > 10
            assert isinstance(line, str)


@pytest.mark.parametrize(
    "order",
    [
        ("X", "Y"),
        ("Y", "X"),
        ("Y", "Z"),
    ],
)
def test_calculate_hud_text(order: tuple[str, str], generic_pickup_category, default_generator_params):
    # Setup
    resource_a = ItemResourceInfo(0, "A", "A", 10)
    resource_b = ItemResourceInfo(1, "B", "B", 10)
    game = RandovaniaGame.BLANK

    pickup_x = PickupEntry(
        "A",
        PickupModel(game, "1"),
        generic_pickup_category,
        generic_pickup_category,
        progression=(((resource_a, 1),)),
        generator_params=default_generator_params,
    )
    pickup_y = PickupEntry(
        "Y",
        PickupModel(game, "2"),
        generic_pickup_category,
        generic_pickup_category,
        progression=(
            (resource_b, 1),
            (resource_a, 5),
        ),
        generator_params=default_generator_params,
    )
    pickup_z = PickupEntry(
        "Z",
        PickupModel(game, "2"),
        generic_pickup_category,
        generic_pickup_category,
        progression=(
            (resource_a, 1),
            (resource_b, 5),
        ),
        generator_params=default_generator_params,
    )

    memo_data = {
        "A": "You got {A} of A",
        "B": "You found {B} of B",
    }
    pickups = {
        "X": pickup_x,
        "Y": pickup_y,
        "Z": pickup_z,
    }

    # Run
    result = pickup_exporter._calculate_collection_text(
        pickups[order[0]], pickups[order[1]], PickupModelStyle.HIDE_ALL, memo_data
    )

    # Assert
    if order[1] == "Y":
        assert result == ["You found 1 of B"]
    elif order[1] == "X":
        assert result == ["You got 1 of A", "You got 1 of A"]
    else:
        assert result == ["You got 1 of A", "You found 5 of B"]


@pytest.mark.parametrize("model_style", PickupModelStyle)
def test_create_pickup_list(
    model_style: PickupModelStyle, empty_patches, generic_pickup_category, blank_resource_db, default_generator_params
):
    # Setup
    has_scan_text = model_style in {PickupModelStyle.ALL_VISIBLE, PickupModelStyle.HIDE_MODEL}
    rng = Random(5000)

    patches = dataclasses.replace(empty_patches, game=MagicMock())
    model_0 = MagicMock(spec=PickupModel)
    model_1 = MagicMock(spec=PickupModel)
    model_2 = MagicMock(spec=PickupModel)
    model_3 = MagicMock(spec=PickupModel)
    for m in [model_0, model_1, model_2, model_3]:
        m.game = RandovaniaGame.METROID_PRIME_ECHOES
    useless_model = PickupModel(
        game=RandovaniaGame.METROID_PRIME_ECHOES,
        name="EnergyTransferModule",
    )

    useless_resource = ItemResourceInfo(0, "Useless", "Useless", 10)
    resource_a = ItemResourceInfo(1, "A", "A", 10)
    resource_b = ItemResourceInfo(2, "B", "B", 10)
    resource_c = ItemResourceInfo(3, "C", "C", 10)
    pickup_a = PickupEntry(
        "P-A",
        model_1,
        generic_pickup_category,
        generic_pickup_category,
        progression=((resource_a, 1),),
        generator_params=default_generator_params,
    )
    pickup_b = PickupEntry(
        "P-B",
        model_2,
        generic_pickup_category,
        generic_pickup_category,
        progression=((resource_b, 1), (resource_a, 5)),
        generator_params=default_generator_params,
    )
    pickup_c = PickupEntry(
        "P-C",
        model_2,
        AMMO_PICKUP_CATEGORY,
        generic_pickup_category,
        progression=(),
        extra_resources=((resource_a, 1), (resource_c, -3)),
        unlocks_resource=True,
        resource_lock=ResourceLock(resource_a, resource_a, useless_resource),
        generator_params=default_generator_params,
    )
    pickup_d = PickupEntry(
        "P-D",
        model_2,
        AMMO_PICKUP_CATEGORY,
        generic_pickup_category,
        progression=(),
        extra_resources=((resource_b, 2), (resource_a, 1)),
        unlocks_resource=True,
        resource_lock=ResourceLock(resource_a, resource_a, useless_resource),
        generator_params=default_generator_params,
    )
    pickup_e = PickupEntry(
        "P-E",
        model_3,
        AMMO_PICKUP_CATEGORY,
        generic_pickup_category,
        progression=(),
        extra_resources=((resource_c, -3),),
        unlocks_resource=True,
        resource_lock=ResourceLock(resource_c, resource_c, useless_resource),
        generator_params=default_generator_params,
    )

    useless_pickup = PickupEntry(
        "P-Useless",
        model_0,
        USELESS_PICKUP_CATEGORY,
        USELESS_PICKUP_CATEGORY,
        progression=((useless_resource, 1),),
        generator_params=default_generator_params,
    )
    patches = patches.assign_new_pickups(
        [
            (PickupIndex(0), PickupTarget(pickup_a, 0)),
            (PickupIndex(2), PickupTarget(pickup_b, 0)),
            (PickupIndex(3), PickupTarget(pickup_a, 0)),
            (PickupIndex(4), PickupTarget(pickup_c, 0)),
            (PickupIndex(5), PickupTarget(pickup_d, 0)),
            (PickupIndex(6), PickupTarget(pickup_e, 0)),
        ]
    )
    creator = pickup_exporter.PickupExporterSolo(
        pickup_exporter.GenericAcquiredMemo(), RandovaniaGame.METROID_PRIME_ECHOES
    )

    region_list = MagicMock()
    region_list.iterate_nodes.return_value = [
        PickupNode(
            NodeIdentifier.create("World", "Area", f"Name {i}"),
            i,
            False,
            None,
            "",
            ("default",),
            {},
            False,
            PickupIndex(i),
            False,
        )
        for i in range(7)
    ]

    # Run
    result = pickup_exporter.export_all_indices(
        patches,
        PickupTarget(useless_pickup, 0),
        region_list,
        rng,
        model_style,
        PickupModelDataSource.ETM,
        creator,
        pickup_creator.create_visual_nothing(RandovaniaGame.METROID_PRIME_ECHOES, "EnergyTransferModule"),
    )

    # Assert
    assert len(result) == 7
    assert result[0] == pickup_exporter.ExportedPickupDetails(
        index=PickupIndex(0),
        name="P-A" if has_scan_text else "Unknown item",
        description="",
        collection_text=["A acquired!"] if model_style != PickupModelStyle.HIDE_ALL else ["Unknown item acquired!"],
        conditional_resources=[ConditionalResources("A", None, ((resource_a, 1),))],
        conversion=[],
        model=model_1 if model_style == PickupModelStyle.ALL_VISIBLE else useless_model,  # type: ignore [arg-type]
        original_model=model_1 if model_style == PickupModelStyle.ALL_VISIBLE else useless_model,  # type: ignore [arg-type]
        other_player=False,
        original_pickup=pickup_a,
    )
    assert result[1] == pickup_exporter.ExportedPickupDetails(
        index=PickupIndex(1),
        name="P-Useless" if has_scan_text else "Unknown item",
        description="",
        collection_text=(
            ["Useless acquired!"] if model_style != PickupModelStyle.HIDE_ALL else ["Unknown item acquired!"]
        ),
        conditional_resources=[ConditionalResources("Useless", None, ((useless_resource, 1),))],
        conversion=[],
        model=model_0 if model_style == PickupModelStyle.ALL_VISIBLE else useless_model,  # type: ignore [arg-type]
        original_model=model_0 if model_style == PickupModelStyle.ALL_VISIBLE else useless_model,  # type: ignore [arg-type]
        other_player=False,
        original_pickup=useless_pickup,
    )
    assert result[2] == pickup_exporter.ExportedPickupDetails(
        index=PickupIndex(2),
        name="P-B" if has_scan_text else "Unknown item",
        description="Provides the following in order: B, A." if has_scan_text else "",
        collection_text=(
            ["B acquired!", "A acquired!"]
            if model_style != PickupModelStyle.HIDE_ALL
            else ["Unknown item acquired!", "Unknown item acquired!"]
        ),
        conditional_resources=[
            ConditionalResources("B", None, ((resource_b, 1),)),
            ConditionalResources("A", resource_b, ((resource_a, 5),)),
        ],
        conversion=[],
        model=model_2 if model_style == PickupModelStyle.ALL_VISIBLE else useless_model,  # type: ignore [arg-type]
        original_model=model_2 if model_style == PickupModelStyle.ALL_VISIBLE else useless_model,  # type: ignore [arg-type]
        other_player=False,
        original_pickup=pickup_b,
    )
    assert result[3] == pickup_exporter.ExportedPickupDetails(
        index=PickupIndex(3),
        name="P-A" if has_scan_text else "Unknown item",
        description="",
        collection_text=["A acquired!"] if model_style != PickupModelStyle.HIDE_ALL else ["Unknown item acquired!"],
        conditional_resources=[ConditionalResources("A", None, ((resource_a, 1),))],
        conversion=[],
        model=model_1 if model_style == PickupModelStyle.ALL_VISIBLE else useless_model,  # type: ignore [arg-type]
        original_model=model_1 if model_style == PickupModelStyle.ALL_VISIBLE else useless_model,  # type: ignore [arg-type]
        other_player=False,
        original_pickup=pickup_a,
    )
    assert result[4] == pickup_exporter.ExportedPickupDetails(
        index=PickupIndex(4),
        name="P-C" if has_scan_text else "Unknown item",
        description="Provides 1 A. Removes 3 C." if has_scan_text else "",
        collection_text=["P-C acquired!"] if model_style != PickupModelStyle.HIDE_ALL else ["Unknown item acquired!"],
        conditional_resources=[
            ConditionalResources(
                "P-C",
                None,
                (
                    (resource_a, 1),
                    (resource_c, -3),
                ),
            )
        ],
        conversion=[ResourceConversion(source=useless_resource, target=resource_a)],
        model=model_2 if model_style == PickupModelStyle.ALL_VISIBLE else useless_model,  # type: ignore [arg-type]
        original_model=model_2 if model_style == PickupModelStyle.ALL_VISIBLE else useless_model,  # type: ignore [arg-type]
        other_player=False,
        original_pickup=pickup_c,
    )
    assert result[5] == pickup_exporter.ExportedPickupDetails(
        index=PickupIndex(5),
        name="P-D" if has_scan_text else "Unknown item",
        description="Provides 2 B and 1 A." if has_scan_text else "",
        collection_text=["P-D acquired!"] if model_style != PickupModelStyle.HIDE_ALL else ["Unknown item acquired!"],
        conditional_resources=[
            ConditionalResources(
                "P-D",
                None,
                (
                    (resource_b, 2),
                    (resource_a, 1),
                ),
            )
        ],
        conversion=[ResourceConversion(source=useless_resource, target=resource_a)],
        model=model_2 if model_style == PickupModelStyle.ALL_VISIBLE else useless_model,  # type: ignore [arg-type]
        original_model=model_2 if model_style == PickupModelStyle.ALL_VISIBLE else useless_model,  # type: ignore [arg-type]
        other_player=False,
        original_pickup=pickup_d,
    )
    assert result[6] == pickup_exporter.ExportedPickupDetails(
        index=PickupIndex(6),
        name="P-E" if has_scan_text else "Unknown item",
        description="Removes 3 C." if has_scan_text else "",
        collection_text=["P-E acquired!"] if model_style != PickupModelStyle.HIDE_ALL else ["Unknown item acquired!"],
        conditional_resources=[
            ConditionalResources(
                "P-E",
                None,
                ((resource_c, -3),),
            )
        ],
        conversion=[ResourceConversion(source=useless_resource, target=resource_c)],
        model=model_3 if model_style == PickupModelStyle.ALL_VISIBLE else useless_model,  # type: ignore [arg-type]
        original_model=model_3 if model_style == PickupModelStyle.ALL_VISIBLE else useless_model,  # type: ignore [arg-type]
        other_player=False,
        original_pickup=pickup_e,
    )


@pytest.mark.parametrize("has_memo_data", [False, True])
def test_create_pickup_list_random_data_source(
    has_memo_data: bool, empty_patches, generic_pickup_category, default_generator_params
):
    # Setup
    rng = Random(5000)
    resource_b = ItemResourceInfo(0, "B", "B", 10)

    model_1 = MagicMock(spec=PickupModel)
    model_1.game = RandovaniaGame.METROID_PRIME_ECHOES
    model_2 = MagicMock(spec=PickupModel)
    model_2.game = RandovaniaGame.METROID_PRIME_ECHOES
    useless_model = PickupModel(game=RandovaniaGame.METROID_PRIME_ECHOES, name="Useless")

    pickup_a = PickupEntry(
        "A",
        model_1,
        generic_pickup_category,
        generic_pickup_category,
        progression=(),
        generator_params=default_generator_params,
    )
    pickup_b = PickupEntry(
        "B",
        model_2,
        generic_pickup_category,
        generic_pickup_category,
        progression=((resource_b, 1), (resource_b, 1)),
        generator_params=default_generator_params,
    )
    pickup_c = PickupEntry(
        "C",
        model_2,
        generic_pickup_category,
        generic_pickup_category,
        progression=(),
        generator_params=default_generator_params,
    )
    useless_pickup = PickupEntry(
        "Useless",
        useless_model,
        USELESS_PICKUP_CATEGORY,
        USELESS_PICKUP_CATEGORY,
        progression=(),
        generator_params=default_generator_params,
    )

    patches = dataclasses.replace(empty_patches, game=MagicMock())
    patches = patches.assign_new_pickups(
        [
            (PickupIndex(0), PickupTarget(pickup_a, 0)),
            (PickupIndex(2), PickupTarget(pickup_b, 0)),
            (PickupIndex(3), PickupTarget(pickup_a, 0)),
            (PickupIndex(4), PickupTarget(pickup_c, 0)),
        ]
    )

    if has_memo_data:
        memo_data = {
            "A": "This is an awesome item A",
            "B": "This is B. It is good.",
            "C": "What a nice day to have a C",
            "Useless": "Try again next time",
        }
    else:
        memo_data = {name: f"{name} acquired!" for name in ("A", "B", "C", "Useless")}

    creator = pickup_exporter.PickupExporterSolo(memo_data, RandovaniaGame.METROID_PRIME_ECHOES)

    region_list = MagicMock()
    region_list.iterate_nodes.return_value = [
        PickupNode(
            NodeIdentifier.create("W", "A", f"Name {i}"),
            i,
            False,
            None,
            "",
            ("default",),
            {},
            False,
            PickupIndex(i),
            False,
        )
        for i in range(5)
    ]

    # Run
    result = pickup_exporter.export_all_indices(
        patches,
        PickupTarget(useless_pickup, 0),
        region_list,
        rng,
        PickupModelStyle.HIDE_ALL,
        PickupModelDataSource.RANDOM,
        creator,
        pickup_creator.create_visual_nothing(RandovaniaGame.METROID_PRIME_ECHOES, "EnergyTransferModule"),
    )

    # Assert
    assert len(result) == 5
    assert result[0] == pickup_exporter.ExportedPickupDetails(
        index=PickupIndex(0),
        name="A",
        description="",
        collection_text=[memo_data["A"]],
        conditional_resources=[ConditionalResources("A", None, ())],
        conversion=[],
        model=model_1,
        original_model=model_1,
        other_player=False,
        original_pickup=pickup_a,
    )
    assert result[1] == pickup_exporter.ExportedPickupDetails(
        index=PickupIndex(1),
        name="A",
        description="",
        collection_text=[memo_data["A"]],
        conditional_resources=[ConditionalResources("Useless", None, ())],
        conversion=[],
        model=model_1,
        original_model=model_1,
        other_player=False,
        original_pickup=useless_pickup,
    )
    assert result[2] == pickup_exporter.ExportedPickupDetails(
        index=PickupIndex(2),
        name="C",
        description="",
        collection_text=[memo_data["C"], memo_data["C"]],
        conditional_resources=[
            ConditionalResources("B", None, ((resource_b, 1),)),
            ConditionalResources("B", resource_b, ((resource_b, 1),)),
        ],
        conversion=[],
        model=model_2,
        original_model=model_2,
        other_player=False,
        original_pickup=pickup_b,
    )
    assert result[3] == pickup_exporter.ExportedPickupDetails(
        index=PickupIndex(3),
        name="B",
        description="",
        collection_text=[memo_data["B"]],
        conditional_resources=[ConditionalResources("A", None, ())],
        conversion=[],
        model=model_2,
        original_model=model_2,
        other_player=False,
        original_pickup=pickup_a,
    )
    assert result[4] == pickup_exporter.ExportedPickupDetails(
        index=PickupIndex(4),
        name="A",
        description="",
        collection_text=[memo_data["A"]],
        conditional_resources=[ConditionalResources("C", None, ())],
        conversion=[],
        model=model_1,
        original_model=model_1,
        other_player=False,
        original_pickup=pickup_c,
    )


def test_pickup_scan_for_progressive_suit(echoes_pickup_database, echoes_resource_database):
    # Setup
    progressive_suit = echoes_pickup_database.standard_pickups["Progressive Suit"]
    pickup = pickup_creator.create_standard_pickup(
        progressive_suit, StandardPickupState(), echoes_resource_database, None, False
    )

    # Run
    result = pickup_exporter._pickup_description(pickup)

    # Assert
    assert result == "Provides the following in order: Dark Suit, Light Suit."


@pytest.mark.parametrize(
    ("item", "ammo", "expected"),
    [
        (
            "Beam Ammo Expansion",
            [4, 20],
            "Provides 4 Dark Ammo, 20 Light Ammo and 1 Item Percentage.",
        ),
        (
            "Beam Ammo Expansion",
            [-4, -20],
            "Provides 1 Item Percentage. Removes 4 Dark Ammo and 20 Light Ammo.",
        ),
        (
            "Beam Ammo Expansion",
            [4, -20],
            "Provides 4 Dark Ammo and 1 Item Percentage. Removes 20 Light Ammo.",
        ),
        ("Missile Expansion", [4], "Provides 4 Missiles and 1 Item Percentage."),
    ],
)
def test_pickup_scan_for_ammo_expansion(echoes_pickup_database, echoes_resource_database, item, ammo, expected):
    # Setup
    expansion = echoes_pickup_database.ammo_pickups[item]
    pickup = pickup_creator.create_ammo_pickup(expansion, ammo, False, echoes_resource_database)

    # Run
    result = pickup_exporter._pickup_description(pickup)

    # Assert
    assert result == expected


@pytest.fixture()
def pickup_for_create_pickup_data(generic_pickup_category, default_generator_params):
    resource_a = ItemResourceInfo(0, "A", "A", 10)
    resource_b = ItemResourceInfo(1, "B", "B", 10)
    return PickupEntry(
        "Cake",
        PickupModel(RandovaniaGame.METROID_PRIME_ECHOES, "theModel"),
        generic_pickup_category,
        generic_pickup_category,
        progression=(
            (resource_a, 1),
            (resource_b, 1),
        ),
        generator_params=default_generator_params,
    )


def test_solo_create_pickup_data(pickup_for_create_pickup_data):
    # Setup
    creator = pickup_exporter.PickupExporterSolo(
        pickup_exporter.GenericAcquiredMemo(), RandovaniaGame.METROID_PRIME_ECHOES
    )
    pickup_model = pickup_for_create_pickup_data
    resource_a = ItemResourceInfo(0, "A", "A", 10)
    resource_b = ItemResourceInfo(1, "B", "B", 10)

    # Run
    data = creator.create_details(
        PickupIndex(10),
        PickupTarget(pickup_for_create_pickup_data, 0),
        pickup_for_create_pickup_data,
        pickup_model,
        PickupModelStyle.ALL_VISIBLE,
        "The Name",
        "Scan Text",
    )

    # Assert
    assert data == pickup_exporter.ExportedPickupDetails(
        index=PickupIndex(10),
        name="The Name",
        description="Scan Text",
        collection_text=["A acquired!", "B acquired!"],
        conditional_resources=[
            ConditionalResources("A", None, ((resource_a, 1),)),
            ConditionalResources("B", resource_a, ((resource_b, 1),)),
        ],
        conversion=[],
        model=pickup_model.model,
        original_model=pickup_model.model,
        other_player=False,
        original_pickup=pickup_for_create_pickup_data,
    )


def test_multi_create_pickup_data_for_self(pickup_for_create_pickup_data):
    # Setup
    solo = pickup_exporter.PickupExporterSolo(
        pickup_exporter.GenericAcquiredMemo(), RandovaniaGame.METROID_PRIME_ECHOES
    )
    creator = pickup_exporter.PickupExporterMulti(solo, PlayersConfiguration(0, {0: "You", 1: "Someone"}))
    resource_a = ItemResourceInfo(0, "A", "A", 10)
    resource_b = ItemResourceInfo(1, "B", "B", 10)

    # Run
    data = creator.create_details(
        PickupIndex(10),
        PickupTarget(pickup_for_create_pickup_data, 0),
        pickup_for_create_pickup_data,
        pickup_for_create_pickup_data,
        PickupModelStyle.ALL_VISIBLE,
        "The Name",
        "Scan Text",
    )

    # Assert
    assert data == pickup_exporter.ExportedPickupDetails(
        index=PickupIndex(10),
        name="Your The Name",
        description="Scan Text",
        collection_text=["A acquired!", "B acquired!"],
        conditional_resources=[
            ConditionalResources("A", None, ((resource_a, 1),)),
            ConditionalResources("B", resource_a, ((resource_b, 1),)),
        ],
        conversion=[],
        model=PickupModel(game=RandovaniaGame.METROID_PRIME_ECHOES, name="theModel"),
        original_model=PickupModel(game=RandovaniaGame.METROID_PRIME_ECHOES, name="theModel"),
        other_player=False,
        original_pickup=pickup_for_create_pickup_data,
    )


def test_multi_create_pickup_data_for_other(pickup_for_create_pickup_data):
    # Setup
    solo = pickup_exporter.PickupExporterSolo(
        pickup_exporter.GenericAcquiredMemo(), RandovaniaGame.METROID_PRIME_ECHOES
    )
    creator = pickup_exporter.PickupExporterMulti(solo, PlayersConfiguration(0, {0: "You", 1: "Someone"}))

    # Run
    data = creator.create_details(
        PickupIndex(10),
        PickupTarget(pickup_for_create_pickup_data, 1),
        pickup_for_create_pickup_data,
        pickup_for_create_pickup_data,
        PickupModelStyle.ALL_VISIBLE,
        "The Name",
        "Scan Text",
    )

    # Assert
    assert data == pickup_exporter.ExportedPickupDetails(
        index=PickupIndex(10),
        name="Someone's The Name",
        description="Scan Text",
        collection_text=["Sent The Name to Someone!"],
        conditional_resources=[
            ConditionalResources(None, None, ()),
        ],
        conversion=[],
        model=PickupModel(game=RandovaniaGame.METROID_PRIME_ECHOES, name="theModel"),
        original_model=PickupModel(game=RandovaniaGame.METROID_PRIME_ECHOES, name="theModel"),
        other_player=True,
        original_pickup=pickup_for_create_pickup_data,
    )
