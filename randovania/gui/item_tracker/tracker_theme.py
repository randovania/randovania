from pathlib import Path
from typing import Self

from pydantic import BaseModel, Field

from randovania.gui.item_tracker.tracker_structure import ElementKind, LabelTrackerElement, TrackerStructure
from randovania.lib import json_lib


class ImageThemeElement(BaseModel):
    image_path: str | list[str]
    disabled_image_path: str | None = None

    @property
    def image_paths(self) -> list[str]:
        if not isinstance(self.image_path, list):
            return [self.image_path]
        return self.image_path


class LabelThemeElement(BaseModel):
    text: str
    style: str | None = None


# Common label renderings so many themes don't each need to spell out the same handful of
# templates under whatever name their label elements happen to have. A theme can still define
# its own entry under one of these names to override the default.
DEFAULT_LABELS: dict[str, LabelThemeElement] = {
    "Capacity": LabelThemeElement(text="x {capacity}"),
    "Capacity with Maximum": LabelThemeElement(text="x {capacity}/{max_capacity}"),
}


class TrackerTheme(BaseModel):
    """
    The visual definition that can be paired with any TrackerStructure of the same game: which
    images to show for each named image element, and which text/style to use for each named
    label element.

    A label element named after one of DEFAULT_LABELS is covered automatically
    even when a theme doesn't mention it, and a label element with its own.

    A theme is required to cover every image name listed in the game's trackers.json.
    """

    images: dict[str, ImageThemeElement] = Field(default_factory=dict)
    labels: dict[str, LabelThemeElement] = Field(default_factory=dict)

    @classmethod
    def read_json(cls, path: Path) -> Self:
        return cls.model_validate(json_lib.read_dict(path))

    def validate_against(self, structure: TrackerStructure) -> None:
        for element in structure.elements:
            if element.kind == ElementKind.IMAGE:
                image = self.images.get(element.name)
                if image is None:
                    raise ValueError(f"Theme is missing an image named {element.name!r}")
                if len(image.image_paths) > 1 and len(image.image_paths) != len(element.resources):
                    raise ValueError(
                        f"{element.name!r} has {len(image.image_paths)} progressive images, "
                        f"but has {len(element.resources)} resources ({element.resources})"
                    )

            elif element.kind == ElementKind.LABEL:
                if element.text is None and element.name not in self.labels and element.name not in DEFAULT_LABELS:
                    raise ValueError(f"Theme is missing a label named {element.name!r}")

    def image_for(self, name: str) -> ImageThemeElement:
        return self.images[name]

    def label_for(self, element: LabelTrackerElement) -> LabelThemeElement:
        if element.text is not None:
            return LabelThemeElement(text=element.text, style=element.style)
        label = self.labels.get(element.name)
        if label is not None:
            return label
        return DEFAULT_LABELS[element.name]
