from randovania.game_description.game_description import GameDescription


def test_every_area_has_asset_id(dread_game_description: GameDescription) -> None:
    for area in dread_game_description.region_list.all_areas:
        assert "asset_id" in area.extra
