from enum import Enum, StrEnum
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import BaseModel, Field

from randovania.game.game_enum import RandovaniaGame
from randovania.lib import json_lib
from randovania.lib.json_lib import JsonObject


class FieldToCheck(Enum):
    AMOUNT = "amount"
    CAPACITY = "capacity"
    MAX_CAPACITY = "max_capacity"


class ElementKind(StrEnum):
    IMAGE = "image"
    LABEL = "label"
    PROGRESS_BAR = "progress_bar"


class BaseTrackerElement(BaseModel):
    """
    The non-visual definition of a tracker element: where it sits in the grid, which
    resources it tracks, and the logic for deciding when it's "checked". None of this
    depends on which theme (image set) is currently in use.
    """

    name: str
    row: int
    column: int
    resources: list[str]

    row_span: int = 1
    col_span: int = 1
    minimum_to_check: int = 1
    maximum_to_check: int = -1
    field_to_check: FieldToCheck = FieldToCheck.CAPACITY


class ImageTrackerElement(BaseTrackerElement):
    kind: Literal[ElementKind.IMAGE] = ElementKind.IMAGE


class LabelTrackerElement(BaseTrackerElement):
    kind: Literal[ElementKind.LABEL] = ElementKind.LABEL


class ProgressBarTrackerElement(BaseTrackerElement):
    kind: Literal[ElementKind.PROGRESS_BAR] = ElementKind.PROGRESS_BAR


type TrackerElement = Annotated[
    ImageTrackerElement | LabelTrackerElement | ProgressBarTrackerElement,
    Field(discriminator="kind"),
]


class TrackerStructure(BaseModel):
    game: RandovaniaGame
    elements: list[TrackerElement]
    extra: JsonObject = Field(default_factory=dict)

    @classmethod
    def read_json(cls, path: Path) -> Self:
        return cls.model_validate(json_lib.read_dict(path))
