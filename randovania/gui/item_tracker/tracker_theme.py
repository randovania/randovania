from pathlib import Path
from typing import Self

from pydantic import BaseModel, Field

from randovania.gui.item_tracker.tracker_structure import ElementKind, TrackerStructure
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


class TrackerTheme(BaseModel):
    """
    The visual definition that can be paired with any TrackerStructure that needs it: which
    images to show for each named image element, and which text/style to use for each named
    label element. Keyed by the element's `name` rather than its position, so the same theme
    applies to every layout that happens to contain a given name (see is_compatible_with) -
    nothing here is tied to one specific structure's shape.
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
                if element.name not in self.labels:
                    raise ValueError(f"Theme is missing a label named {element.name!r}")

    def is_compatible_with(self, structure: TrackerStructure) -> bool:
        try:
            self.validate_against(structure)
        except ValueError:
            return False
        return True

    def image_for(self, name: str) -> ImageThemeElement:
        return self.images[name]

    def label_for(self, name: str) -> LabelThemeElement:
        return self.labels[name]
