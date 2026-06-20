from enum import Enum
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, Field

from randovania.game.game_enum import RandovaniaGame
from randovania.lib import json_lib
from randovania.lib.json_lib import JsonObject


class FieldToCheck(Enum):
    AMOUNT = "amount"
    CAPACITY = "capacity"
    MAX_CAPACITY = "max_capacity"


class BaseTrackerElement(BaseModel):
    row: int
    column: int
    resources: list[str]

    row_span: int = 1
    col_span: int = 1
    minimum_to_check: int = 1
    maximum_to_check: int = -1
    field_to_check: FieldToCheck = FieldToCheck.CAPACITY


class ImageTrackerElement(BaseTrackerElement):
    image_path: str | list[str]
    disabled_image_path: str | None = None

    @property
    def image_paths(self) -> list[str]:
        if not isinstance(self.image_path, list):
            return [self.image_path]
        return self.image_path


class LabelTrackerElement(BaseTrackerElement):
    label: str
    style: str | None = None


class ProgressBarTrackerElement(BaseTrackerElement):
    progress_bar: Literal[True]


type TrackerElement = ImageTrackerElement | LabelTrackerElement | ProgressBarTrackerElement


class TrackerLayout(BaseModel):
    game: RandovaniaGame
    elements: list[TrackerElement]
    extra: JsonObject = Field(default_factory=dict)

    @classmethod
    def read_json(cls, path: Path) -> Self:
        return cls.model_validate(json_lib.read_dict(path))
