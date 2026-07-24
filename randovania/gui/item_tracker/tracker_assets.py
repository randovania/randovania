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
    named themes. A theme applies to whichever layouts contain every name it needs to cover
    (checked dynamically via TrackerTheme.is_compatible_with) - nothing here hard-codes which
    layouts a theme was "meant" for, so one theme file can serve every layout that fits it.
    """

    layouts: dict[str, Path]
    themes: dict[str, Path]

    def theme_names_for(self, layout_name: str) -> list[str]:
        """Themes compatible with the given layout, in catalog order."""
        structure = TrackerStructure.read_json(self.layouts[layout_name])
        return [
            name for name, path in self.themes.items() if TrackerTheme.read_json(path).is_compatible_with(structure)
        ]

    def resolve(self, layout_name: str, theme_name: str) -> TrackerAssetPaths:
        return TrackerAssetPaths(structure=self.layouts[layout_name], theme=self.themes[theme_name])

    def as_named_combos(self) -> dict[str, TrackerAssetPaths]:
        """Flatten every valid (layout, theme) pair into a single "Theme (Layout)" name.

        Used by consumers that only care about a flat list of ready-to-use trackers (e.g. the
        per-player tracker popup), not about picking layout and theme independently.
        """
        single_layout = len(self.layouts) == 1
        result: dict[str, TrackerAssetPaths] = {}
        for layout_name in self.layouts:
            for theme_name in self.theme_names_for(layout_name):
                name = theme_name if single_layout else f"{theme_name} ({layout_name})"
                result[name] = self.resolve(layout_name, theme_name)
        return result
