"""Bounds helpers shared by the data editor canvas and the Discord bot."""

from __future__ import annotations

from typing import NamedTuple


class BoundsInt(NamedTuple):
    min_x: int
    min_y: int
    max_x: int
    max_y: int


class BoundsFloat(NamedTuple):
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @classmethod
    def from_bounds(cls, data: dict[str, float]) -> BoundsFloat:
        return BoundsFloat(data["x1"], data["y1"], data["x2"], data["y2"])


def expand_bounds_to_match_aspect(image_bounds: BoundsInt, world_bounds: BoundsFloat) -> BoundsInt:
    """
    Expands the image bounds symmetrically on one axis until its aspect ratio matches the world bounds.
    """
    world_width = world_bounds.max_x - world_bounds.min_x
    world_height = world_bounds.max_y - world_bounds.min_y
    if world_width <= 0 or world_height <= 0:
        return image_bounds

    image_width = image_bounds.max_x - image_bounds.min_x
    image_height = image_bounds.max_y - image_bounds.min_y
    if image_width <= 0 or image_height <= 0:
        return image_bounds

    if image_width * world_height < image_height * world_width:
        # image is proportionally narrower than the world: include more columns
        padding = (image_height * world_width / world_height - image_width) / 2
        return BoundsInt(
            min_x=round(image_bounds.min_x - padding),
            min_y=image_bounds.min_y,
            max_x=round(image_bounds.max_x + padding),
            max_y=image_bounds.max_y,
        )
    else:
        # image is proportionally shorter than the world: include more rows
        padding = (image_width * world_height / world_width - image_height) / 2
        return BoundsInt(
            min_x=image_bounds.min_x,
            min_y=round(image_bounds.min_y - padding),
            max_x=image_bounds.max_x,
            max_y=round(image_bounds.max_y + padding),
        )
