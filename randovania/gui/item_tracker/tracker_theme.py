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
    The visual definition paired with a TrackerStructure: which images to show for each
    image element, and which text/style to use for each label element. Keyed by the
    element's index in TrackerStructure.elements, so a single theme is only meaningful
    together with the specific structure it was authored against (see validate_against).
    """

    images: dict[int, ImageThemeElement] = Field(default_factory=dict)
    labels: dict[int, LabelThemeElement] = Field(default_factory=dict)

    @classmethod
    def read_json(cls, path: Path) -> Self:
        return cls.model_validate(json_lib.read_dict(path))

    def validate_against(self, structure: TrackerStructure) -> None:
        for index, element in enumerate(structure.elements):
            if element.kind == ElementKind.IMAGE:
                image = self.images.get(index)
                if image is None:
                    raise ValueError(f"Theme is missing an image for element {index} ({element.resources})")
                if len(image.image_paths) > 1 and len(image.image_paths) != len(element.resources):
                    raise ValueError(
                        f"Element {index} has {len(image.image_paths)} progressive images, "
                        f"but has {len(element.resources)} resources ({element.resources})"
                    )

            elif element.kind == ElementKind.LABEL:
                if index not in self.labels:
                    raise ValueError(f"Theme is missing a label for element {index} ({element.resources})")

    def image_for(self, index: int) -> ImageThemeElement:
        return self.images[index]

    def label_for(self, index: int) -> LabelThemeElement:
        return self.labels[index]
