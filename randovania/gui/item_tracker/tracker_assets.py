import dataclasses
from pathlib import Path

from randovania.gui.item_tracker.tracker_structure import TrackerStructure
from randovania.gui.item_tracker.tracker_theme import TrackerTheme


@dataclasses.dataclass(frozen=True)
class TrackerAssetPaths:
    """Points at a TrackerStructure file and a TrackerTheme file meant to be used together."""

    structure: Path
    theme: Path

    def load(self) -> tuple[TrackerStructure, TrackerTheme]:
        structure = TrackerStructure.read_json(self.structure)
        theme = TrackerTheme.read_json(self.theme)
        theme.validate_against(structure)
        return structure, theme
