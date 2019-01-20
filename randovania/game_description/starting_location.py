from dataclasses import dataclass


@dataclass(frozen=True)
class StartingLocation:
    world_asset_id: int
    area_asset_id: int
