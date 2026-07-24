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


@dataclasses.dataclass(frozen=True)
class TrackerCatalog:
    """
    Everything available for one game: a set of named layouts (structures) and a set of
    named themes, where each theme only covers whichever layouts it was authored for
    (e.g. a "Stream-friendly" theme might only exist for one specific layout).
    """

    layouts: dict[str, Path]
    themes: dict[str, dict[str, Path]]

    def theme_names_for(self, layout_name: str) -> list[str]:
        """Themes that have an entry for the given layout, in catalog order."""
        return [name for name, per_layout in self.themes.items() if layout_name in per_layout]

    def resolve(self, layout_name: str, theme_name: str) -> TrackerAssetPaths:
        return TrackerAssetPaths(structure=self.layouts[layout_name], theme=self.themes[theme_name][layout_name])

    def as_named_combos(self) -> dict[str, TrackerAssetPaths]:
        """Flatten every valid (layout, theme) pair into a single "Theme (Layout)" name.

        Used by consumers that only care about a flat list of ready-to-use trackers (e.g. the
        per-player tracker popup), not about picking layout and theme independently.
        """
        single_layout = len(self.layouts) == 1
        result: dict[str, TrackerAssetPaths] = {}
        for theme_name, per_layout in self.themes.items():
            for layout_name in per_layout:
                name = theme_name if single_layout else f"{theme_name} ({layout_name})"
                result[name] = self.resolve(layout_name, theme_name)
        return result
